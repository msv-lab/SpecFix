import argparse
import ast
import copy
import random
import jsonlines
from concurrent.futures import ThreadPoolExecutor
from specfix.model import Model
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.tester import differential_tester, ground_truth_tester
from specfix.utils import get_entry_point, get_inputs_outputs, read_jsonl, unwrap, unify_model_name


def build_openai_prompt(role_description, user_content):
    return [
        {'role': 'system', 'content': role_description},
        {'role': 'user', 'content': user_content}
    ]


def prompt_repair(requirement, questions):
    system_desc = (
        'You will receive a user requirement and clarifying questions. '
        'Answer these clarifying questions using the given requirement. '
        'Provide reasonable answers if the requirement lacks specifics. '
        'Wrap your answers in <answers></answers> tags without repeating the questions.'
    )
    user_content = f'### User Requirement:\n{requirement}\n\n### Clarifying Questions:\n{questions}\n\n### Answers:\n{{<answers>insert here.</answers>}}'
    return build_openai_prompt(system_desc, user_content)


def prompt_generate_questions(requirement, inconsistent_solutions):
    system_desc = (
        'You will be given a user requirement and candidate solutions with differing functionalities due to unclear requirements. '
        'Analyze differences, determine unclear points, and ask clarifying questions. '
        'Wrap questions only (no analysis) in <questions></questions> tags.'
    )
    sol_str = '\n'.join(f"Solution {i}:\n{sol}" for i, sol in enumerate(inconsistent_solutions))
    user_content = f'### User Requirement:{requirement}\n### Inconsistent Solutions:\n{sol_str}\n\n### Analysis and Clarifying Questions:\n{{insert here.}}'
    return build_openai_prompt(system_desc, user_content)


# Mutation Logic for Tests
def type_aware_mutation(tests, n=10):
    def mutate(x):
        if isinstance(x, (int, float)):
            return x + random.choice([-1, 1])
        if isinstance(x, bool):
            return not x
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
    return problem['requirement'], problem['entry_point'], problem['input_output_examples']


# Main Worker Function
def worker(idx, problem, orig_problem, evaluator, model, inputs, outputs, model_name, n_programs):
    requirement, entry_point, examples = parse_problem(problem)

    test_inputs = ast.literal_eval(problem["llm_generated_inputs"][model_name])
    mutated_inputs = type_aware_mutation(test_inputs)

    programs = evaluator.generate_programs(requirement, entry_point, n_programs)
    clusters = evaluator.get_clusters(requirement, programs, mutated_inputs, entry_point, examples)

    problem.update({
        "original_passk": orig_problem["original_passk"],
        "original_cluster": clusters.serialize()
    })

    if clusters.entropy == 0:
        problem.update({key: None for key in [
            "repaired_requirement", "repaired_cluster", "clarifying_questions",
            "repaired_generated_programs", "repaired_failed_inputs_outputs",
            "repaired_requirement_woe", "repaired_woe_generated_programs",
            "repaired_woe_failed_inputs_outputs"]})
        problem["repaired_passk"] = orig_problem["original_passk"]
        return idx, problem

    inconsistent_solutions = [c.programs_str[0] for c in clusters.cluster_list]
    questions_prompt = prompt_generate_questions(requirement, inconsistent_solutions)
    questions_response = model.get_response(*[p["content"] for p in questions_prompt], True)
    clarifying_questions = unwrap(questions_response, "questions")

    repair_prompt = prompt_repair(requirement, clarifying_questions)
    repair_response = model.get_response(*[p["content"] for p in repair_prompt], True)
    answers = unwrap(repair_response, "answers")

    repaired_requirement = f"{requirement}\nClarification:\n{answers}\n\"\"\""

    repaired_programs = evaluator.generate_programs(repaired_requirement, entry_point, n_programs)
    repaired_clusters = evaluator.get_clusters(repaired_requirement, repaired_programs, mutated_inputs, entry_point,
                                               examples)

    passk_res = evaluator.pass_k_sample(repaired_requirement, inputs[idx], outputs[idx], entry_point, 1, 10)
    problem_woe = evaluator.remove_example(problem, repaired_requirement)
    woe_passk_res = evaluator.pass_k_sample(problem_woe["requirement"], inputs[idx], outputs[idx], get_entry_point(problem_woe["requirement"]), 1, 10)

    problem.update({
        "repaired_requirement": repaired_requirement,
        "repaired_cluster": repaired_clusters.serialize(),
        "clarifying_questions": clarifying_questions,
        "repaired_passk": passk_res[0],
        "repaired_generated_programs": passk_res[1],
        "repaired_failed_inputs_outputs": str(passk_res[2]),
        "repaired_requirement_woe": problem_woe["requirement"],
        "repaired_woe_passk": woe_passk_res[0],
        "repaired_woe_generated_programs": woe_passk_res[1],
        "repaired_woe_failed_inputs_outputs": str(woe_passk_res[2])
    })

    return idx, problem


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", required=True)
    parser.add_argument("-m", "--model", required=True)
    parser.add_argument("-n", "--program_number", type=int, default=20)
    args = parser.parse_args()

    inputs, outputs = get_inputs_outputs(args.dataset)
    unified_model_name = unify_model_name(args.model)
    original_problems = read_jsonl(f"../test_based_repair/original_passk/{unified_model_name}/{args.dataset}.jsonl")
    problems = read_jsonl(f"../../dataset/{args.dataset}.jsonl")

    evaluator = SpecFixAccuracyEvaluator(model=args.model, differential_tester=differential_tester,
                                         ground_truth_tester=ground_truth_tester)
    model = Model(args.model)

    output_path = f"{unified_model_name}_{args.dataset}_clarifygpt.jsonl"
    with jsonlines.open(output_path, mode='w', flush=True) as writer:
        # for i, (prob, orig_prob) in enumerate(zip(problems, original_problems)):
        #     idx, result = worker(i, prob, orig_prob, evaluator, model, inputs, outputs, unified_model_name,
        #                          args.program_number)
        #     print(idx)
        #     writer.write(result)
        # multi-threading

        tasks = [(i, prob, orig_prob, evaluator, model, inputs, outputs, unified_model_name, args.program_number)
                 for i, (prob, orig_prob) in enumerate(zip(problems, original_problems))]
        with ThreadPoolExecutor(max_workers=10) as executor:
            for i, result in executor.map(lambda x: worker(*x), tasks):
                print(i)
                writer.write(result)


if __name__ == "__main__":
    main()
