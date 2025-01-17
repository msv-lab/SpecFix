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
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

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
    woe = "_woe" if options.without_example else ""

    if dataset == "taco_lite":
        with jsonlines.open(dataset_path) as reader, jsonlines.open(f"{dataset}{woe}_pilot_classification.jsonl",
                                                                    mode='w',
                                                                    flush=True) as writer:
            for problem in reader:
                result = {}
                requirement = problem['requirement']
                answer, reasoning = specfix_accuracy_evaluator.classification(requirement)
                result['requirement'] = requirement
                result['label'] = answer
                result['reasoning'] = reasoning
                print(result)
                writer.write(result)
    elif dataset == "humaneval" or dataset == "mbpp":
        with jsonlines.open(dataset_path) as reader, jsonlines.open(f"{dataset}{woe}_pilot_classification.jsonl",
                                                                    mode='w',
                                                                    flush=True) as writer:
            for problem in reader:
                result = {}
                requirement = problem['requirement']
                answer, reasoning = specfix_accuracy_evaluator.classification(requirement)
                result['requirement'] = requirement
                result['label'] = answer
                result['reasoning'] = reasoning
                print(result)
                writer.write(result)


if __name__ == "__main__":
    main()
