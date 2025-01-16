import random
import jsonlines
import argparse
import configparser

from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.differential import differential_tester
from specfix.solution_transformer import transform_code
from specfix.utils import construct_requirement
from evalplus.data import get_human_eval_plus, get_mbpp_plus


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of dataset: taco_lite, humaneval, mbpp")
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

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        api_key=api_key,
        differential_tester=differential_tester,
        model=model,
        temperature=temperature
    )

    if dataset.lower() == "taco_lite":
        with jsonlines.open(dataset_path) as reader:
            for i, obj in enumerate(reader):
                starter_code = obj['starter_code']
                entry_point = obj['entry_point']
                requirement = obj['requirement']
                requirement = construct_requirement(requirement, starter_code)
                canonical_solution = transform_code(random.choice(obj['solutions']))
                task_id = i
                if oracle == "code":
                    unambiguous_requirement = specfix_accuracy_evaluator.specfix_code(canonical_solution, requirement,
                                                                                  entry_point, task_id,
                                                                                  num_programs,
                                                                                  max_iterations)
                print("***************Case", i, "***************")
                print("The original requirement:\n", requirement)
                print("The unambiguous requirement:\n", unambiguous_requirement)
    elif dataset.lower() == "humaneval" or dataset.lower() == "mbpp":
        problems = get_human_eval_plus() if dataset.lower() == "humaneval" else get_mbpp_plus()
        for problem in problems:
            task_id = problem['task_id']
            requirement = problem['requirement']
            canonical_solution = problem['canonical_solution']
            entry_point = problem['entry_point']
            if oracle == "code":
                unambiguous_requirement = specfix_accuracy_evaluator.specfix_code(canonical_solution, requirement, entry_point,
                                                                              task_id,
                                                                              num_programs,
                                                                              max_iterations)

    specfix_accuracy_evaluator.calculate_accuracy()


if __name__ == "__main__":
    main()
