from specfix.utils import read_jsonl, count_passk, count_passk_ambiguous, count_ambiguity


def analyze(model, dataset):
    results = read_jsonl(f"clarify_gpt_zero_shot/{model}/{dataset}.jsonl")
    for result in results:
        if result["original_result"] == True and result["repaired_result"] == False:
            print(result["requirement"])
            print(result["repaired_requirement"])
            print(result["original_result"])
            print(result["repaired_result"])
            print(result["original_clusters"]["entropy"])
            print(result["original_clusters"]["weighted_test_consistency"])
            print(result["repaired_clusters"]["weighted_test_consistency"])
            print(result["repaired_failed_inputs_outputs"])
            print()
            
            
            
# analyze("deepseek-v3", "humaneval_0")
# count_passk("clarify_gpt_zero_shot","qwen2.5-coder-32b-instruct", "taco_lite_woe_0")
count_passk_ambiguous("clarify_gpt_zero_shot","deepseek-v3", "taco_lite_0")
count_passk("clarify_gpt_zero_shot","deepseek-v3", "taco_lite_0")