import argparse
import ast
from os.path import dirname, abspath

import jsonlines

from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import read_jsonl, construct_output_file, unify_model_name
from specfix.tester import differential_tester, ground_truth_tester


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=20)
    parser.add_argument("-m", "--model", dest="model")
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

    options = parser.parse_args()
    dataset = options.dataset
    model_name = options.model
    wo_example = "_woe" if options.without_example else ""
    dataset_path = f"../../dataset/{dataset}{wo_example}_pilot.jsonl"
    n_programs = options.number

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        differential_tester=differential_tester,
        ground_truth_tester=ground_truth_tester,
        model=model_name
    )

    model_name = unify_model_name(model_name)
    problems = read_jsonl(dataset_path)
    output_file = construct_output_file(dirname(abspath(__file__)), model_name, dataset, None, wo_example,
                                        "label")
    with jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(problems):
            requirement, entry_point = problem["requirement"], problem["entry_point"],
            print(f"Case {i}: {requirement}")

            test_inputs = ast.literal_eval(problem["llm_generated_inputs"][model_name])
            if not test_inputs:
                continue
            print(f"Test inputs: {test_inputs}")
            programs = specfix_accuracy_evaluator.parallel_generate_programs(requirement, n_programs, entry_point)
            clusters = specfix_accuracy_evaluator.get_clusters(programs, test_inputs, entry_point,
                                                               problem["input_output_examples"])
            specfix_accuracy_evaluator.calculate_ambiguity(clusters, entry_point)
            problem["clusters"] = clusters.serialize()
            writer.write(problem)


if __name__ == "__main__":
    main()
