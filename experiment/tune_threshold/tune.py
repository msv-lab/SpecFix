import argparse
from os.path import dirname, abspath

import jsonlines

from specfix.differential import differential_tester, ground_truth_tester
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_output_file, unwrap, calculate_f1_score


def tune_threshold(results, ground_truth):
    threshold_dict = {}
    for threshold in range(0, 1000):
        threshold = threshold / 1000
        results = ["Ambiguous" if result["ambiguity"] > threshold else "Unambiguous" for result in results]
        f1_score = calculate_f1_score(results, ground_truth)
        threshold_dict[threshold] = f1_score
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
    parser.add_argument("-e", "--example_dataset_path", dest="example_dataset_path",
                        help="Path to dataset with examples")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=50)
    parser.add_argument("-m", "--model", dest="model")
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

    options = parser.parse_args()

    model_name = options.model
    dataset = options.dataset
    dataset_path = options.dataset_path
    example_dataset_path = options.example_dataset
    n_programs = options.number
    wo_example = "_woe" if options.without_example else ""

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        differential_tester=differential_tester,
        ground_truth_tester=ground_truth_tester,
        model=model_name
    )

    output_file = construct_output_file(dirname(abspath(__file__)), model_name, dataset, None, wo_example,
                                        "labelled")
    with jsonlines.open(example_dataset_path) as example_reader:
        examples = [example for example in example_reader]
    ambiguity_results = []
    ground_truths = []
    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(reader):
            requirement, entry_point = parse_problem(problem)
            example = examples[i]["examples"]
            ground_truth = problem["ground_truth"]
            clusters = problem["clusters"]
            specfix_accuracy_evaluator.calculate_ambiguity(clusters, example, entry_point)
            ambiguity_results.append(clusters.ambiguity)
            ground_truths.append(ground_truth)
        best_threshold = tune_threshold(ambiguity_results, ground_truths)
        print(f"Best threshold: {best_threshold}")


if __name__ == "__main__":
    main()
