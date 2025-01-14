import jsonlines
import random
import configparser
import argparse

from mus.utils import construct_requirement
from mus.evaluator import MUSAccuracyEvaluator
from mus.differential import differential_tester, model_verifier
from evalplus.data import get_human_eval_plus, get_mbpp_plus


def process_problems(
        problems,
        output_ambiguity_file_path,
        output_incorrect_file_path,
        mus_accuracy_evaluator,
        verifier_name,
        verifier_api_key,
        N=10,
        max_count=100
):
    ambiguity = []
    incorrect_generation = []

    with jsonlines.open(output_ambiguity_file_path, "w", flush=True) as ambiguity_file, jsonlines.open(
            output_incorrect_file_path, "w", flush=True) as incorrect_file:

        for i, problem in enumerate(problems):
            if i >= max_count:
                break

            requirement = problem['question'] if 'question' in problem else problems[problem]['prompt']
            entry_point = problem['entry_point'] if 'entry_point' in problem else problems[problem]['entry_point']
            # 若是 TACO 题目，也可能在 problem 里存了 starter_code，需要构造 requirement
            if 'question' in problem and 'starter_code' in problem:
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

            if len(clusters) > 1:
                print(f"Case {i}: *********Discrepancy found!*********")

                cluster1, cluster2 = random.sample(clusters, k=2)

                for test_i, test_input in enumerate(test_inputs):
                    if cluster1.outputs[test_i] != cluster2.outputs[test_i]:
                        res, explanation = model_verifier(
                            requirement,
                            [random.choice(cluster1.programs_str), random.choice(cluster2.programs_str)],
                            test_input,
                            [cluster1.outputs[test_i], cluster2.outputs[test_i]],
                            model=verifier_name,
                            api_key=verifier_api_key
                        )
                        if not res:
                            print("*********Incorrect generation found!*********")
                            problem_dict = {
                                'requirement': requirement,
                                'test_input': test_input,
                                'program1': cluster1.programs_str,
                                'program2': cluster2.programs_str,
                                'output1': cluster1.outputs[test_i],
                                'output2': cluster2.outputs[test_i],
                                'explanation': explanation
                            }
                            incorrect_generation.append(problem_dict)
                            try:
                                incorrect_file.write(problem_dict)
                            except Exception as e:
                                pass
                            break
                else:
                    print("*********Ambiguity found!*********")
                    problem_dict = {
                        'requirement': requirement,
                        'test_input': test_input,
                        'program1': cluster1.programs_str,
                        'program2': cluster2.programs_str,
                        'output1': cluster1.outputs[test_i],
                        'output2': cluster2.outputs[test_i],
                        'explanation': explanation
                    }
                    ambiguity.append(problem_dict)
                    try:
                        ambiguity_file.write(problem_dict)
                    except Exception as e:
                        print(f"Error writing ambiguity to file: {e}")
            else:
                print(f"Case {i}: No discrepancy found.")

    # 打印统计结果
    print("Ambiguity number:", len(ambiguity))
    print("Ambiguity percentage:", len(ambiguity) / max_count)
    print("Incorrect generation number:", len(incorrect_generation))
    print("Incorrect generation percentage:", len(incorrect_generation) / max_count)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")

    options = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../../.config')

    model_name = "qwen2.5-coder-14b-instruct"
    api_key = config['API_KEY']['qwen_key']

    verifier_name = "o1-mini"
    verifier_api_key = config['API_KEY']['openai_key']

    mus_accuracy_evaluator = MUSAccuracyEvaluator(
        api_key=api_key,
        differential_tester=differential_tester,
        model=model_name,
        temperature=0
    )

    dataset = options.dataset
    dataset_path = options.dataset_path

    if dataset == "taco_lite":
        with jsonlines.open(dataset_path) as reader:
            process_problems(
                reader,
                output_ambiguity_file_path="taco_ambiguity.jsonl",
                output_incorrect_file_path="taco_incorrect_generation.jsonl",
                mus_accuracy_evaluator=mus_accuracy_evaluator,
                verifier_name=verifier_name,
                verifier_api_key=verifier_api_key,
                N=10,
                max_count=100
            )

    elif dataset == "humaneval":
        problems = get_human_eval_plus()
        process_problems(
            problems,
            output_ambiguity_file_path="humaneval_ambiguity.jsonl",
            output_incorrect_file_path="humaneval_incorrect_generation.jsonl",
            mus_accuracy_evaluator=mus_accuracy_evaluator,
            verifier_name=verifier_name,
            verifier_api_key=verifier_api_key,
            N=10,
            max_count=100
        )

    elif dataset == "mbpp":
        problems = get_mbpp_plus()
        process_problems(
            problems,
            output_ambiguity_file_path="mbpp_ambiguity.jsonl",
            output_incorrect_file_path="mbpp_incorrect_generation.jsonl",
            mus_accuracy_evaluator=mus_accuracy_evaluator,
            verifier_name=verifier_name,
            verifier_api_key=verifier_api_key,
            N=10,
            max_count=100
        )


if __name__ == "__main__":
    main()
