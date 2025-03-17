import argparse
import ast
import copy
import json
import random
import jsonlines

from specfix.model import Model
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.tester import differential_tester, differential_tester_crosshair
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


# Main Worker Function
def worker(requirement, entry_point, examples, evaluator, model, n_programs):
    problem = {}

    test_inputs = evaluator.generate_tests(requirement, entry_point)
    mutated_inputs = type_aware_mutation(test_inputs)
    if model == "deepseek-v3-241226":
        programs = evaluator.generate_programs(requirement, entry_point, n_programs)
    else:
        programs = evaluator.parallel_generate_programs(requirement, entry_point, n_programs)
    # clusters = differential_tester_crosshair(programs, entry_point)
    clusters = differential_tester(programs, mutated_inputs, entry_point)
    clusters.calculate_ambiguity()

    problem.update({
        "original_cluster": clusters.serialize()
    })
    print(clusters.entropy)
    if clusters.entropy == 0:
        problem.update({key: None for key in [
            "repaired_requirement", "repaired_cluster", "clarifying_questions",
            "repaired_generated_programs", "repaired_failed_inputs_outputs",
            "repaired_requirement_woe", "repaired_woe_generated_programs",
            "repaired_woe_failed_inputs_outputs"]})
        problem["repaired_passk"] = None
        return problem

    inconsistent_solutions = [c.programs_str[0] for c in clusters.cluster_list]
    questions_prompt = prompt_generate_questions(requirement, inconsistent_solutions)
    questions_response = model.get_response(*[p["content"] for p in questions_prompt], True)
    clarifying_questions = unwrap(questions_response, "questions")
    print(clarifying_questions)

    repair_prompt = prompt_repair(requirement, clarifying_questions)
    repair_response = model.get_response(*[p["content"] for p in repair_prompt], True)
    answers = unwrap(repair_response, "answers")

    repaired_requirement = f"{requirement}\nClarification:\n{answers}\n\"\"\""

    programs = evaluator.generate_programs(requirement, entry_point, n_programs)
    # repaired_clusters = differential_tester_crosshair(repaired_programs, entry_point)
    repaired_clusters = differential_tester(programs, mutated_inputs, entry_point)
    repaired_clusters.calculate_ambiguity()
    pass_k = evaluator.pass_k_sample(repair_prompt,)

    problem.update({
        "repaired_requirement": repaired_requirement,
        "repaired_cluster": repaired_clusters.serialize(),
        "clarifying_questions": clarifying_questions,
        # "repaired_passk": passk_res[0],
        # "repaired_generated_programs": passk_res[1],
        # "repaired_failed_inputs_outputs": str(passk_res[2]),
        # "repaired_requirement_woe": woe_req,
        # "repaired_woe_passk": woe_passk_res[0],
        # "repaired_woe_generated_programs": woe_passk_res[1],
        # "repaired_woe_failed_inputs_outputs": str(woe_passk_res[2])
    })

    return problem


def main():
    model_name = "deepseek-v3-241226"
    # model_name = "qwen2.5-14b-instruct"
    # model_name = "gpt-4o"

    evaluator = SpecFixAccuracyEvaluator(model=model_name,
                                         differential_tester=differential_tester)
    model = Model(model_name)

    requirement = """
from typing import List\n\n\ndef pairs_sum_to_zero(l: List[int]) -> bool:\n    \"\"\"\n    pairs_sum_to_zero takes a list of integers as an input.\n    it returns True if there are two distinct elements in the list that\n    sum to zero, and False otherwise.\n    >>> pairs_sum_to_zero([1, 3, 5, 0])\n    False\n    >>> pairs_sum_to_zero([1, 3, -2, 1])\n    False\n    >>> pairs_sum_to_zero([1, 2, 3, 7])\n    False\n    >>> pairs_sum_to_zero([2, 4, -5, 3, 5, 7])\n    True\n    >>> pairs_sum_to_zero([1])\n    False\n    \"\"\"
 """
    entry_point = "pairs_sum_to_zero"
    examples = [[[[1, 3, 5, 0]], [[1, 3, -2, 1]], [[1, 2, 3, 7]], [[2, 4, -5, 3, 5, 7]], [[1]]],
                [[False], [False], [False], [True], [False]]]

    result = worker(requirement, entry_point, examples, evaluator, model, 20)

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
