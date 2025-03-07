import argparse
import sys

import jsonlines
from os.path import abspath, dirname
from concurrent.futures import ThreadPoolExecutor, as_completed
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_output_file, unify_model_name

sys.set_int_max_str_digits(0)


def process_case(problem, specfix_accuracy_evaluator):
    requirement = problem['requirement']
    requirement_without_example = problem['requirement_without_examples']
    try:
        answer, reason = specfix_accuracy_evaluator.classification(requirement)
        answer_without_example, reason_without_example = specfix_accuracy_evaluator.classification(
            requirement_without_example)
        result = {
            'task_id': problem['task_id'],
            'requirement': requirement,
            'answer': answer,
            'reason': reason,
            'requirement_without_examples': requirement_without_example,
            'answer_without_examples': answer_without_example,
            'reason_without_examples': reason_without_example
        }
        return result
    except Exception as e:
        return {
            'task_id': problem['task_id'],
            'requirement': requirement,
            'answer': "",
            'reason': "",
            'requirement_without_examples': requirement_without_example,
            'answer_without_examples': "",
            'reason_without_examples': ""
        }


def main():
    # model_name = "deepseek-v3-241226"
    model_name = "qwen2.5-coder-32b-instruct"
    # model_name = "accounts/fireworks/models/qwen2p5-coder-32b-instruct"

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        model=model_name,
    )

    model_name = unify_model_name(model_name)
    dataset_path = "user_study.jsonl"

    output_file = construct_output_file(dirname(abspath(__file__)), model_name, "user_study", None, "",
                                        "vanilla_detect")

    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        with ThreadPoolExecutor(max_workers=50) as executor:
            # Prepare arguments for process_case
            futures = [executor.submit(process_case, problem, specfix_accuracy_evaluator) for
                       i, problem in
                       enumerate(reader)]
            results = [future.result() for future in as_completed(futures)]
            # sort results by task_id
            results = sorted(results, key=lambda x: int(x['task_id'].split('/')[-1]))
            writer.write_all(results)
        # for i, problem in enumerate(reader):
        #     print(f"Case {i}: {problem['requirement']}")
        #     result = process_case( problem, specfix_accuracy_evaluator)
        #     writer.write(result)


if __name__ == "__main__":
    main()
