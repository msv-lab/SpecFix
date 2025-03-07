import argparse
import ast
import sys
from os.path import dirname, abspath

import jsonlines

from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import get_evalplus_inputs_outputs, construct_output_file, read_jsonl, get_taco_lite_inputs_outputs, \
    unify_model_name
from specfix.tester import differential_tester, ground_truth_tester

sys.set_int_max_str_digits(0)
humaneval_dataset = read_jsonl("../../dataset/humaneval.jsonl")
mbpp_dataset = read_jsonl("../../dataset/mbpp.jsonl")
taco_lite_dataset = read_jsonl("../../dataset/taco_lite.jsonl")


def parse_problem(problem):
    requirement = problem['requirement']
    requirement_without_examples = problem['requirement_without_examples']
    examples = problem['input_output_examples']
    entry_point = problem['entry_point']
    task_id = problem['task_id']
    return requirement, requirement_without_examples, entry_point, examples, task_id


def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-n", "--program_number", dest="number", type=int, default=20)
    # parser.add_argument("-t", "--threshold", dest="threshold", type=float, default=0.7)
    # parser.add_argument("-m", "--model", dest="model")
    #
    # options = parser.parse_args()

    model_name = "qwen2.5-coder-32b-instruct"
    model_name = "accounts/fireworks/models/qwen2p5-coder-32b-instruct"
    # model_name = "deepseek-v3-241226"

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        differential_tester=differential_tester,
        ground_truth_tester=ground_truth_tester,
        model=model_name,
    )

    model_name = unify_model_name(model_name)

    n_programs = 20
    threshold = 0.306
    dataset_path = "user_study.jsonl"

    output_file = construct_output_file(dirname(abspath(__file__)), model_name, "user_study", threshold, "",
                                        "specifx_detect")

    problems = read_jsonl(dataset_path)
    with jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(problems):
            print("Processing problem {}/{}".format(i + 1, len(problems)))
            requirement, requirement_without_examples, entry_point, examples, task_id = parse_problem(problem)
            test_inputs = ast.literal_eval(problem["llm_generated_inputs"][model_name])

            print(f"Test inputs:\n {test_inputs}")
            programs = specfix_accuracy_evaluator.parallel_generate_programs(requirement, n_programs, entry_point)
            clusters = specfix_accuracy_evaluator.get_clusters(programs, test_inputs, entry_point, examples)
            specfix_accuracy_evaluator.calculate_ambiguity(clusters, entry_point)
            print(f"Case {task_id}:\n clusters ambiguity: {clusters.ambiguity}")
            if clusters.ambiguity > threshold:
                problem["answer"] = "Yes"
            else:
                problem["answer"] = "No"

            programs_woe = specfix_accuracy_evaluator.parallel_generate_programs(requirement_without_examples,
                                                                                 n_programs, entry_point)
            clusters_woe = specfix_accuracy_evaluator.get_clusters(programs_woe, test_inputs, entry_point, examples)
            specfix_accuracy_evaluator.calculate_ambiguity(clusters_woe, entry_point)
            if clusters_woe.ambiguity > threshold:
                problem["answer_without_examples"] = "Yes"
            else:
                problem["answer_without_examples"] = "No"
            writer.write({
                "requirement": problem["requirement"],
                "requirement_without_examples": problem["requirement_without_examples"],
                "answer": problem["answer"],
                "answer_without_examples": problem["answer_without_examples"],
                "clusters": clusters.serialize(),
                "clusters_woe": clusters_woe.serialize()
            })


if __name__ == "__main__":
    main()
