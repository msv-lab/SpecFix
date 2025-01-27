import jsonlines


def get_align(clusters):
    result = []
    for cluster in clusters["clusters"]:
        if cluster["is_align_req"]:
            result.append(1)
        else:
            result.append(0)
    return result


def avg_align_at_least_1(clusters):
    return sum([1 if any(cluster) else 0 for cluster in clusters]) / len(clusters)


with jsonlines.open("qwen25-coder-14b-instruct/humaneval_70_vanilla_repair.jsonl") as reader:
    humaneval_original_alignment = []
    humaneval_repair_alignment = []
    for obj in reader:
        humaneval_original_alignment.append(get_align(obj["original_clusters"]))
        if "repaired_clusters" in obj:
            humaneval_repair_alignment.append(get_align(obj["original_clusters"]))

with jsonlines.open("qwen25-coder-14b-instruct/humaneval_70_woe_vanilla_repair.jsonl") as reader:
    humaneval_woe_original_alignment = []
    humaneval_woe_repair_alignment = []
    for obj in reader:
        humaneval_woe_original_alignment.append(get_align(obj["original_clusters"]))
        if "repaired_clusters" in obj:
            humaneval_woe_repair_alignment.append(get_align(obj["original_clusters"]))

with jsonlines.open("qwen25-coder-14b-instruct/mbpp_70_vanilla_repair.jsonl") as reader:
    mbpp_original_alignment = []
    mbpp_repair_alignment = []
    for obj in reader:
        mbpp_original_alignment.append(get_align(obj["original_clusters"]))
        if "repaired_clusters" in obj:
            mbpp_repair_alignment.append(get_align(obj["original_clusters"]))

with jsonlines.open("qwen25-coder-14b-instruct/mbpp_70_woe_vanilla_repair.jsonl") as reader:
    mbpp_woe_original_alignment = []
    mbpp_woe_repair_alignment = []
    for obj in reader:
        mbpp_woe_original_alignment.append(get_align(obj["original_clusters"]))
        if "repaired_clusters" in obj:
            mbpp_woe_repair_alignment.append(get_align(obj["original_clusters"]))

with jsonlines.open("qwen25-coder-14b-instruct/taco_lite_70_vanilla_repair.jsonl") as reader:
    taco_lite_original_alignment = []
    taco_lite_repair_alignment = []
    for obj in reader:
        taco_lite_original_alignment.append(get_align(obj["original_clusters"]))
        if "repaired_clusters" in obj:
            taco_lite_repair_alignment.append(get_align(obj["original_clusters"]))

with jsonlines.open("qwen25-coder-14b-instruct/taco_lite_70_woe_vanilla_repair.jsonl") as reader:
    taco_lite_woe_original_alignment = []
    taco_lite_woe_repair_alignment = []
    for obj in reader:
        taco_lite_woe_original_alignment.append(get_align(obj["original_clusters"]))
        if "repaired_clusters" in obj:
            taco_lite_woe_repair_alignment.append(get_align(obj["original_clusters"]))

print("Humaneval original alignment:", avg_align_at_least_1(humaneval_original_alignment))
print("Humaneval repair alignment:", avg_align_at_least_1(humaneval_repair_alignment))
print("Humaneval woe original alignment:", avg_align_at_least_1(humaneval_woe_original_alignment))
print("Humaneval woe repair alignment:", avg_align_at_least_1(humaneval_woe_repair_alignment))
print("MBPP original alignment:", avg_align_at_least_1(mbpp_original_alignment))
print("MBPP repair alignment:", avg_align_at_least_1(mbpp_repair_alignment))
print("MBPP woe original alignment:", avg_align_at_least_1(mbpp_woe_original_alignment))
print("MBPP woe repair alignment:", avg_align_at_least_1(mbpp_woe_repair_alignment))
print("Taco Lite original alignment:", avg_align_at_least_1(taco_lite_original_alignment))
print("Taco Lite repair alignment:", avg_align_at_least_1(taco_lite_repair_alignment))
print("Taco Lite woe original alignment:", avg_align_at_least_1(taco_lite_woe_original_alignment))
print("Taco Lite woe repair alignment:", avg_align_at_least_1(taco_lite_woe_repair_alignment))
