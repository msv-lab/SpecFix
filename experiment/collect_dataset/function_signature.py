import jsonlines
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

from specfix.model import Model
from specfix.utils import unwrap


def extract_type_imports(func):
    imports = []
    if "List" in func:
        imports.append("from typing import List")
    if "Dict" in func:
        imports.append("from typing import Dict")
    if "Set" in func:
        imports.append("from typing import Set")
    if "Tuple" in func:
        imports.append("from typing import Tuple")
    if "Union" in func:
        imports.append("from typing import Union")
    return "\n".join(imports)


model = Model("gpt-4o")

instruction_function_signature = "You are an AI assistant that extract function signature from a python canonical solution."


def prompt_function_signature(requirement, solution, entry_point):
    prompt = (
            f"Your task is to extract the function signature from programming problem requirement and the corresponding canonical solution. The function name in signature is {entry_point}.\n"
            + "First, judge the parameter types and return type of the function. Then extract the function signature.\n"
            + "The function signature should include the function name, parameters, and return type."
            + "Don't change the function name and parameter name. Do not include any other content such as the function body or any other code."
            + "Here is an function signature example: "
            + "def find_n_largest_numbers(arr: List[int], n: int) -> int:\n"
            + "Wrap the extracted function signature in <signature></signature> tags. Don't output any explanation.\n"
            + "Here is the problem requirement:\n"
            + requirement
            + "\nHere is the corresponding canonical solution:\n"
            + solution
    )
    return prompt


with jsonlines.open("mbpp.jsonl") as reader, jsonlines.open("mbpp_woe.jsonl") as reader1:
    tasks = list(zip(reader, reader1))


def process_task(task):
    problem, problem1 = task
    requirement = problem1["requirement"]
    solution = problem["canonical_solution"]
    problem["entry_point"] = problem["entry_point"].strip()
    entry_point = problem["entry_point"]

    if len(solution) > 100000:
        print(problem["task_id"])
        return problem, problem1

    response = model.get_response(instruction_function_signature,
                                  prompt_function_signature(requirement, solution, entry_point,
                                                            ))
    signature = unwrap(response, "signature")
    imports = extract_type_imports(signature + "\n\tpass")
    starter_code = signature
    original_import_lines = []
    original_starter_code = ""
    for line in problem["requirement"].split("\n"):
        if line.startswith("import ") or line.startswith("from "):
            original_import_lines.append(line)
        if f"def {problem["entry_point"]}" in line:
            original_starter_code = line
            break
    original_imports = "\n".join(original_import_lines)
    # original_starter_code = problem["starter_code"]

    if original_starter_code != "":
        problem["requirement"] = problem["requirement"].replace(original_starter_code, starter_code).strip()
        problem1["requirement"] = problem1["requirement"].replace(original_starter_code, starter_code).strip()
    else:
        if "\"\"\"" in problem["requirement"]:
            problem["requirement"] = starter_code + "\n" + problem["requirement"]
            problem1["requirement"] = starter_code + "\n" + problem1["requirement"]
        else:
            problem["requirement"] = starter_code + "\n\"\"\"\n" + problem["requirement"] + "\n\"\"\""
            problem1["requirement"] = starter_code + "\n\"\"\"\n" + problem1["requirement"] + "\n\"\"\""
    if original_imports != "":
        problem["requirement"] = problem["requirement"].replace(original_imports, imports)
        problem1["requirement"] = problem1["requirement"].replace(original_imports, imports)
    else:
        problem["requirement"] = imports + "\n" + problem["requirement"]
        problem1["requirement"] = imports + "\n" + problem1["requirement"]
    problem["starter_code"] = (imports + "\n" + starter_code).strip()
    problem1["starter_code"] = (imports + "\n" + starter_code).strip()

    return problem, problem1


with ThreadPoolExecutor() as executor, \
        jsonlines.open("mbpp1.jsonl", "w", flush=True) as writer, \
        jsonlines.open("mbpp_woe1.jsonl", "w", flush=True) as writer1:
    futures = [executor.submit(process_task, task) for task in tasks]

    for future in tqdm(futures, total=len(tasks), desc="Processing"):
        problem_result, problem1_result = future.result()
        writer.write(problem_result)
        writer1.write(problem1_result)
#
# with jsonlines.open("mbpp1.jsonl", "w") as writer, jsonlines.open("mbpp_woe1.jsonl", "w") as writer1:
#     for task in tasks:
#         if task[0]["task_id"] != "Mbpp/75":
#             continue
#         problem_result, problem1_result = process_task(task)
#         writer.write(problem_result)
#         writer1.write(problem1_result)
