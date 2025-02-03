import argparse
import os
import random
import concurrent.futures
import jsonlines
import configparser
from os.path import abspath, dirname

from specfix.differential import differential_tester, ground_truth_testing
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_requirement


def parse_problem(problem, dataset):
    if dataset == "taco_lite":
        requirement = construct_requirement(problem['requirement'], problem['starter_code'])
        examples = random.choice(problem['input_output_examples'])
    else:
        requirement = problem['requirement']
        examples = problem['input_output_examples']
    entry_point = problem['entry_point']
    return requirement, examples, entry_point


def generate_and_test(specfix_evaluator, requirement, test_inputs, entry_point, examples, n_programs):
    generated_programs = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(specfix_evaluator.generate_programs, requirement)
                   for _ in range(n_programs)]
        for future in concurrent.futures.as_completed(futures):
            prog = future.result()
            generated_programs.append(prog)

    print("Differential Testing")
    clusters = differential_tester(generated_programs, test_inputs, entry_point)
    ground_truth_testing(clusters, examples, entry_point)
    return clusters


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

    config = configparser.ConfigParser()
    config.read('../../.config')
    model_name = options.model
    api_key = ""
    if "qwen" in model_name:
        api_key = config['API_KEY']['qwen_key']
    elif "gpt" in model_name or "o1" in model_name:
        api_key = config['API_KEY']['openai_key']

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        api_key=api_key,
        differential_tester=differential_tester,
        model=model_name,
        temperature=0
    )

    dataset = options.dataset
    dataset_path = options.dataset_path
    n_programs = options.number
    threshold = options.threshold
    wo_example = "_woe" if options.without_example else ""

    cwd = dirname(abspath(__file__))
    model_name = model_name.replace(".", "")

    if not os.path.exists(f"{cwd}/{model_name}"):
        os.mkdir(f"{cwd}/{model_name}")

    # Open dataset and output JSONL in one place
    output_file = f"{cwd}/{model_name}/{dataset}_{str(int(threshold * 100))}{wo_example}_vanilla_repair.jsonl"
    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(reader):
            requirement, examples, entry_point = parse_problem(problem, dataset)
            print(f"Case {i}: {requirement}")

            test_inputs = specfix_accuracy_evaluator.generate_tests(requirement)
            print(f"Test inputs: {test_inputs}")
            clusters = generate_and_test(
                specfix_evaluator=specfix_accuracy_evaluator,
                requirement=requirement,
                test_inputs=test_inputs,
                entry_point=entry_point,
                examples=examples,
                n_programs=n_programs
            )
            print(f"Case {i}: clusters entropy: {clusters.entropy}")
            if clusters.entropy > threshold:
                repaired_requirement = specfix_accuracy_evaluator.vanilla_repair_requirements(requirement)
                print(f"Case {i}: Repaired requirement: {repaired_requirement}")

                repaired_clusters = generate_and_test(
                    specfix_evaluator=specfix_accuracy_evaluator,
                    requirement=repaired_requirement,
                    test_inputs=test_inputs,
                    entry_point=entry_point,
                    examples=examples,
                    n_programs=n_programs
                )
                entropy_diff = clusters.entropy - repaired_clusters.entropy
                result = {
                    'original_requirement': requirement,
                    'original_clusters': clusters.serialize(),
                    'repaired_requirement': repaired_requirement,
                    'repaired_clusters': repaired_clusters.serialize(),
                    'entropy_diff': entropy_diff
                }
            else:
                result = {
                    'original_requirement': requirement,
                    'original_clusters': clusters.serialize(),
                }
            writer.write(result)


if __name__ == "__main__":
    main()
