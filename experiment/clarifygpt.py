import argparse
from pathlib import Path
import random
import jsonlines
from concurrent.futures import ProcessPoolExecutor

from specfix.model import Model
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.tester import differential_tester, ground_truth_tester
from specfix.utils import (
    get_inputs_outputs,
    read_jsonl,
    unwrap,
    unify_model_name,
    construct_output_file,
)

# -------------------------
# Globals initialized per worker process
# -------------------------
_G_EVALUATOR = None
_G_MODEL = None
_G_INPUTS = None
_G_OUTPUTS = None
_G_MODEL_NAME = None
_G_N_PROGRAMS = None


def _proc_initializer(model_name: str, dataset: str, n_programs: int):
    """
    Per-process initializer. Runs once when a worker process starts.

    Initializes global heavy resources to avoid re-initialization for every task:
    - SpecFixAccuracyEvaluator
    - Model
    - Inputs/Outputs for the dataset
    - Unified model name and number of programs
    """
    global _G_EVALUATOR, _G_MODEL, _G_INPUTS, _G_OUTPUTS, _G_MODEL_NAME, _G_N_PROGRAMS
    _G_EVALUATOR = SpecFixAccuracyEvaluator(
        model=model_name,
        differential_tester=differential_tester,
        ground_truth_tester=ground_truth_tester,
    )
    _G_MODEL = Model(model_name)
    _G_INPUTS, _G_OUTPUTS = get_inputs_outputs(dataset)
    _G_MODEL_NAME = unify_model_name(model_name)
    _G_N_PROGRAMS = n_programs


def build_openai_prompt(role_description, user_content):
    return [
        {"role": "system", "content": role_description},
        {"role": "user", "content": user_content},
    ]


def prompt_repair(requirement, questions):
    system_desc = (
        "You will receive a user requirement and clarifying questions. "
        "Answer these clarifying questions using the given requirement. "
        "Provide reasonable answers if the requirement lacks specifics. "
        "Wrap your answers in <answers></answers> tags without repeating the questions."
    )
    user_content = (
        f"### User Requirement:\n{requirement}\n\n"
        f"### Clarifying Questions:\n{questions}\n\n"
        f"### Answers:\n{{<answers>insert here.</answers>}}"
    )
    return build_openai_prompt(system_desc, user_content)


def prompt_generate_questions(requirement, inconsistent_solutions):
    system_desc = (
        "You will be given a user requirement and candidate solutions with differing functionalities due to unclear requirements. "
        "Analyze differences, determine unclear points, and ask clarifying questions. "
        "Wrap questions only (no analysis) in <questions></questions> tags."
    )
    sol_str = "\n".join(f"Solution {i}:\n{sol}" for i, sol in enumerate(inconsistent_solutions))
    user_content = (
        f"### User Requirement:{requirement}\n"
        f"### Inconsistent Solutions:\n{sol_str}\n\n"
        f"### Analysis and Clarifying Questions:\n{{insert here.}}"
    )
    return build_openai_prompt(system_desc, user_content)


# Mutation Logic for Tests (unchanged)
def type_aware_mutation(tests, n=10):
    def mutate(x):
        if isinstance(x, bool):
            return not x
        if isinstance(x, (int, float)):
            return x + random.choice([-1, 1])
        if isinstance(x, str):
            return x[:-1] if x else x
        if isinstance(x, (list, tuple, set)):
            return type(x)(mutate(e) for e in x)
        if isinstance(x, dict):
            return {k: mutate(v) for k, v in x.items()}
        return x

    new_tests, iterations = list(tests), 0
    while len(new_tests) < n and iterations < n * 10:
        candidate = [mutate(x) for x in random.choice(tests)]
        if candidate not in new_tests:
            new_tests.append(candidate)
        iterations += 1
    return new_tests


def parse_problem(problem):
    return (
        problem["requirement"],
        problem["entry_point"],
        problem["input_output_examples"],
    )


def worker(task):
    """
    Process a single problem using globally-initialized resources.

    Parameters
    ----------
    task : dict
        Task payload containing:
          - idx: index into inputs/outputs
          - problem: the problem dict (with 'original_clusters_serialized')
    """
    global _G_EVALUATOR, _G_MODEL, _G_INPUTS, _G_OUTPUTS

    idx = task["idx"]
    problem = task["problem"]
    requirement, entry_point, examples = parse_problem(problem)
    # Rehydrate original clusters inside the subprocess
    programs = _G_EVALUATOR.generate_programs(
        requirement,
        entry_point,
        _G_N_PROGRAMS,
    )
    tests = _G_EVALUATOR.generate_tests(
        requirement,
        entry_point,
    )
    original_clusters = _G_EVALUATOR.get_clusters(requirement, programs, tests, entry_point, examples)

    # If there is no ambiguity (entropy == 0), short-circuit
    if original_clusters and getattr(original_clusters, "entropy", None) == 0:
        result = {
            "task_id": problem["task_id"],
            "requirement": problem["requirement"],
            "clarifying_questions": None,
            "repaired_requirement": None,
            "original_clusters": original_clusters.serialize(),
            "repaired_clusters": original_clusters.serialize(),
            "result": {
                "repaired_passk": None,
                "repaired_pass_rate": None,
                "repaired_passk_bigger_than_0": None,
                "repaired_solved_with_majority_vote": None,
            },
        }
        return result

    # Generate clarifying questions based on inconsistent solutions
    inconsistent_solutions = [c.programs_str[0] for c in original_clusters.cluster_list]
    questions_prompt = prompt_generate_questions(requirement, inconsistent_solutions)
    questions_response = _G_MODEL.get_response(*[p["content"] for p in questions_prompt], True)
    clarifying_questions = unwrap(questions_response, "questions")

    # Repair requirement based on clarifications
    repair_prompt = prompt_repair(requirement, clarifying_questions)
    repair_response = _G_MODEL.get_response(*[p["content"] for p in repair_prompt], True)
    answers = unwrap(repair_response, "answers")

    repaired_requirement = f'{requirement}\nClarification:\n{answers}\n"""'
    problem["repaired_requirement"] = repaired_requirement

    # Detect clusters and evaluate
    _, repaired_clusters = _G_EVALUATOR.specfix_detect(problem, _G_N_PROGRAMS, "repaired_requirement")

    (
        repaired_passk,
        repaired_pass_rate,
        repaired_generated_programs,
        repaired_failed_inputs_outputs,
    ) = _G_EVALUATOR.pass_k_and_pass_rate(
        repaired_requirement,
        _G_INPUTS[idx],
        _G_OUTPUTS[idx],
        problem["entry_point"],
        1,
        10,
    )

    repaired_solved_with_majority_vote = _G_EVALUATOR.solved_with_majority_vote(
        repaired_clusters, _G_INPUTS[idx], _G_OUTPUTS[idx]
    )

    result = {
        "task_id": problem["task_id"],
        "requirement": problem["requirement"],
        "clarifying_questions": clarifying_questions,
        "repaired_requirement": repaired_requirement,
        "original_clusters": original_clusters.serialize() if original_clusters else None,
        "repaired_clusters": repaired_clusters.serialize() if repaired_clusters else None,
        "result": {
            "repaired_passk": repaired_passk,
            "repaired_pass_rate": repaired_pass_rate,
            "repaired_passk_bigger_than_0": (repaired_passk > 0 if repaired_passk is not None else None),
            "repaired_solved_with_majority_vote": repaired_solved_with_majority_vote,
        },
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", required=True)
    parser.add_argument("-m", "--model", required=True)
    parser.add_argument("-n", "--program_number", type=int, default=20)
    args = parser.parse_args()

    problems = read_jsonl(f"dataset/{args.dataset}.jsonl")

    # Construct output path
    output_file = construct_output_file(
        Path(__file__).resolve().parent, unify_model_name(args.model), args.dataset, "clarifygpt_repair"
    )

    # Build tasks (only problems that actually have clusters to process)
    tasks = [{"idx": i, "problem": prob} for i, prob in enumerate(problems)]

    if not tasks:
        # Nothing to process; still create an empty file for consistency.
        with jsonlines.open(output_file, mode="w", flush=True) as writer:
            pass
        return

    max_workers = 96

    # Use ProcessPoolExecutor with per-process initializer
    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=_proc_initializer,
        initargs=(args.model, args.dataset, args.program_number),
    ) as executor, jsonlines.open(output_file, mode="w", flush=True) as writer:
        # Map returns an iterator; iterate and write each result as it completes in order
        for processed_problem in executor.map(worker, tasks, chunksize=1):
            writer.write(processed_problem)


if __name__ == "__main__":
    main()
