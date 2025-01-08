# mus_eval/main.py

import random
import jsonlines
import argparse

from .evaluator import MUSAccuracyEvaluator
from .differential import differential_tester
from .solution_transformer import transform_code
from evalplus.data import get_human_eval_plus, get_mbpp_plus


def main():
    """
    Entry point for the command-line interface.
    Parses arguments, initializes the evaluator, and runs the pipeline.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of dataset")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path", help="Path to dataset")
    parser.add_argument("-k", "--api-key", dest="api_key", help="OpenAI API key")
    parser.add_argument("-m", "--model", dest="model", help="OpenAI model")
    parser.add_argument("-t", "--temperature", dest="temperature", help="OpenAI temperature")
    parser.add_argument("-n", "--num-programs", dest="num_programs", help="Number of programs to generate")
    parser.add_argument("-i", "--max-iterations", dest="max_iterations", help="Maximum number of iterations")

    (options, args) = parser.parse_args()

    dataset = options.dataset
    dataset_path = options.dataset_path
    api_key = options.api_key
    model = options.model
    temperature = float(options.temperature)
    num_programs = int(options.num_programs)
    max_iterations = int(options.max_iterations)

    mus_accuracy_evaluator = MUSAccuracyEvaluator(
        api_key=api_key,
        differential_tester=differential_tester,
        model=model,
        temperature=temperature
    )

    if dataset.lower() == "taco":
        with jsonlines.open(dataset_path) as reader:
            for i, obj in enumerate(reader):
                requirement = obj['question']
                program = transform_code(random.choice(obj['solutions']))
                mus_accuracy_evaluator.mus_requirement_execute(program, requirement, i + 1, num_programs,
                                                               max_iterations)
    elif dataset.lower() == "humaneval":
        humaneval_problem = get_human_eval_plus()
        for problem in humaneval_problem:
            task_id = problem['task_id']
            prompt = problem['prompt']
            canonical_solution = problem['canonical_solution']
            mus_accuracy_evaluator.mus_code(canonical_solution, prompt, task_id, num_programs, max_iterations)
    elif dataset.lower() == "mbpp":
        mbpp = get_mbpp_plus()
        for problem in mbpp:
            task_id = problem['task_id']
            prompt = problem['prompt']
            canonical_solution = problem['canonical_solution']
            mus_accuracy_evaluator.mus_code(canonical_solution, prompt, task_id, num_programs, max_iterations)

    mus_accuracy_evaluator.calculate_accuracy()


if __name__ == "__main__":
    main()
