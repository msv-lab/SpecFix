import argparse
import random
import concurrent.futures
import jsonlines
import configparser
from scipy.stats import pointbiserialr
from specfix.differential import differential_tester, ground_truth_testing
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_requirement


def parse_problem(problem, dataset):
    if dataset == "taco_lite":
        requirement = construct_requirement(problem['requirement'], problem['starter_code'])
        canonical_solution = random.choice(problem['solutions'])
    else:
        requirement = problem['requirement']
        canonical_solution = problem['canonical_solution']
    entry_point = problem['entry_point']
    return requirement, canonical_solution, entry_point


def generate_and_test(specfix_evaluator, requirement, test_inputs, entry_point, canonical_solution, n_programs):
    generated_programs = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(specfix_evaluator.generate_programs_clarify_gpt, requirement)
                   for _ in range(n_programs)]
        for future in concurrent.futures.as_completed(futures):
            prog = future.result()
            generated_programs.append(prog)

    print("Differential Testing")
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
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

    options = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../../.config')

    model_name = "qwen2.5-coder-14b-instruct"
    api_key = config['API_KEY']['qwen_key']

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
    entropy_list = []

    # Open dataset and output JSONL in one place
    output_file = f"{dataset}_{str(int(threshold * 100))}{wo_example}_clarify_gpt.jsonl"
    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(reader):
            requirement, canonical_solution, entry_point = parse_problem(problem, dataset)
            print(f"Case {i}: {requirement}")

            test_inputs = specfix_accuracy_evaluator.generate_tests_clarify_gpt(requirement)
            print(f"Test inputs: {test_inputs}")
            clusters = generate_and_test(
                specfix_evaluator=specfix_accuracy_evaluator,
                requirement=requirement,
                test_inputs=test_inputs,
                entry_point=entry_point,
                canonical_solution=canonical_solution,
                n_programs=n_programs
            )
            print(f"Case {i}: clusters entropy: {clusters.entropy}")
            if clusters.entropy > threshold:
                
                # Generate clarifying questions using requirements and clusters
                print("TESTING TESTING TESTING TESTING")
                
                inconsistent_solutions = [c.programs_str[0] for c in clusters.clusters]
                print(inconsistent_solutions)
                print("TESTING END TESTING END TESTING END")
                clarifying_questions = specfix_accuracy_evaluator.generate_clarifying_question_clarify_gpt(requirement, inconsistent_solutions)
                
                # Repair requirement 
                print("REQUIREMENT HAHAHAHA")
                print(requirement)
                repaired_requirement = specfix_accuracy_evaluator.repair_requirements_clarify_gpt(requirement, inconsistent_solutions, clarifying_questions)
                print(f"Case {i}: Repaired requirement: {repaired_requirement}")

                repaired_clusters = generate_and_test(
                    specfix_evaluator=specfix_accuracy_evaluator,
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
            else:
                result = {
                    'original_requirement': requirement,
                    'original_clusters': clusters.serialize(),
                }
            writer.write(result)
            entropy_list.append(clusters.entropy)

    with jsonlines.open(f"{dataset}{wo_example}_pilot_correlation.jsonl", mode='w', flush=True) as writer, \
            jsonlines.open(f"../ambiguity_classification/{dataset}_pilot_classification.jsonl") as pilot:
        labels = [1 if problem['label'] == 'Yes' else 0 for problem in pilot]

        # The point biserial correlation is used to measure the relationship between a binary variable, x, and a continuous variable, y. Like other correlation coefficients, this one varies between -1 and +1 with 0 implying no correlation. Correlations of -1 or +1 imply a determinative relationship.
        correlation, p_value = pointbiserialr(entropy_list, labels)

        result = {
            'entropy': entropy_list,
            'labels': labels,
            'correlation': correlation,
            'p_value': p_value
        }
        writer.write(result)


if __name__ == "__main__":
    main()
