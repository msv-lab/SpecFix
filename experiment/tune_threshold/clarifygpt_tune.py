import argparse
import math

from specfix.cluster import Clusters
from specfix.utils import read_jsonl, calculate_mcc


def tune_threshold(results, ground_truth):
    threshold_dict = {}
    for threshold in range(0, math.ceil(max(results) * 1000), 1):
        threshold = threshold / 1000
        predicts = [1 if result > threshold else 0 for result in results]
        mcc = calculate_mcc(ground_truth, predicts)
        threshold_dict[threshold] = mcc
    # Find the best threshold
    plot_best_threshold(threshold_dict)
    best_threshold = max(threshold_dict, key=threshold_dict.get)
    return best_threshold


def plot_best_threshold(threshold_dict):
    import matplotlib.pyplot as plt
    plt.plot(threshold_dict.keys(), threshold_dict.values())
    plt.xlabel("Threshold")
    plt.ylabel("MCC")
    plt.show()


def read_ground_truth():
    ground_truth = []
    humaneval = read_jsonl("humaneval_pilot_ground_truth.jsonl")
    # humaneval_woe = read_jsonl("humaneval_woe_pilot_ground_truth.jsonl")
    mbpp = read_jsonl("mbpp_pilot_ground_truth.jsonl")
    # mbpp_woe = read_jsonl("mbpp_woe_pilot_ground_truth.jsonl")
    taco = read_jsonl("taco_lite_pilot_ground_truth.jsonl")
    # taco_woe = read_jsonl("taco_lite_woe_pilot_ground_truth.jsonl")
    # for i, problem in enumerate(humaneval_woe + mbpp_woe + taco_woe):
    # for i, problem in enumerate(humaneval + humaneval_woe + mbpp + mbpp_woe + taco + taco_woe):
    for i, problem in enumerate(humaneval + mbpp + taco):
        ground_truth.append(problem["ground_truth"])
    return ground_truth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", dest="model")

    options = parser.parse_args()
    model_name = options.model

    ground_truths = read_ground_truth()

    cluster_results = []
    humaneval_path = f"ambiguity_detection/{model_name}/humaneval.jsonl"
    mbpp_path = f"ambiguity_detection/{model_name}/mbpp.jsonl"
    taco_path = f"ambiguity_detection/{model_name}/taco.jsonl"
    # humaneval_woe_path = f"ambiguity_detection/{model_name}/humaneval_woe.jsonl"
    # mbpp_woe_path = f"ambiguity_detection/{model_name}/mbpp_woe.jsonl"
    # taco_woe_path = f"ambiguity_detection/{model_name}/taco_woe.jsonl"
    humaneval_problems = read_jsonl(humaneval_path)
    # humaneval_woe_problems = read_jsonl(humaneval_woe_path)
    mbpp_problems = read_jsonl(mbpp_path)
    # mbpp_woe_problems = read_jsonl(mbpp_woe_path)
    taco_problems = read_jsonl(taco_path)
    # taco_woe_problems = read_jsonl(taco_woe_path)
    # all_problems = humaneval_problems + mbpp_problems + taco_problems + humaneval_woe_problems + mbpp_woe_problems + taco_woe_problems
    # all_problems = humaneval_woe_problems + mbpp_woe_problems + taco_woe_problems
    all_problems = humaneval_problems + mbpp_problems + taco_problems
    for i, problem in enumerate(all_problems):
        clusters = Clusters()
        clusters.deserialize(problem["clusters"])
        cluster_results.append(len(clusters.cluster_list))
    best_threshold = tune_threshold(cluster_results, ground_truths)
    print(f"Best threshold for all_datasets: {best_threshold}")


if __name__ == "__main__":
    main()
