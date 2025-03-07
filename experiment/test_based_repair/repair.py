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


def parse_problem(problem):
    requirement = problem['requirement']
    examples = problem['input_output_examples']
    entry_point = problem['entry_point']
    task_id = problem['task_id']
    return requirement, entry_point, examples, task_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=20)
    parser.add_argument("-t", "--threshold", dest="threshold", type=float, default=0.7)
    parser.add_argument("-m", "--model", dest="model")
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

    options = parser.parse_args()

    model_name = options.model

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        differential_tester=differential_tester,
        ground_truth_tester=ground_truth_tester,
        model=model_name,
    )

    model_name = unify_model_name(model_name)

    dataset = options.dataset
    n_programs = options.number
    threshold = options.threshold
    wo_example = "_woe" if options.without_example else ""
    dataset_path = f"../../dataset/{dataset}{wo_example}.jsonl"
    original_results = []
    repaired_results = []

    if dataset == "humaneval" or dataset == "mbpp":
        inputs, outputs = get_evalplus_inputs_outputs(dataset)
    else:
        inputs, outputs = get_taco_lite_inputs_outputs()

    output_file = construct_output_file(dirname(abspath(__file__)), model_name, dataset, threshold, wo_example,
                                        "test_based_repair")

    problems = read_jsonl(dataset_path)
    with jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(problems):
            if i < 50:
                continue
            requirement, entry_point, examples, task_id = parse_problem(problem)
            repaired_requirement = None
            repaired_clusters = None
            print(f"Case {task_id}:\n {requirement}")
            test_inputs = ast.literal_eval(problem["llm_generated_inputs"][model_name])
            print(f"Test inputs:\n {test_inputs}")
            programs = specfix_accuracy_evaluator.parallel_generate_programs(requirement, n_programs, entry_point)
            clusters = specfix_accuracy_evaluator.get_clusters(programs, test_inputs, entry_point, examples)
            specfix_accuracy_evaluator.calculate_ambiguity(clusters, entry_point)
            print(f"Case {task_id}:\n clusters ambiguity: {clusters.ambiguity}")
            if clusters.ambiguity > threshold:
                cluster = clusters.get_largest_cluster()
                if cluster.test_consistency != 1:
                    repaired_code = specfix_accuracy_evaluator.test_based_repair(requirement, entry_point,
                                                                                 cluster.programs_str[0],
                                                                                 cluster.failed_input_output_examples)
                    repaired_requirement = specfix_accuracy_evaluator.repair_requirement(requirement, entry_point,
                                                                                         repaired_code)
                else:
                    other_programs = [c.programs_str[0] for c in clusters.cluster_list if c != cluster]
                    repaired_requirement = specfix_accuracy_evaluator.repair_largest_cluster_requirement(
                        requirement, entry_point,
                        other_programs,
                        cluster.programs_str[
                            0])
                print(f"Case {task_id}:\n Repaired requirement: {repaired_requirement}")
                repaired_programs = specfix_accuracy_evaluator.parallel_generate_programs(repaired_requirement,
                                                                                          n_programs, entry_point)
                repaired_clusters = specfix_accuracy_evaluator.get_clusters(repaired_programs, test_inputs,
                                                                            entry_point, examples)
                specfix_accuracy_evaluator.calculate_ambiguity(repaired_clusters, entry_point)

            original_result, repaired_result, failed_inputs_outputs = specfix_accuracy_evaluator.pass_k(requirement,
                                                                                                        repaired_requirement,
                                                                                                        inputs[i],
                                                                                                        outputs[i],
                                                                                                        entry_point,
                                                                                                        1)

            writer.write({
                "requirement": requirement,
                "repaired_requirement": repaired_requirement,
                "original_clusters": clusters.serialize(),
                "repaired_clusters": repaired_clusters.serialize() if repaired_clusters is not None else None,
                "original_result": original_result,
                "repaired_result": repaired_result,
                'original_program': failed_inputs_outputs[0],
                'repaired_program': failed_inputs_outputs[2],
                "original_failed_inputs_outputs": str(failed_inputs_outputs[1]),
                "repaired_failed_inputs_outputs": str(failed_inputs_outputs[3])
            })
            original_results.append(original_result)
            repaired_results.append(repaired_result)
            print(
                f"By case {task_id}, original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")
        print(
            f"{dataset}{wo_example} original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


if __name__ == "__main__":
    main()
