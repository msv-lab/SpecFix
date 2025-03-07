import jsonlines

from specfix.utils import read_jsonl

humaneval = read_jsonl("../../dataset/humaneval.jsonl")
mbpp = read_jsonl("../../dataset/mbpp.jsonl")
taco_deepseek = read_jsonl("../llm_generated_inputs/deepseek-v3_taco_lite_full.jsonl")
taco_qwen = read_jsonl("../llm_generated_inputs/qwen2.5-coder-32b-instruct_taco_lite_full.jsonl")
with jsonlines.open('user_study.jsonl') as reader, jsonlines.open("user_study1.jsonl", "w", flush=True) as writer:
    for obj in reader:
        if "humaneval" in obj["task_id"].lower():
            for problem in humaneval:
                if problem["task_id"] == obj["task_id"]:
                    obj["llm_generated_inputs"] = problem["llm_generated_inputs"]
                    break
        elif "mbpp" in obj["task_id"].lower():
            for problem in mbpp:
                if problem["task_id"] == obj["task_id"]:
                    obj["llm_generated_inputs"] = problem["llm_generated_inputs"]
                    break
        else:
            obj["llm_generated_inputs"] = {}
            for problem in taco_deepseek:
                if problem["task_id"] == obj["task_id"]:
                    obj["llm_generated_inputs"]["deepseek-v3"] = problem["llm_generated_inputs"]
                    break
            for problem in taco_qwen:
                if problem["task_id"] == obj["task_id"]:
                    obj["llm_generated_inputs"]["qwen2.5-coder-32b-instruct"] = problem["llm_generated_inputs"]
                    break
        writer.write(obj)
