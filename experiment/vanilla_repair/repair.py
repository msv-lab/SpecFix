import argparse
import random
import jsonlines
import configparser

from specfix.differential import differential_tester, ground_truth_testing
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_requirement
from specfix.correlation import point_biserial_correlation


def parse_problem(problem, dataset):
    if dataset == "taco_lite":
        requirement = construct_requirement(problem['question'], problem['starter_code'])
        canonical_solution = random.choice(problem['solutions'])
    else:
        requirement = problem['prompt']
        canonical_solution = problem['canonical_solution']
    entry_point = problem['entry_point']
    return requirement, canonical_solution, entry_point


def generate_and_test(mus_evaluator, requirement, test_inputs, entry_point, canonical_solution, n_programs):
    generated_programs = []
    for _ in range(n_programs):
        prog = mus_evaluator.generate_programs(requirement)
        generated_programs.append(prog)
        print(prog)

    clusters = differential_tester(generated_programs, test_inputs, entry_point)
    ground_truth_testing(canonical_solution, clusters, test_inputs, entry_point)
    return clusters


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=50)
    parser.add_argument("-t", "--threshold", dest="threshold", type=float, default=0.7)

    options = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../../.config')

    model_name = "qwen2.5-coder-14b-instruct"
    api_key = config['API_KEY']['qwen_key']

    mus_accuracy_evaluator = SpecFixAccuracyEvaluator(
        api_key=api_key,
        differential_tester=differential_tester,
        model=model_name,
        temperature=0
    )

    dataset = options.dataset
    dataset_path = options.dataset_path
    n_programs = options.number
    threshold = options.threshold
    entropy_list = []

    # Open dataset and output JSONL in one place
    output_file = f"{dataset}_{str(threshold)}_vanilla_repair.jsonl"
    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(reader):
            requirement, canonical_solution, entry_point = parse_problem(problem, dataset)
            print(f"Case {i}: {requirement}")

            test_inputs = mus_accuracy_evaluator.generate_tests(requirement)

            clusters = generate_and_test(
                mus_evaluator=mus_accuracy_evaluator,
                requirement=requirement,
                test_inputs=test_inputs,
                entry_point=entry_point,
                canonical_solution=canonical_solution,
                n_programs=n_programs
            )

            if clusters.entropy > threshold:
                repaired_requirement = mus_accuracy_evaluator.repair_requirements(requirement, clusters)
                print(f"Case {i}: Repaired requirement: {repaired_requirement}")

                repaired_clusters = generate_and_test(
                    mus_evaluator=mus_accuracy_evaluator,
                    requirement=repaired_requirement,
                    test_inputs=test_inputs,
                    entry_point=entry_point,
                    canonical_solution=canonical_solution,
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
                writer.write(result)

            entropy_list.append(clusters.entropy)

    with jsonlines.open(f"{dataset}_correlation.jsonl", mode='w', flush=True) as writer, \
            jsonlines.open(f"../../experiment/ambiguity_classification/{dataset}_pilot.jsonl") as pilot:
        labels = [problem['label'] for problem in pilot]
        correlation = point_biserial_correlation(entropy_list, labels)
        result = {
            'entropy': entropy_list,
            'labels': labels,
            'correlation': correlation
        }
        writer.write(result)


if __name__ == "__main__":
    main()
