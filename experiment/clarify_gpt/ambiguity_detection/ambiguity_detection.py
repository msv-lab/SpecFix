import argparse
import random
import concurrent.futures
import jsonlines
import configparser
import re
from scipy.stats import pointbiserialr
from specfix.differential import differential_tester, calculate_accuracy_ground_truth_testing
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


def generate_and_test(specfix_evaluator, requirement, test_inputs, entry_point, canonical_solution, n_programs, n_shot, initial=False):
    generated_programs = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        evaluator = specfix_evaluator.generate_initial_programs_clarify_gpt if initial else specfix_evaluator.generate_programs_clarify_gpt 
        futures = [executor.submit(evaluator, requirement, n_shot)
                   for _ in range(n_programs)]
        for future in concurrent.futures.as_completed(futures):
            prog = future.result()
            generated_programs.append(prog)

    print("Differential Testing")
    clusters = differential_tester(generated_programs, test_inputs, entry_point)
    calculate_accuracy_ground_truth_testing(canonical_solution, clusters, test_inputs, entry_point)
    return clusters


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=50)
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')
    parser.add_argument("-ns", "--nshot", dest="n_shot", default="zero_shot",
                        help="Number of shots (demonstrations) given to LLM before prompt: one_shot, two_shot, three_shot")

    options = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../../../.config')

    model_name = "qwen2.5-coder-32b-instruct"
    api_key = config['API_KEY']['qwen_key']

    # For all LLMs, we set the top p to 0.95, the frequency_penalty to 0. The max_tokens represents the maximum
    # number of tokens to be generated, which is set to 800 for the prompt of asking clarifying questions
    # and 300 for other prompts. In particular, we set the temperature to 0, except when sampling code
    # solutions, for which the temperature is set to 0.8.
    
    # Frequency penalty defaults to 0
    # max tokens varies depending on prompt, is a parameter of get_response in our model API
    
    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        api_key=api_key,
        differential_tester=differential_tester,
        model=model_name,
        temperature=0,
        top_p=0.95
    )
    # ONLY TESTED FOR CLARIFY_MBPP
    dataset = options.dataset
    dataset_path = options.dataset_path
    n_programs = options.number
    wo_example = "_woe" if options.without_example else ""
    n_shot = options.n_shot

    # Open dataset and output JSONL in one place
    output_file = f"{dataset}{wo_example}_clarify_gpt_{n_shot}.jsonl"
    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(reader):
            requirement, canonical_solution, entry_point = parse_problem(problem, dataset)

            print(f"Case {i}: {requirement}")

            test_inputs = specfix_accuracy_evaluator.generate_tests_clarify_gpt(requirement, n_shot)
            mutated_test_inputs = specfix_accuracy_evaluator.type_aware_mutation(test_inputs)
            print(f"Test inputs: {test_inputs}")
            print(f"Mutated test inputs: {mutated_test_inputs}")
            clusters = generate_and_test(
                specfix_evaluator=specfix_accuracy_evaluator,
                requirement=requirement,
                test_inputs=mutated_test_inputs,
                entry_point=entry_point,
                canonical_solution=canonical_solution,
                n_programs=n_programs,
                n_shot=n_shot,
                initial=True
            )
            
            print(f"Case {i}: clusters entropy: {clusters.entropy}")
            # Note: in ClarifyGPT's case, our threshold is 0. They think a solution is ambiguous if there are ANY non identical solutions
            # see quote:
            
            # First, we employ a two-step code consistency check
            # to decide when to ask clarifying questions. We are motivated by the observation that feeding
            # a clear requirement to LLMs usually results in generating diverse code snippets that behave
            # consistently, i.e., given the same test inputs, those different code snippets will likely return the same
            # outputs. While feeding an unclear requirement, LLMs are likely to generate diverse code snippets
            # that behave differently. Specifically, in the first step, ClarifyGPT aims to generate numerous
            # high-quality test inputs for a given requirement via type-aware mutation. In the second step,
            # ClarifyGPT inputs the given requirement into an LLM to sample 𝑛 code solutions and checks
            # whether they produce identical outputs when tested with the generated input. If the outputs are
            # not identical, ClarifyGPT determines that the requirement requires further clarification; and vice
            # versa
            ambiguity = 0
            
            if clusters.entropy > 0:
                ambiguity = 1
            
            result = {
                'task_id': problem['task_id'],
                'requirement': requirement,
                'Ambiguity': ambiguity,
            }
            writer.write(result)


if __name__ == "__main__":
    main()
