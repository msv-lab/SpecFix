from specfix.utils import read_jsonl, count_passk, count_passk_ambiguous, count_ambiguity


def analyze(model, dataset):
    results = read_jsonl(f"test_based_repair/{model}/{dataset}.jsonl")
    for result in results:
        if result["original_result"] == True and result["repaired_result"] == False:
            print(result["requirement"])
            print(result["repaired_requirement"])
            print(result["original_result"])
            print(result["repaired_result"])
            print(result["original_clusters"]["entropy"])
            print(result["original_clusters"]["weighted_test_consistency"])
            print(result["repaired_failed_inputs_outputs"])
            print()




# count_result("deepseek-v3", "mbpp_25_woe")
analyze("deepseek-v3", "taco_lite_0.125")
# count_passk("test_based_repair","qwen2.5-coder-32b-instruct", "taco_lite_0.306")
# count_passk_ambiguous("test_based_repair","qwen2.5-coder-32b-instruct", "taco_lite_0.306")
# count_ambiguity("test_based_repair","qwen2.5-coder-32b-instruct", "taco_lite_0.306")
# count_passk("test_based_repair","deepseek-v3", "taco_lite_0.125")
# count_passk_ambiguous("test_based_repair","deepseek-v3", "taco_lite_0.125")
# count_ambiguity("test_based_repair","deepseek-v3", "taco_lite_0.125")