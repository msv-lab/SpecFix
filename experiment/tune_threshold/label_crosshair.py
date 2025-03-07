import argparse
from os.path import dirname, abspath

import jsonlines

from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import read_jsonl, construct_output_file
from specfix.tester import differential_tester, ground_truth_tester, differential_tester_crosshair


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=20)
    parser.add_argument("-m", "--model", dest="model")
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

    options = parser.parse_args()
    dataset = options.dataset
    model_name = options.model
    dataset_path = options.dataset_path
    n_programs = options.number
    wo_example = "_woe" if options.without_example else ""

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        differential_tester=differential_tester_crosshair,
        ground_truth_tester=ground_truth_tester,
        model=model_name
    )

    problems = read_jsonl(dataset_path)
    output_file = construct_output_file(dirname(abspath(__file__)), model_name, dataset, None, wo_example,
                                        "ambiguity_detection_crosshair")
    with jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(problems):
            requirement, entry_point = problem["requirement"], problem["entry_point"],
            print(f"Case {i}: {requirement}")

            programs = specfix_accuracy_evaluator.parallel_generate_programs(requirement, n_programs,entry_point)
            clusters = specfix_accuracy_evaluator.get_clusters_crosshair(programs, entry_point,
                                                                         problem["input_output_examples"])
            specfix_accuracy_evaluator.calculate_ambiguity(clusters, entry_point)
            problem["clusters"] = clusters.serialize()
            writer.write(problem)


if __name__ == "__main__":
    main()
