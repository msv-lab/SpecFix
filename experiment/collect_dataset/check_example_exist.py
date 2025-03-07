from asyncio import as_completed
from concurrent.futures import ThreadPoolExecutor

import jsonlines

from specfix.model import Model
from specfix.utils import unwrap

model = Model("qwen-plus")

instruction_check_example = "You are an assistant that checks whether there exists any example in the requirement."


def prompt_check_example(requirement):
    return f"""
    Please check whether there exists any example, including sample inputs/outputs, in-text illustrations (e.g., 'for example, if...'), or standalone example sections in the requirement. Think step by step. If there is, please return 1; otherwise, return 0.
    Wrap the judgment in <check></check> tags. Wrap your step-by-step reasoning in <reasoning></reasoning> tags.
    
    # Requirement
    {requirement}
    """


def process_problem(problem):
    print("Case ", problem["task_id"])
    response = model.get_response(instruction_check_example, prompt_check_example(problem["requirement"]))
    judgment = unwrap(response, "check")
    reasoning = unwrap(response, "reasoning")
    if int(judgment) == 0 and problem["input_output_examples"] != "[[], []]":
        print(problem["requirement"])
        print(reasoning)
        problem["input_output_examples"] = "[[], []]"
    elif int(judgment) == 1 and problem["input_output_examples"] == "[[], []]":
        print(problem["requirement"])
        print(reasoning)
        problem["input_output_examples"] = "[[], []]"
    return problem


# with jsonlines.open('humaneval.jsonl') as reader:
#     problems = list(reader)
#     with ThreadPoolExecutor(max_workers=50) as executor:
#         futures = {executor.submit(process_problem, problem): problem for problem in problems}

# with jsonlines.open('mbpp.jsonl') as reader:
#     problems = list(reader)
#     with ThreadPoolExecutor(max_workers=50) as executor:
#         futures = {executor.submit(process_problem, problem): problem for problem in problems}

with jsonlines.open('taco_lite.jsonl') as reader:
    problems = list(reader)
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(process_problem, problem): problem for problem in problems}
