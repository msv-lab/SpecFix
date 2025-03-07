import inspect
import os
import subprocess
import sys
import tempfile
import types
import random
from os.path import dirname, abspath
from typing import List, Dict, Set, Tuple

import math
import re
import jsonlines
from func_timeout import func_timeout, FunctionTimedOut
from tqdm import trange
from sklearn.metrics import matthews_corrcoef
from specfix.solution_transformer import remove_comments_and_asserts, transform_code
from evalplus.data import get_human_eval_plus, get_mbpp_plus, get_human_eval_plus_hash, get_mbpp_plus_hash
from evalplus.evaluate import get_groundtruth


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
    if func_str == "":
        return "EmptyCodeError"
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

        except (ModuleNotFoundError, ImportError) as e:
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
            results.append(["Timeout"])
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
            # return transform_code(cleaned).strip()
            return cleaned.strip()
        except Exception as e:
            print("AST parsing error")
            print(extracted)
            return ''

    return extracted


def get_failed_input_output(result_list, inputs, outputs):
    if inputs == [] or outputs == [] or compare(result_list, outputs):
        return [], 1
    failed_input_output_examples = []
    for i in range(len(inputs)):
        if not compare(result_list[i], outputs[i]):
            failed_input_output_examples.append([inputs[i], result_list[i], outputs[i]])
    return failed_input_output_examples, 1 - (len(failed_input_output_examples) / len(inputs))


def compare(a, b):
    try:
        if a == "Timeout" or b == "Timeout":
            return True
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            if len(a) != len(b):
                return False
            for x, y in zip(a, b):
                if not compare(x, y):
                    return False
            return True
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return math.isclose(a, b, rel_tol=0.001)
        else:
            return a == b
    except:
        return False


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
    if not os.path.exists(f"{cwd}/{task}/{model_name}"):
        os.makedirs(f"{cwd}/{task}/{model_name}")

    # Open dataset and output JSONL in one place
    if threshold is None:
        output_file = f"{cwd}/{task}/{model_name}/{dataset}{wo_example}.jsonl"
    else:
        output_file = f"{cwd}/{task}/{model_name}/{dataset}{wo_example}_{str(threshold)}.jsonl"
    return output_file


def calculate_mcc(ground_truths, predict):
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


def read_jsonl(file_name):
    with jsonlines.open(file_name) as reader:
        return list(reader)


def get_evalplus_inputs_outputs(data_name):
    data = get_human_eval_plus() if data_name == "humaneval" else get_mbpp_plus()
    hash = get_human_eval_plus_hash() if data_name == "humaneval" else get_mbpp_plus_hash()
    expected_outputs = get_groundtruth(data, hash, [])
    inputs = []
    outputs = []
    for key in data.keys():
        problem = data[key]
        inputs.append((problem['base_input'] + problem['plus_input']) if problem['plus_input'] != {} else problem[
            'base_input'])
        outputs.append([[output] for output in expected_outputs[key]['base'] + expected_outputs[key]['plus']])
    return inputs, outputs


def get_taco_lite_inputs_outputs():
    path = dirname(abspath(__file__)) + '/../dataset/' + "taco_lite.jsonl"
    problems = read_jsonl(path)
    return [problem['inputs'] for problem in problems], [problem['outputs'] for problem in problems]


def get_entry_point(requirement):
    for line in requirement.split("\n"):
        if "def " in line and "(" in line and ")" in line and ":" in line:
            return line.split("def ")[1].split("(")[0]
    return None


def deepcopy(program, entry_point):
    try:
        namespace = {}
        exec(program, namespace)

        func_name = entry_point
        target_func = namespace[func_name]

        sig = inspect.signature(target_func)
        params = sig.parameters

        mutable_containers = {list, dict, set, tuple, List, Dict, Set, Tuple}
        needs_deepcopy = []
        type_hints = []

        for name, param in params.items():
            anno = param.annotation
            type_str = "Any"

            if getattr(anno, "__origin__", None) in mutable_containers:
                needs_deepcopy.append(name)
                args = [a.__name__ for a in getattr(anno, "__args__", [])]
                type_str = f"{anno.__origin__.__name__}[{', '.join(args)}]"
            elif anno in mutable_containers:
                needs_deepcopy.append(name)
                type_str = anno.__name__ if isinstance(anno, type) else anno._name
            elif anno != param.empty:
                type_str = anno.__name__ if isinstance(anno, type) else str(anno)

            type_hints.append(f"{name}: {type_str}")

        copy_lines = [
            f"    {name}_copy = copy.deepcopy({name})"
            for name in needs_deepcopy
        ]
        arg_list = [
            f"{name}_copy" if name in needs_deepcopy else name
            for name in params
        ]
        final_program = f"""
import copy

{program}

def f({', '.join(type_hints)}):
{chr(10).join(copy_lines) if copy_lines else "    pass"}
    return {func_name}({', '.join(arg_list)})
    """
        return final_program
    except Exception as e:
        return ""


def crosshair_compare(program1, program2, entry_point):
    with tempfile.TemporaryDirectory(delete=True) as tmpdirname:
        with open(f"{tmpdirname}/program1.py", "w") as f:
            program1 = deepcopy(program1, entry_point).strip()
            if program1 == "":
                return False
            f.write(program1)
        with open(f"{tmpdirname}/program2.py", "w") as f:
            program2 = deepcopy(program2, entry_point).strip()
            if program2 == "":
                return False
            f.write(program2)
        try:
            result = subprocess.run(
                ["crosshair", "diffbehavior", f"program1.f", f"program2.f", "--exception_equivalence", "SAME_TYPE",
                 "--per_condition_timeout", "1"],
                capture_output=True, text=True, cwd=f"{tmpdirname}")
            if result.returncode != 0:
                return False
            else:
                return True
        except:
            return "CrosshairError"


def unify_model_name(model_name):
    model_name = model_name.split("/")[-1]
    if model_name == "deepseek-chat" or model_name == "deepseek-v3-241226":
        model_name = "deepseek-v3"
    elif model_name == "deepseek-reasoner":
        model_name = "deepseek-r1"
    elif model_name == "qwen2p5-coder-32b-instruct":
        model_name = "qwen2.5-coder-32b-instruct"
    return model_name


def count_passk_ambiguous(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    origin_result_list = []
    repaired_result_list = []
    for result in results:
        if result["repaired_requirement"] is not None:
            origin_result_list.append(result["original_result"])
            repaired_result_list.append(result["repaired_result"])
    print(
        f"{dataset} original pass@1: {sum(origin_result_list) / len(origin_result_list)}, repaired pass@1: {sum(repaired_result_list) / len(repaired_result_list)}, Improvement: {sum(repaired_result_list) / len(repaired_result_list) - sum(origin_result_list) / len(origin_result_list)}")


def count_ambiguity(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_ambiguity = []
    repaired_ambiguity = []
    for result in results:
        if result["repaired_clusters"] is not None:
            original_ambiguity.append(result["original_clusters"]["ambiguity"])
            repaired_ambiguity.append(result["repaired_clusters"]["ambiguity"])
    print(
        f"{dataset} original ambiguity: {sum(original_ambiguity) / len(original_ambiguity)}, repaired ambiguity: {sum(repaired_ambiguity) / len(repaired_ambiguity)}, Improvement: {sum(repaired_ambiguity) / len(repaired_ambiguity) - sum(original_ambiguity) / len(original_ambiguity)}")


def count_passk(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = []
    repaired_results = []
    for result in results:
        original_results.append(result["original_result"])
        repaired_results.append(result["repaired_result"])
    print(
        f"{dataset} original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")