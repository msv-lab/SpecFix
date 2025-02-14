import os
import subprocess
import sys
import types
import random
import math
import re
import jsonlines
from func_timeout import func_timeout, FunctionTimedOut
from tqdm import trange
from sklearn.metrics import matthews_corrcoef

from specfix.solution_transformer import remove_comments_and_asserts, transform_code


def post_process(text: str) -> str:
    python_pattern = re.compile(r'```python\s*(.*?)\s*```', re.DOTALL)
    match = python_pattern.search(text)
    if match:
        return match.group(1)

    general_pattern = re.compile(r'```(.*?)```', re.DOTALL)
    match = general_pattern.search(text)
    if match:
        return match.group(1)
    return text.strip()


def execute(func_str, func_args, entry_point):
    max_install_attempts = 3
    installed_modules = set()

    while True:
        try:
            local_env = {}
            exec(func_str, local_env)

            if entry_point in local_env:
                func = local_env[entry_point]
            else:
                target_funcs = [f for f in local_env.values() if isinstance(f, types.FunctionType)]
                if len(target_funcs) == 1:
                    func = target_funcs[0]
                else:
                    func = random.choice(target_funcs)

            return func(*func_args)

        except ModuleNotFoundError as e:
            module_name = e.name
            if module_name in installed_modules:
                return "ModuleNotFoundError"
            if len(installed_modules) >= max_install_attempts:
                return "ModuleNotFoundError"

            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module_name], stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)
                installed_modules.add(module_name)
                continue
            except subprocess.CalledProcessError:
                return "ModuleNotFoundError"

        except Exception as e:
            return e.__class__.__name__


def execute_inputs(func_str, inputs_list, entry_point, timeout=1):
    results = []
    for i in trange(len(inputs_list)):
        try:
            # results.append([execute(func_str, inputs_list[i], entry_point)])
            results.append([func_timeout(timeout, execute, args=(func_str, inputs_list[i], entry_point))])
        except FunctionTimedOut:
            results.append("Timeout")
    return results


def unwrap(string: str, label: str) -> str:
    pattern = re.compile(rf'<{label}>(.*?)</{label}>', re.DOTALL)
    match = pattern.search(string)

    extracted = match.group(1).strip() if match else string

    if label in {'code', 'test'} and '```' in extracted:
        extracted = post_process(extracted)

    if label == 'code':
        try:
            cleaned = remove_comments_and_asserts(extracted)
            return transform_code(cleaned).strip()
        except Exception as e:
            return ''

    return extracted


def check_failed_input_output_examples(result_list, inputs, outputs):
    if inputs == [] or outputs == []:
        return [], 1
    failed_input_output_examples = []
    for i in range(len(inputs)):
        if result_list[i] != outputs[i]:
            failed_input_output_examples.append([inputs[i], result_list[i], outputs[i]])
    return failed_input_output_examples, 1 - (len(failed_input_output_examples) / len(inputs))


def compare(results, outputs):
    if len(results) != len(outputs):
        return False
    for result, output in zip(results, outputs):
        if len(result) != len(output):
            return False
        for res, out in zip(result, output):
            try:
                if (isinstance(res, (int, float, complex)) and isinstance(out, (int, float, complex))
                        and math.isclose(res, out, rel_tol=0.001)):
                    continue
                if res != out:
                    return False
            except:
                return False
    return True


def wilson_lower(p_obs, n, z=1.96):
    if n == 0 or p_obs < 0 or p_obs > 1:
        return 0.0

    x = round(p_obs * n)
    x = max(0, min(x, n))

    denominator = 1 + (z ** 2) / n
    centre_adjusted = x / n + (z ** 2) / (2 * n)
    adjusted_variance = (x * (n - x) / n ** 3) + (z ** 2) / (4 * n ** 2)

    if adjusted_variance <= 0:
        return max(0.0, x / n - z / (2 * n))

    adjust = z * math.sqrt(adjusted_variance)
    lower_bound = (centre_adjusted - adjust) / denominator

    return max(lower_bound, 0.0)


def construct_output_file(cwd, model_name, dataset, threshold, wo_example, task):
    model_name = model_name.replace(".", "")

    if not os.path.exists(f"{cwd}/{task}/{model_name}"):
        os.makedirs(f"{cwd}/{task}/{model_name}")

    # Open dataset and output JSONL in one place
    if threshold is None:
        output_file = f"{cwd}/{task}/{model_name}/{dataset}{wo_example}.jsonl"
    else:
        output_file = f"{cwd}/{task}/{model_name}/{dataset}_{str(int(threshold * 100))}{wo_example}.jsonl"
    return output_file


def calculate_mcc(predict, ground_truths):
    return matthews_corrcoef(ground_truths, predict)


def get_parameter_number(requirement, entry_point):
    for line in requirement.split("\n"):
        if f"def {entry_point}(" in line:
            return line.split("(")[1].split(")")[0].count(":")


def generate_pilot(file_name):
    with jsonlines.open(file_name) as reader, jsonlines.open(file_name.replace(".jsonl", "_pilot.jsonl"),
                                                             "w") as writer:
        for i, problem in enumerate(reader):
            if i < 50:
                writer.write(problem)
