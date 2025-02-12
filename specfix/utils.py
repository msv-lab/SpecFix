import os
import random

import math
import types
import re
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
    except Exception as e:
        return repr(e)


def execute_inputs(func_str, inputs_list, entry_point, timeout=1):
    results = []
    for i in trange(len(inputs_list)):
        # for i in range(len(inputs_list)):
        try:
            results.append([func_timeout(timeout, execute, args=(func_str, inputs_list[i], entry_point))])
        except FunctionTimedOut:
            results.append("Timeout")
    return results


def construct_test_case(program, inputs):
    """
    First extract function name from program. Then construct a test case for a given program.e.g., assert func_name(inputs) == outputs. return a list of assertions.
    """
    local_scope = {}
    exec(program, {}, local_scope)
    func_name = next(iter(local_scope))
    assertions = []
    outputs = execute_inputs(program, inputs)
    for i, input_args in enumerate(inputs):
        assertions.append(f"assert {func_name}({input_args}) == {outputs[i]}")
    return assertions


def unwrap(string, label):
    string = string.split(f"<{label}>", 1)[1].split(f"</{label}>")[
        0].strip() if f"<{label}>" in string and f"</{label}>" in string and string.index(
        f"<{label}>") < string.index(
        f"</{label}>") else string
    if "```" in string and (label == "code" or label == "test"):
        string = post_process(string)
    if label == "code":
        try:
            string = remove_comments_and_asserts(string).strip()
            string = transform_code(string)
        except:
            return ""
    return string


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

    if not os.path.exists(f"{cwd}/{model_name}"):
        os.mkdir(f"{cwd}/{model_name}")

    # Open dataset and output JSONL in one place
    if threshold is None:
        output_file = f"{cwd}/{model_name}/{dataset}{wo_example}_{task}.jsonl"
    else:
        output_file = f"{cwd}/{model_name}/{dataset}_{str(int(threshold * 100))}{wo_example}_{task}.jsonl"
    return output_file


def calculate_mcc(predict, ground_truths):
    return matthews_corrcoef(ground_truths, predict)


def get_parameter_number(requirement, entry_point):
    for line in requirement.split("\n"):
        if f"def {entry_point}(" in line:
            return len(line.split("(")[1].split(")")[0].split(","))
