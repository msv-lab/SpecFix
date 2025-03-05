from specfix.utils import read_jsonl


def count_result(model, dataset):
    results = read_jsonl(f"repair/{model}/{dataset}.jsonl")
    original_results = []
    repaired_results = []
    for result in results:
        original_results.append(result["original_result"])
        repaired_results.append(result["repaired_result"])
    print(
        f"{dataset} original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


def analyze(model, dataset):
    results = read_jsonl(f"repair/{model}/{dataset}.jsonl")
    for result in results:
        if result["original_result"] != result["repaired_result"]:
            print(result["requirement"])
            print(result["repaired_requirement"])
            print(result["original_result"])
            print(result["repaired_result"])
            print(result["ambiguous"])
            print(result["weighted_test_consistency"])
            print()


def count_improvement_ambiguous(model, dataset):
    results = read_jsonl(f"repair/{model}/{dataset}.jsonl")
    origin_result_list = []
    repaired_result_list = []
    for result in results:
        if result["repaired_requirement"] is not None:
            origin_result_list.append(result["original_result"])
            repaired_result_list.append(result["repaired_result"])
    print(
        f"{dataset} original pass@1: {sum(origin_result_list) / len(origin_result_list)}, repaired pass@1: {sum(repaired_result_list) / len(repaired_result_list)}, Improvement: {sum(repaired_result_list) / len(repaired_result_list) - sum(origin_result_list) / len(origin_result_list)}")


# count_result("deepseek-v3", "mbpp_25_woe")
# analyze("deepseek-v3", "mbpp_25_woe")
count_result("deepseek-v3", "mbpp_25_woe")
# count_improvement_ambiguous("deepseek-v3","humaneval_25_woe")
