import argparse
import jsonlines
import configparser
from specfix.evaluator import SpecFixAccuracyEvaluator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")

    options = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../../.config')

    model_name = "gpt-4o"
    api_key = config['API_KEY']['openai_key']

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        api_key=api_key,
        model=model_name,
        temperature=0
    )

    dataset = options.dataset
    dataset_path = options.dataset_path

    if dataset == "taco_lite":
        with jsonlines.open(dataset_path) as reader, jsonlines.open(f"{dataset}_classification.jsonl", mode='w',
                                                                    flush=True) as writer:
            for problem in reader:
                result = {}
                requirement = problem['question']
                answer, reasoning = specfix_accuracy_evaluator.classification(requirement)
                result['question'] = requirement
                result['label'] = answer
                result['reasoning'] = reasoning
                print(result)
                writer.write(result)
    elif dataset == "humaneval" or dataset == "mbpp":
        with jsonlines.open(dataset_path) as reader, jsonlines.open(f"{dataset}_classification.jsonl", mode='w',
                                                                    flush=True) as writer:
            for problem in reader:
                result = {}
                requirement = problem['prompt']
                answer, reasoning = specfix_accuracy_evaluator.classification(requirement)
                result['question'] = requirement
                result['label'] = answer
                result['reasoning'] = reasoning
                print(result)
                writer.write(result)


if __name__ == "__main__":
    main()
