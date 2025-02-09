import argparse

import jsonlines

from specfix.differential import differential_tester, ground_truth_tester
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_output_file


def parse_problem(problem):
    requirement = problem['requirement']
    examples = problem['examples']
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
        temperature=0
    )

    dataset = options.dataset
    dataset_path = options.dataset_path
    n_programs = options.number
    threshold = options.threshold
    wo_example = "_woe" if options.without_example else ""

    output_file = construct_output_file(model_name, dataset, threshold, wo_example, "test_based_repair")
    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(reader):
            requirement, entry_point, examples = parse_problem(problem)
            print(f"Case {i}: {requirement}")

            test_inputs = specfix_accuracy_evaluator.generate_tests(requirement)
            print(f"Test inputs: {test_inputs}")
            programs = specfix_accuracy_evaluator.parallel_generate_programs(requirement, n_programs)
            clusters = specfix_accuracy_evaluator.get_clusters(programs, test_inputs, examples, entry_point)
            specfix_accuracy_evaluator.calculate_ambiguity(clusters, examples, entry_point)
            print(f"Case {i}: clusters entropy: {clusters.entropy}")
            if clusters.ambiguity > threshold:
                cluster = clusters.get_largest_cluster()
                if cluster.test_consistency != 1:
                    repaired_code = specfix_accuracy_evaluator.test_based_repair(requirement, requirement,
                                                                                 cluster.failed_semantic_input_output)
                    repaired_requirement = specfix_accuracy_evaluator.inverse_requirement(repaired_code)
                else:
                    other_programs = [c.program_str[0] for c in clusters.clusters if c != cluster]
                    repaired_requirement = specfix_accuracy_evaluator.repair_largest_cluster_requirement(requirement,
                                                                                                         other_programs,
                                                                                                         cluster.programs_str[
                                                                                                             0])
                print(f"Case {i}: Repaired requirement: {repaired_requirement}")

                repaired_programs = specfix_accuracy_evaluator.parallel_generate_programs(repaired_requirement,
                                                                                          n_programs)
                repaired_clusters = specfix_accuracy_evaluator.get_clusters(repaired_programs, test_inputs, examples,
                                                                            entry_point)
                specfix_accuracy_evaluator.calculate_ambiguity(repaired_clusters, examples, entry_point)
                entropy_diff = clusters.entropy - repaired_clusters.entropy
                ambiguity_diff = clusters.ambiguity - repaired_clusters.ambiguity
                result = {
                    'original_requirement': requirement,
                    'original_clusters': clusters.serialize(),
                    'repaired_requirement': repaired_requirement,
                    'repaired_clusters': repaired_clusters.serialize(),
                    'entropy_diff': entropy_diff,
                    'ambiguity_diff': ambiguity_diff,
                }
            else:
                result = {
                    'original_requirement': requirement,
                    'original_clusters': clusters.serialize(),
                }
            writer.write(result)


if __name__ == "__main__":
    main()
