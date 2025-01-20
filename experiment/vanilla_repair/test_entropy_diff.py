import jsonlines
import matplotlib.pyplot as plt

# Read HumanEval data
with jsonlines.open("qwen25-coder-14b-instruct/humaneval_70_vanilla_repair.jsonl") as reader, \
     jsonlines.open("qwen25-coder-14b-instruct/humaneval_70_woe_vanilla_repair.jsonl") as reader2:

    humaneval_original_entropy_diff = []
    humaneval_entropy = []
    humaneval_woe_entropy = []

    for obj, obj2 in zip(reader, reader2):
        humaneval_entropy.append(obj["original_clusters"]["entropy"])
        humaneval_woe_entropy.append(obj2["original_clusters"]["entropy"])
        humaneval_original_entropy_diff.append(
            obj["original_clusters"]["entropy"] - obj2["original_clusters"]["entropy"]
        )

# Read MBPP data
with jsonlines.open("qwen25-coder-14b-instruct/mbpp_70_vanilla_repair.jsonl") as reader, \
     jsonlines.open("qwen25-coder-14b-instruct/mbpp_70_woe_vanilla_repair.jsonl") as reader2:

    mbpp_original_entropy_diff = []
    mbpp_entropy = []
    mbpp_woe_entropy = []

    for obj, obj2 in zip(reader, reader2):
        mbpp_entropy.append(obj["original_clusters"]["entropy"])
        mbpp_woe_entropy.append(obj2["original_clusters"]["entropy"])
        mbpp_original_entropy_diff.append(
            obj["original_clusters"]["entropy"] - obj2["original_clusters"]["entropy"]
        )

# Read TACO Lite data
with jsonlines.open("qwen25-coder-14b-instruct/taco_lite_70_vanilla_repair.jsonl") as reader, \
     jsonlines.open("qwen25-coder-14b-instruct/taco_lite_70_woe_vanilla_repair.jsonl") as reader2:

    taco_lite_original_entropy_diff = []
    taco_lite_entropy = []
    taco_lite_woe_entropy = []

    for obj, obj2 in zip(reader, reader2):
        taco_lite_entropy.append(obj["original_clusters"]["entropy"])
        taco_lite_woe_entropy.append(obj2["original_clusters"]["entropy"])
        taco_lite_original_entropy_diff.append(
            obj["original_clusters"]["entropy"] - obj2["original_clusters"]["entropy"]
        )

# Plotting
fig, axes = plt.subplots(3, 2, figsize=(10, 10))

# HumanEval
axes[0][0].hist(humaneval_original_entropy_diff, bins=20, color='blue', alpha=0.7)
axes[0][0].set_title('HumanEval: Original - WOE Entropy')
axes[0][0].set_xlabel('Difference')
axes[0][0].set_ylabel('Frequency')

axes[0][1].boxplot([humaneval_entropy, humaneval_woe_entropy], labels=['Original', 'WOE'])
axes[0][1].set_title('HumanEval Entropies')

# MBPP
axes[1][0].hist(mbpp_original_entropy_diff, bins=20, color='orange', alpha=0.7)
axes[1][0].set_title('MBPP: Original - WOE Entropy')
axes[1][0].set_xlabel('Difference')
axes[1][0].set_ylabel('Frequency')

axes[1][1].boxplot([mbpp_entropy, mbpp_woe_entropy], labels=['Original', 'WOE'])
axes[1][1].set_title('MBPP Entropies')

# TACO Lite
axes[2][0].hist(taco_lite_original_entropy_diff, bins=20, color='green', alpha=0.7)
axes[2][0].set_title('TACO Lite: Original - WOE Entropy')
axes[2][0].set_xlabel('Difference')
axes[2][0].set_ylabel('Frequency')

axes[2][1].boxplot([taco_lite_entropy, taco_lite_woe_entropy], labels=['Original', 'WOE'])
axes[2][1].set_title('TACO Lite Entropies')

plt.tight_layout()
plt.show()
