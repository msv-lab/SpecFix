import argparse
import jsonlines
import configparser
from specfix.differential import differential_tester
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_requirement
from specfix.correlation import point_biserial_correlation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=30, )
    parser.add_argument("-t", "--threshold", dest="threshold", type=float, default=0.8)

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
    N = options.number
    threshold = options.threshold
    entropy_list = []
    if dataset == "taco_lite":
        with jsonlines.open(dataset_path) as reader, jsonlines.open(f"{dataset}_{str(threshold)}_vanilla_repair.jsonl",
                                                                    mode='w',
                                                                    flush=True) as writer:
            for i, problem in enumerate(reader):
                entry_point = problem['entry_point']
                requirement = construct_requirement(problem['question'], problem['starter_code'])
                print(f"Case {i}: {requirement}")
                test_inputs = mus_accuracy_evaluator.generate_tests(requirement)

                generated_programs = []
                for n in range(N):
                    prog = mus_accuracy_evaluator.generate_programs(requirement)
                    generated_programs.append(prog)
                    print(prog)

                print(f"Case {i}: Differential testing...")
                clusters = differential_tester(generated_programs, test_inputs, entry_point)
                if clusters.entropy > threshold:
                    repaired_requirement = mus_accuracy_evaluator.repair_requirements(requirement, clusters)
                    print(f"Case {i}: Repaired requirement: {repaired_requirement}")
                    generated_programs = []
                    for n in range(N):
                        prog = mus_accuracy_evaluator.generate_programs(requirement)
                        generated_programs.append(prog)
                        print(prog)

                    print(f"Case {i}: Differential testing...")
                    repaired_clusters = differential_tester(generated_programs, test_inputs, entry_point)
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
    elif dataset == "humaneval" or dataset == "mbpp":
        with jsonlines.open(dataset_path) as reader, jsonlines.open(f"{dataset}_{str(threshold)}_vanilla_repair.jsonl",
                                                                    mode='w',
                                                                    flush=True) as writer:
            for i, problem in enumerate(reader):
                requirement = problem['prompt']
                entry_point = problem['entry_point']
                print(f"Case {requirement}")
                test_inputs = mus_accuracy_evaluator.generate_tests(requirement)

                generated_programs = []
                for n in range(N):
                    prog = mus_accuracy_evaluator.generate_programs(requirement)
                    generated_programs.append(prog)
                    print(prog)

                print(f"Case {i}: Differential testing...")
                clusters = differential_tester(generated_programs, test_inputs, entry_point)
                if clusters.entropy > threshold:
                    repaired_requirement = mus_accuracy_evaluator.repair_requirements(requirement, clusters)
                    print(f"Case {i}: Repaired requirement: {repaired_requirement}")
                    generated_programs = []
                    for n in range(N):
                        prog = mus_accuracy_evaluator.generate_programs(requirement)
                        generated_programs.append(prog)
                        print(prog)

                    print(f"Case {i}: Differential testing...")
                    repaired_clusters = differential_tester(generated_programs, test_inputs, entry_point)
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
    with jsonlines.open(f"{dataset}_correlation.jsonl", mode='w', flush=True) as writer, jsonlines.open(
            f"../../experiment/ambiguity_classification/{dataset}_pilot.jsonl") as pilot:
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
