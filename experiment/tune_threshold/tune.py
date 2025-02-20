import argparse

import jsonlines

from specfix.cluster import Clusters
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import calculate_mcc
from specfix.tester import differential_tester, ground_truth_tester


def tune_threshold(results, ground_truth):
    threshold_dict = {}
    for threshold in range(0, 5000):
        threshold = threshold / 1000
        predicts = [1 if result > threshold else 0 for result in results]
        mcc = calculate_mcc(ground_truth, predicts)
        threshold_dict[threshold] = mcc
    # Find the best threshold
    best_threshold = max(threshold_dict, key=threshold_dict.get)
    return best_threshold


def parse_problem(problem):
    requirement = problem['requirement']
    entry_point = problem['entry_point']
    return requirement, entry_point


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

    options = parser.parse_args()

    dataset = options.dataset
    dataset_path = options.dataset_path
    wo_example = "_woe" if options.without_example else ""

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        differential_tester=differential_tester,
        ground_truth_tester=ground_truth_tester,
    )
    ambiguity_results = []
    ground_truths = []
    with jsonlines.open(dataset_path) as reader:
        for i, problem in enumerate(reader):
            requirement, entry_point = parse_problem(problem)
            ground_truth = problem["ground_truth"]
            clusters = Clusters()
            clusters.deserialize(problem["clusters"])
            specfix_accuracy_evaluator.calculate_ambiguity(clusters, entry_point)
            ambiguity_results.append(clusters.ambiguity)
            ground_truths.append(ground_truth)
        best_threshold = tune_threshold(ambiguity_results, ground_truths)
        print(f"Best threshold for {dataset}{wo_example}: {best_threshold}")


if __name__ == "__main__":
    main()
