import jsonlines

from specfix.utils import calculate_mcc


def count_mcc(path):
    with jsonlines.open("../user_study/human_feedback/ground_truth.jsonl") as ground_truth, jsonlines.open(
            path) as predictions:
        predict_requirement = []
        predict_requirement_woe = []
        ground_truth_requirement = []
        ground_truth_requirement_woe = []
        for prediction, truth in zip(predictions, ground_truth):
            predict_requirement.append("Ambiguous" if prediction["answer"] == "Yes" else "Unambiguous")
            predict_requirement_woe.append(
                "Ambiguous" if prediction["answer_without_examples"] == "Yes" else "Unambiguous")
            ground_truth_requirement.append(truth["answer"])
            ground_truth_requirement_woe.append(truth["answer_without_examples"])
        mcc = calculate_mcc(ground_truth_requirement, predict_requirement)
        mcc_woe = calculate_mcc(ground_truth_requirement_woe, predict_requirement_woe)
        print(f"MCC: {mcc}, MCC_woe: {mcc_woe}")


count_mcc("vanilla_detect/qwen2.5-coder-32b-instruct/user_study.jsonl")
count_mcc("vanilla_detect/deepseek-v3/user_study.jsonl")
count_mcc("specifx_detect/deepseek-v3/user_study_0.125.jsonl")
count_mcc("specifx_detect/qwen2.5-coder-32b-instruct/user_study_0.306.jsonl")
