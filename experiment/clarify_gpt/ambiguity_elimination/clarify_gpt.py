import argparse
import concurrent.futures
import jsonlines
import configparser
from os.path import dirname, abspath

from specfix.differential import differential_tester, ground_truth_tester
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import get_evalplus_inputs_outputs, get_taco_lite_inputs_outputs, construct_output_file


def parse_problem(problem):
    requirement = problem['requirement']
    examples = problem['input_output_examples']
    entry_point = problem['entry_point']
    task_id = problem['task_id']
    return requirement, entry_point, examples, task_id


def generate_programs(specfix_evaluator, requirement, n_programs, n_shot, initial=False):
    generated_programs = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        evaluator = specfix_evaluator.generate_initial_program_clarify_gpt if initial else specfix_evaluator.generate_program_clarify_gpt 
        futures = [executor.submit(evaluator, requirement, n_shot)
                   for _ in range(n_programs)]
        for future in concurrent.futures.as_completed(futures):
            prog = future.result()
            generated_programs.append(prog)

    return generated_programs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-m", "--model", dest="model")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=20)
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')
    parser.add_argument("-ns", "--nshot", dest="n_shot", default="zero_shot",
                        help="Number of shots (demonstrations) given to LLM before prompt: one_shot, two_shot, three_shot")

    options = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../../../.config')

    # model_name = "qwen2.5-coder-32b-instruct"
    model_name = options.model
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

    dataset = options.dataset
    wo_example = "_woe" if options.without_example else ""
    dataset_path = f"../../../dataset/{dataset}{wo_example}.jsonl"
    n_programs = options.number
    n_shot = options.n_shot
    threshold = 0
    original_results = []
    repaired_results = []

    if dataset == "humaneval" or dataset == "mbpp":
        inputs, outputs = get_evalplus_inputs_outputs(dataset)
    else:
        inputs, outputs = get_taco_lite_inputs_outputs()

    # Open dataset and output JSONL in one place
    results_path = "results.jsonl"
    
    output_file = construct_output_file(dirname(abspath(__file__)), model_name, dataset, threshold, wo_example,
                                        f"clarify_gpt_{n_shot}")
    # output_file = f"/{model_name}/{dataset}{wo_example}_clarify_gpt_{n_shot}.jsonl"
    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(reader):
            # Ignore the first 50 entries in the dataset, as we have used these for tuning our threshold
            if (i < 50):
                continue
            
            requirement, entry_point, examples, task_id = parse_problem(problem)
            
            # Skip extremely computationally expensive case
            if (task_id == "Mbpp/255"):
                continue

            print(f"Case {task_id}:\n {requirement}")

            # test_inputs = specfix_accuracy_evaluator.generate_tests_clarify_gpt(requirement, n_shot)
            # Use the same generated inputs for all tests to eliminate randomness for better result reproduction
            # print(problem['qwen2.5-coder-32b-instruct'])
            test_inputs = problem['llm_generated_inputs'][model_name]
            mutated_test_inputs = specfix_accuracy_evaluator.type_aware_mutation(test_inputs)
            print(f"Mutated test inputs:\n {mutated_test_inputs}")
            
            generated_programs = generate_programs(
                specfix_evaluator=specfix_accuracy_evaluator,
                requirement=requirement,
                n_programs=n_programs,
                n_shot=n_shot,
                initial=True
            )
            
            print("Differential Testing:\n")
            clusters = differential_tester(generated_programs, mutated_test_inputs, entry_point)
            clusters.set_input_output_examples(examples)
            ground_truth_tester(clusters, entry_point)
            
            repaired_requirement = None
            repaired_clusters = None
            print(f"Clusters entropy: {clusters.entropy}")
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

            if clusters.entropy > threshold:
                
                # Generate clarifying questions using requirements and clusters
                inconsistent_solutions = [c.programs_str[0] for c in clusters.get_cluster_list()]
                clarifying_questions = specfix_accuracy_evaluator.generate_clarifying_question_clarify_gpt(requirement, inconsistent_solutions, n_shot)
                print(f"Clarifying Questions:\n{clarifying_questions}")
                # Repair requirement 
                repaired_requirement = specfix_accuracy_evaluator.repair_requirements_clarify_gpt(requirement, clarifying_questions, n_shot)
                print(f"Repaired requirement:\n{repaired_requirement}")

                generated_programs = generate_programs(
                    specfix_evaluator=specfix_accuracy_evaluator,
                    requirement=repaired_requirement,
                    n_programs=n_programs,
                    n_shot=n_shot
                )
                
                print("Differential Testing:\n")
                repaired_clusters = differential_tester(generated_programs, mutated_test_inputs, entry_point)
                repaired_clusters.set_input_output_examples(examples)
                ground_truth_tester(clusters, entry_point)
            
            original_result, repaired_result, failed_inputs_ouputs = specfix_accuracy_evaluator.pass_k_clarify_gpt(requirement, repaired_requirement, inputs[i], outputs[i], entry_point, n_shot, 1)
            # original_result, repaired_result, failed_inputs_ouputs = specfix_accuracy_evaluator.pass_k_(requirement, repaired_requirement, inputs[i], outputs[i], entry_point, 1)

            writer.write({
                "requirement": requirement,
                "repaired_requirement": repaired_requirement,
                "original_clusters": clusters.serialize(),
                "repaired_clusters": repaired_clusters.serialize() if repaired_clusters is not None else None,
                "original_result": original_result,
                "repaired_result": repaired_result,
                "original_failed_inputs_outputs": str(failed_inputs_ouputs[0]),
                "repaired_failed_inputs_outputs": str(failed_inputs_ouputs[1])
            })
            original_results.append(original_result)
            repaired_results.append(repaired_result)
            print(
                f"By case {task_id}, original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")
        print(
            f"{dataset}{wo_example} original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")
        with jsonlines.open(f"{dataset}{wo_example}pass@1", mode='w', flush=True) as writer:
            writer.write({
                "original pass@1": sum(original_results) / len(original_results),
                "repaired pass@1": sum(repaired_results) / len(repaired_results),
                "improvement": sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)
            })
        


if __name__ == "__main__":
    main()
