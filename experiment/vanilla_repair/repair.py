import argparse
import jsonlines
from os.path import abspath, dirname
from concurrent.futures import ThreadPoolExecutor
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_output_file


def process_case(i, problem, specfix_accuracy_evaluator, writer):
    requirement = problem['requirement']
    print(f"Case {i}: {requirement}")

    answer, reason = specfix_accuracy_evaluator.classification(requirement)

    if answer == "Yes":
        repaired_requirement = specfix_accuracy_evaluator.vanilla_repair_requirements(requirement)
        print(f"Case {i}: Repaired requirement: {repaired_requirement}")
        result = {
            'original_requirement': requirement,
            'ambiguous': answer,
            'reason': reason,
            'repaired_requirement': repaired_requirement,
        }
    else:
        result = {
            'original_requirement': requirement,
            'ambiguous': answer,
        }

    writer.write(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=50)
    parser.add_argument("-m", "--model", dest="model")
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

    options = parser.parse_args()
    model_name = options.model

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        model=model_name,
    )

    dataset = options.dataset
    dataset_path = options.dataset_path
    threshold = options.threshold
    wo_example = "_woe" if options.without_example else ""

    output_file = construct_output_file(dirname(abspath(__file__)), model_name, dataset, threshold, wo_example,
                                        "vanilla_repair")

    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        with ThreadPoolExecutor() as executor:
            # Submit all tasks to the executor
            futures = [executor.submit(process_case, i, problem, specfix_accuracy_evaluator, writer)
                       for i, problem in enumerate(reader)]

            # Wait for all tasks to complete
            for future in futures:
                future.result()


if __name__ == "__main__":
    main()
