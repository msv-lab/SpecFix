import argparse
import configparser
import jsonlines
from mus.evaluator import MUSAccuracyEvaluator
from evalplus.data import get_human_eval_plus, get_mbpp_plus


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

    mus_accuracy_evaluator = MUSAccuracyEvaluator(
        api_key=api_key,
        model=model_name,
        temperature=0
    )

    dataset = options.dataset
    dataset_path = options.dataset_path

    if dataset == "taco_lite":
        with jsonlines.open(dataset_path) as reader:
            for problem in reader:
                requirement = problem['requirement']
                print(mus_accuracy_evaluator.generate_facts(requirement))
    elif dataset == "humaneval":
        humaneval_problem = get_human_eval_plus()
        for problem in humaneval_problem:
            requirement = humaneval_problem[problem]["requirement"]
            print(mus_accuracy_evaluator.generate_facts(requirement))
    elif dataset == "mbpp":
        mbpp_problem = get_mbpp_plus()
        for problem in mbpp_problem:
            requirement = mbpp_problem[problem]["requirement"]
            print(mus_accuracy_evaluator.generate_facts(requirement))


if __name__ == "__main__":
    main()
