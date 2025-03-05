import ast
import random

import jsonlines
from concurrent.futures import ThreadPoolExecutor
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.model import Model
from specfix.prompting import instruction_generate_test, prompt_generate_test
from specfix.utils import read_jsonl, unwrap

model_name = "deepseek-v3"
# 配置项
FILE_PAIRS = [
    ("humaneval.jsonl", "humaneval_llm_generated_inputs.jsonl"),
    ("humaneval_woe.jsonl", "humaneval_woe_llm_generated_inputs.jsonl"),
    ("mbpp.jsonl", "mbpp_llm_generated_inputs.jsonl"),
    ("mbpp_woe.jsonl", "mbpp_woe_llm_generated_inputs.jsonl"),
    ("taco_lite_selected.jsonl", "taco_lite_llm_generated_inputs.jsonl"),
    ("taco_lite_woe_selected.jsonl", "taco_lite_woe_llm_generated_inputs.jsonl"),
]


def process_file_pair(input_file, output_file):
    problems = read_jsonl(input_file)

    def process_problem(problem):
        problem["llm_generated_inputs"] = str(specfix_accuracy_evaluator.generate_tests(
            problem["requirement"],
            problem["entry_point"]
        ))
        return problem

    with ThreadPoolExecutor(max_workers=10) as executor:
        processed_problems = list(executor.map(process_problem, problems))

    with jsonlines.open(model_name + "_" + output_file, mode='w') as writer:
        writer.write_all(processed_problems)


def fill_blank(file):
    problems = read_jsonl(model_name + "_" + file)
    with jsonlines.open((model_name + "_" + file).replace(".jsonl", "_fill.jsonl"), "w") as writer:
        for problem in problems:
            print(problem["task_id"])
            if not ast.literal_eval(problem["llm_generated_inputs"]):
                problem["llm_generated_inputs"] = str(
                    specfix_accuracy_evaluator.generate_tests(problem["requirement"], problem["entry_point"]))
        writer.write_all(problems)


def select():
    random.seed(25)
    d_problems = read_jsonl("deepseek-v3_taco_lite_llm_generated_inputs.jsonl")[50:]
    q_problems = read_jsonl("qwen2.5-coder-32b-instruct_taco_lite_llm_generated_inputs.jsonl")[50:]
    d_woe_problems = read_jsonl("deepseek-v3_taco_lite_woe_llm_generated_inputs.jsonl")[50:]
    q_woe_problems = read_jsonl("qwen2.5-coder-32b-instruct_taco_lite_woe_llm_generated_inputs.jsonl")[50:]
    problems = []
    for d, q, d_woe, q_woe in zip(d_problems, q_problems, d_woe_problems, q_woe_problems):
        if d["llm_generated_inputs"] != "[]" and q["llm_generated_inputs"] != "[]" and d_woe[
            "llm_generated_inputs"] != "[]" and q_woe["llm_generated_inputs"] != "[]":
            problems.append(d)
    selected_problems = random.sample(problems, 400)
    # sort by task_id
    selected_problems = sorted(selected_problems, key=lambda x: int(x["task_id"].split("/")[-1]))
    with jsonlines.open("deepseek-v3_taco_lite_llm_generated_inputs_selected.jsonl", "w") as writer:
        writer.write_all(selected_problems)
    with jsonlines.open("deepseek-v3_taco_lite_woe_llm_generated_inputs_selected.jsonl", "w") as writer:
        for p in selected_problems:
            for d_woe in d_woe_problems:
                if d_woe["task_id"] == p["task_id"]:
                    writer.write(d_woe)
                    break
    with jsonlines.open("qwen2.5-coder-32b-instruct_taco_lite_llm_generated_inputs_selected.jsonl", "w") as writer:
        for p in selected_problems:
            for q in q_problems:
                if q["task_id"] == p["task_id"]:
                    writer.write(q)
                    break
    with jsonlines.open("qwen2.5-coder-32b-instruct_taco_lite_woe_llm_generated_inputs_selected.jsonl", "w") as writer:
        for p in selected_problems:
            for q_woe in q_woe_problems:
                if q_woe["task_id"] == p["task_id"]:
                    writer.write(q_woe)
                    break


def get_pilot_data(path):
    problems = read_jsonl(path)
    with jsonlines.open(path.replace(".jsonl", "_pilot.jsonl"), "w") as writer:
        writer.write_all(problems[:50])


if __name__ == "__main__":
    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(model=model_name)

    for input_file, output_file in FILE_PAIRS:
        print("GENERATE TEST ATTEMPT", input_file)
        # process_file_pair(input_file, output_file)
        # fill_blank(output_file)
        get_pilot_data(model_name + "_" + input_file)
