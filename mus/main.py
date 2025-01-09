import random
import jsonlines
import argparse
import configparser
from mus.evaluator import MUSAccuracyEvaluator
from mus.differential import differential_tester, probe_tester
from mus.solution_transformer import transform_code
from evalplus.data import get_human_eval_plus, get_mbpp_plus


def main():
    """
    Entry point for the command-line interface.
    Parses arguments, initializes the evaluator, and runs the pipeline.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of dataset: taco, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path", help="Path to dataset")
    parser.add_argument("-k", "--api-key", dest="api_key", help="OpenAI API key")
    parser.add_argument("-m", "--model", dest="model", help="OpenAI model")
    parser.add_argument("-t", "--temperature", dest="temperature", help="OpenAI temperature")
    parser.add_argument("-n", "--num-programs", dest="num_programs", help="Number of programs to generate")
    parser.add_argument("-i", "--max-iterations", dest="max_iterations", help="Maximum number of iterations")
    parser.add_argument("-o", "--oracle", dest="oracle", help="Test oracle: Code or Probe")

    options = parser.parse_args()

    dataset = options.dataset
    dataset_path = options.dataset_path
    model = options.model
    if options.api_key is not None:
        api_key = options.api_key
    else:
        config = configparser.ConfigParser()
        config.read('.config')
        if "qwen" in model:
            api_key = config['API_KEY']['qwen_key']
        else:
            api_key = config['API_KEY']['openai_key']

    temperature = float(options.temperature)
    num_programs = int(options.num_programs)
    max_iterations = int(options.max_iterations)
    oracle = options.oracle

    mus_accuracy_evaluator = MUSAccuracyEvaluator(
        api_key=api_key,
        differential_tester=differential_tester if oracle.lower() == "code" else probe_tester,
        model=model,
        temperature=temperature
    )

    if dataset.lower() == "taco":
        with jsonlines.open(dataset_path) as reader:
            for i, obj in enumerate(reader):
                requirement = obj['question']
                canonical_solution = transform_code(random.choice(obj['solutions']))
                task_id = i
                if oracle == "code":
                    mus_accuracy_evaluator.mus_code(canonical_solution, requirement, task_id, num_programs,
                                                    max_iterations)
                elif oracle == "probe":
                    mus_accuracy_evaluator.mus_probe(canonical_solution, requirement, task_id, num_programs,
                                                     max_iterations)
    elif dataset.lower() == "humaneval" or dataset.lower() == "mbpp":
        problems = get_human_eval_plus() if dataset.lower() == "humaneval" else get_mbpp_plus()
        for problem in problems:
            task_id = problem['task_id']
            requirement = problem['prompt']
            canonical_solution = problem['canonical_solution']
            if oracle == "code":
                mus_accuracy_evaluator.mus_code(canonical_solution, requirement, task_id, num_programs,
                                                max_iterations)
            elif oracle == "probe":
                mus_accuracy_evaluator.mus_probe(canonical_solution, requirement, task_id, num_programs,
                                                 max_iterations)

    mus_accuracy_evaluator.calculate_accuracy()


if __name__ == "__main__":
    main()
