import configparser

import jsonlines

from specfix.evaluator import SpecFixAccuracyEvaluator

config = configparser.ConfigParser()
config.read('../../.config')
model_name = "o1-mini"
api_key = ""
if "qwen" in model_name:
    api_key = config['API_KEY']['qwen_key']
elif "gpt3" in model_name or "o1" in model_name:
    api_key = config['API_KEY']['openai_key']

specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
    api_key=api_key,
    model=model_name,
    temperature=1
)

with jsonlines.open("qwen25-coder-14b-instruct/taco_lite_70_vanilla_repair.jsonl") as reader:
    for obj in reader:
        if "entropy_diff" in obj and obj["entropy_diff"] > 0.5 and any(cluster["is_align_req"] for cluster in obj["repaired_clusters"]["clusters"]):
            print(obj["original_requirement"])
            print(obj["repaired_requirement"])
            print(obj["entropy_diff"])
            instruction = "You are AI-assistant to analyze the differences between the two requirements."
            prompt = f"Here is an ambiguous requirement: {obj["original_requirement"]}. And here is the corresponding repaired requirement: {obj["repaired_requirement"]}, which removes ambiguity. Please analyze the differences between the two requirements and provide reason why the repaired requirement removes the ambiguity."
            response = specfix_accuracy_evaluator.model.get_response(instruction, prompt)
            print(response)
