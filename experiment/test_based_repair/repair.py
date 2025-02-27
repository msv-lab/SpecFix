import argparse
from os.path import dirname, abspath

import jsonlines

from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import get_evalplus_inputs_outputs, construct_output_file
from specfix.tester import differential_tester, ground_truth_tester


def parse_problem(problem):
    requirement = problem['requirement']
    examples = problem['input_output_examples']
    entry_point = problem['entry_point']
    return requirement, entry_point, examples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=50)
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

    dataset = options.dataset
    dataset_path = options.dataset_path
    n_programs = options.number
    threshold = options.threshold
    wo_example = "_woe" if options.without_example else ""
    original_results = []
    repair_results = []

    if dataset == "humaneval" or dataset == "mbpp":
        inputs, outputs = get_evalplus_inputs_outputs(dataset)

    output_file = construct_output_file(dirname(abspath(__file__)), model_name, dataset, threshold, wo_example,
                                        "repair")

    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        reader = list(reader)[50:]
        for i, problem in enumerate(reader):
            requirement, entry_point, examples = parse_problem(problem)
            repaired_requirement = None
            print(f"Case {i + 50}: {requirement}")

            test_inputs = specfix_accuracy_evaluator.generate_tests(requirement, entry_point)
            print(f"Test inputs: {test_inputs}")
            programs = specfix_accuracy_evaluator.parallel_generate_programs(requirement, n_programs)
            clusters = specfix_accuracy_evaluator.get_clusters(programs, test_inputs, entry_point, examples)
            specfix_accuracy_evaluator.calculate_ambiguity(clusters, entry_point)
            print(f"Case {i + 50}: clusters ambiguity: {clusters.ambiguity}")
            if clusters.ambiguity > threshold:
                cluster = clusters.get_largest_cluster()
                if cluster.test_consistency != 1:
                    repaired_code = specfix_accuracy_evaluator.test_based_repair(requirement, requirement,
                                                                                 cluster.failed_input_output_examples)
                    repaired_requirement = specfix_accuracy_evaluator.inverse_requirement(repaired_code)
                else:
                    other_programs = [c.programs_str[0] for c in clusters.cluster_list if c != cluster]
                    repaired_requirement = specfix_accuracy_evaluator.repair_largest_cluster_requirement(requirement,
                                                                                                         other_programs,
                                                                                                         cluster.programs_str[
                                                                                                             0])
                print(f"Case {i + 50}: Repaired requirement: {repaired_requirement}")
            if dataset == "humaneval" or dataset == "mbpp":
                original_result, repaired_result = specfix_accuracy_evaluator.pass_k_repair(requirement,
                                                                                            repaired_requirement,
                                                                                            inputs[i + 50],
                                                                                            outputs[i + 50],
                                                                                            entry_point, 1)
            else:
                original_result, repaired_result = specfix_accuracy_evaluator.pass_k_repair(requirement,
                                                                                            repaired_requirement,
                                                                                            problem["inputs"],
                                                                                            problem["outputs"],
                                                                                            entry_point,
                                                                                            1)
            writer.write({
                "requirement": requirement,
                "ambiguous": clusters.ambiguity,
                "t_consistency": clusters.weighted_t_consistency,
                "original_result": original_result,
                "repaired_requirement": repaired_requirement,
                "repaired_result": repaired_result
            })
            original_results.append(original_result)
            repair_results.append(repaired_result)
        print(
            f"{dataset}{wo_example} original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repair_results) / len(repair_results)}, Improvement: {sum(repair_results) / len(repair_results) - sum(original_results) / len(original_results)}")


if __name__ == "__main__":
    main()
