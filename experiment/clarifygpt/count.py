from specfix.utils import read_jsonl


def check_original_passk(results, ground_truths):
    for result, ground_truth in zip(results, ground_truths):
        if result["original_passk"] != ground_truth["original_passk"]:
            print(result["original_passk"], ground_truth["original_passk"])
            return False
    return True


def count(data):
    results = read_jsonl(data)
    original_results = []
    repaired_results = []
    ambiguous_original_results = []
    ambiguous_repaired_results = []
    for result in results:
        original_results.append(result["original_passk"])
        repaired_results.append(result["repaired_passk"])
        if result["repaired_requirement"] is not None:
            ambiguous_original_results.append(result["original_passk"])
            ambiguous_repaired_results.append(result["repaired_passk"])
    print(
        f"original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")
    print(
        f"original pass@1: {sum(ambiguous_original_results) / len(ambiguous_original_results)}, repaired pass@1: {sum(ambiguous_repaired_results) / len(ambiguous_repaired_results)}, Improvement: {sum(ambiguous_repaired_results) / len(ambiguous_repaired_results) - sum(ambiguous_original_results) / len(ambiguous_original_results)}")


# gts = read_jsonl("../test_based_repair/original_passk/qwen2.5-coder-32b-instruct/humaneval_woe.jsonl")

# check_original_passk(problems, gts)
count("deepseek-v3_mbpp_clarifygpt.jsonl")
# count("deepseek-v3_humaneval_clarifygpt.jsonl")
