import jsonlines

with jsonlines.open("qwen25-coder-14b-instruct/humaneval_70_vanilla_repair.jsonl") as reader:
    humaneval_entropy_diff = []
    for obj in reader:
        if "entropy_diff" in obj:
            humaneval_entropy_diff.append(obj["entropy_diff"])

with jsonlines.open("qwen25-coder-14b-instruct/humaneval_70_woe_vanilla_repair.jsonl") as reader:
    humaneval_woe_entropy_diff = []
    for obj in reader:
        if "entropy_diff" in obj:
            humaneval_woe_entropy_diff.append(obj["entropy_diff"])

with jsonlines.open("qwen25-coder-14b-instruct/mbpp_70_vanilla_repair.jsonl") as reader:
    mbpp_entropy_diff = []
    for obj in reader:
        if "entropy_diff" in obj:
            mbpp_entropy_diff.append(obj["entropy_diff"])

with jsonlines.open("qwen25-coder-14b-instruct/mbpp_70_woe_vanilla_repair.jsonl") as reader:
    mbpp_woe_entropy_diff = []
    for obj in reader:
        if "entropy_diff" in obj:
            mbpp_woe_entropy_diff.append(obj["entropy_diff"])

with jsonlines.open("qwen25-coder-14b-instruct/taco_lite_70_vanilla_repair.jsonl") as reader:
    taco_lite_entropy_diff = []
    for obj in reader:
        if "entropy_diff" in obj:
            taco_lite_entropy_diff.append(obj["entropy_diff"])

with jsonlines.open("qwen25-coder-14b-instruct/taco_lite_70_woe_vanilla_repair.jsonl") as reader:
    taco_lite_woe_entropy_diff = []
    for obj in reader:
        if "entropy_diff" in obj:
            taco_lite_woe_entropy_diff.append(obj["entropy_diff"])

humaneval_repair_ratio = len(humaneval_entropy_diff) / 50
humaneval_woe_repair_ratio = len(humaneval_woe_entropy_diff) / 50

mbpp_repair_ratio = len(mbpp_entropy_diff) / 50
mbpp_woe_repair_ratio = len(mbpp_woe_entropy_diff) / 50

taco_lite_repair_ratio = len(taco_lite_entropy_diff) / 50
taco_lite_woe_repair_ratio = len(taco_lite_woe_entropy_diff) / 50

print(f"HumanEval: {humaneval_repair_ratio} {sum(humaneval_entropy_diff) / len(humaneval_entropy_diff)}")
print(
    f"HumanEval WOE: {humaneval_woe_repair_ratio} {sum(humaneval_woe_entropy_diff) / len(humaneval_woe_entropy_diff)}")

print(f"MBPP: {mbpp_repair_ratio} {sum(mbpp_entropy_diff) / len(mbpp_entropy_diff)}")
print(f"MBPP WOE: {mbpp_woe_repair_ratio} {sum(mbpp_woe_entropy_diff) / len(mbpp_woe_entropy_diff)}")

print(f"TACO Lite: {taco_lite_repair_ratio} {sum(taco_lite_entropy_diff) / len(taco_lite_entropy_diff)}")
print(
    f"TACO Lite WOE: {taco_lite_woe_repair_ratio} {sum(taco_lite_woe_entropy_diff) / len(taco_lite_woe_entropy_diff)}")
