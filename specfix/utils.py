import inspect
import os
import subprocess
import sys
import tempfile
import types
import random
from datetime import datetime
from os.path import dirname, abspath
from typing import List, Dict, Set, Tuple
from copy import deepcopy
import math
import re
import jsonlines
from func_timeout import func_timeout, FunctionTimedOut
from tqdm import trange
from sklearn.metrics import matthews_corrcoef
from specfix.solution_transformer import remove_comments_and_asserts, transform_code
from evalplus.data import get_human_eval_plus, get_mbpp_plus, get_human_eval_plus_hash, get_mbpp_plus_hash
from evalplus.evaluate import get_groundtruth
import numpy as np


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
            # results.append([execute(func_str, deepcopy_arguments(inputs_list[i]), entry_point)])
            deepcopy_argument = deepcopy(inputs_list[i])
            results.append(
                [func_timeout(timeout, execute, args=(func_str, deepcopy_argument, entry_point))])
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
            return transform_code(cleaned).strip()
            # return cleaned.strip()
        except Exception as e:
            print("AST parsing error")
            print(extracted)
            return ""

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


def construct_output_file(cwd, model_name, dataset, task):
    # timestamp by minute
    time_stamp = datetime.now().strftime("%Y%m%d%H%M")
    if not os.path.exists(f"{cwd}/{task}/{model_name}/{time_stamp}"):
        os.makedirs(f"{cwd}/{task}/{model_name}/{time_stamp}")

    output_file = f"{cwd}/{task}/{model_name}/{time_stamp}/{dataset}.jsonl"
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


def get_inputs_outputs(data_name):
    if data_name == "humaneval" or data_name == "mbpp":
        return get_evalplus_inputs_outputs(data_name)
    elif data_name == "taco_lite":
        return get_taco_lite_inputs_outputs()
    else:
        raise ValueError("Invalid data_name")


def get_entry_point(requirement):
    for line in requirement.split("\n"):
        if "def " in line and "(" in line and ")" in line and ":" in line:
            return line.split("def ")[1].split("(")[0]
    return None


def deepcopy_crosshair(program, entry_point):
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
    print("Crosshair compare")
    with tempfile.TemporaryDirectory(delete=True) as tmpdirname:
        with open(f"{tmpdirname}/program1.py", "w") as f:
            program1 = deepcopy_crosshair(program1, entry_point).strip()
            if program1 == "":
                return False
            f.write(program1)
        with open(f"{tmpdirname}/program2.py", "w") as f:
            program2 = deepcopy_crosshair(program2, entry_point).strip()
            if program2 == "":
                return False
            f.write(program2)
        try:
            result = subprocess.run(
                ["crosshair", "diffbehavior", f"program1.f", f"program2.f", "--exception_equivalence", "SAME_TYPE",
                 "--per_condition_timeout", "10"],
                capture_output=True, text=True, cwd=f"{tmpdirname}")
            if result.returncode != 0:
                return False
            else:
                return True
        except:
            return "CrosshairError"


def unify_model_name(model_name):
    model_name = model_name.split("/")[-1]
    if model_name == "deepseek-chat" or model_name == "deepseek-v3-241226" or model_name == "deepseek-v3-241226-deprecated":
        model_name = "deepseek-v3"
    elif model_name == "deepseek-reasoner":
        model_name = "deepseek-r1"
    return model_name


def count_entropy(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_ambiguity = []
    repaired_ambiguity = []
    for result in results:
        if result["original_clusters"] is not None:
            original_ambiguity.append(result["original_clusters"]["entropy"])
        if result["repaired_clusters"] is not None:
            repaired_ambiguity.append(result["repaired_clusters"]["entropy"])
    print(
        f"{model} {dataset} original entropy: {sum(original_ambiguity) / len(original_ambiguity)}, repaired entropy: {sum(repaired_ambiguity) / len(repaired_ambiguity)}, Improvement: {sum(repaired_ambiguity) / len(repaired_ambiguity) - sum(original_ambiguity) / len(original_ambiguity)}")


def count_entropy_ambiguous(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_ambiguity = []
    repaired_ambiguity = []
    for result in results:
        if result["repaired_requirement"] is not None:
            if result["original_clusters"] is not None:
                original_ambiguity.append(result["original_clusters"]["entropy"])
            if result["repaired_clusters"] is not None:
                repaired_ambiguity.append(result["repaired_clusters"]["entropy"])
    print(
        f"{model} {dataset} AMBIGUOUS original entropy: {sum(original_ambiguity) / len(original_ambiguity)}, repaired entropy: {sum(repaired_ambiguity) / len(repaired_ambiguity)}, Improvement: {sum(repaired_ambiguity) / len(repaired_ambiguity) - sum(original_ambiguity) / len(original_ambiguity)}")


def count_passk(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = []
    repaired_results = []
    for result in results:
        if result["result"]["original_passk"] is not None:
            original_results.append(result["result"]["original_passk"])
        if result["result"]["repaired_passk"] is not None:
            repaired_results.append(result["result"]["repaired_passk"])
    print(
        f"{model} {dataset} original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


def count_passk_ambiguous(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    origin_result_list = []
    repaired_result_list = []
    for result in results:
        if result["repaired_requirement"] is not None:
            if result["result"]["original_passk"] is not None and result["result"]["repaired_passk"] is not None:
                origin_result_list.append(result["result"]["original_passk"])
                repaired_result_list.append(result["result"]["repaired_passk"])
    print(
        f"{model} {dataset} AMBIGUOUS original pass@1: {sum(origin_result_list) / len(origin_result_list)}, repaired pass@1: {sum(repaired_result_list) / len(repaired_result_list)}, Improvement: {sum(repaired_result_list) / len(repaired_result_list) - sum(origin_result_list) / len(origin_result_list)}")


def count_pass_rate(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = []
    repaired_results = []
    for result in results:
        if result["result"]["original_pass_rate"] is not None:
            original_results.append(result["result"]["original_pass_rate"])
        if result["result"]["repaired_pass_rate"] is not None:
            repaired_results.append(result["result"]["repaired_pass_rate"])
    print(
        f"{model} {dataset} original pass rate: {sum(original_results) / len(original_results)}, repaired pass rate: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


def count_pass_rate_ambiguous(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = []
    repaired_results = []
    for result in results:
        if result["repaired_requirement"] is not None:
            if result["result"]["original_pass_rate"] is not None and result["result"][
                "repaired_pass_rate"] is not None:
                original_results.append(result["result"]["original_pass_rate"])
                repaired_results.append(result["result"]["repaired_pass_rate"])
    print(
        f"{model} {dataset} AMBIGUOUS original pass rate: {sum(original_results) / len(original_results)}, repaired pass rate: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


def count_overall_passk(label, model):
    original_results = []
    repaired_results = []
    for filepath, dirname, filenames in os.walk(f"{label}/{model}/"):
        for filename in filenames:
            if "localization" in filename:
                continue
            results = read_jsonl(f"{filepath}{filename}")
            for result in results:
                original_results.append(result["original_passk"])
                repaired_results.append(result["repaired_passk"])
    print(
        f"Overall original pass@1: {sum(original_results) / len(original_results)}, repaired pass@1: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


def count_overall_passk_ambiguous(label, model):
    origin_result_list = []
    repaired_result_list = []
    for filepath, dirname, filenames in os.walk(f"{label}/{model}/"):
        for filename in filenames:
            results = read_jsonl(f"{filepath}{filename}")
            for result in results:
                if result["repaired_requirement"] is not None:
                    origin_result_list.append(result["original_passk"])
                    repaired_result_list.append(result["original_passk"])
    print(
        f"Overall original pass@1: {sum(origin_result_list) / len(origin_result_list)}, repaired pass@1: {sum(repaired_result_list) / len(repaired_result_list)}, Improvement: {sum(repaired_result_list) / len(repaired_result_list) - sum(origin_result_list) / len(origin_result_list)}")


def count_passk_bigger_than_0(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = []
    repaired_results = []
    for result in results:
        if result["result"]["original_passk_bigger_than_0"] is not None:
            original_results.append(result["result"]["original_passk_bigger_than_0"])
        if result["result"]["repaired_passk_bigger_than_0"] is not None:
            repaired_results.append(result["result"]["repaired_passk_bigger_than_0"])
    print(
        f"{model} {dataset} original pass@1 bigger than 0: {sum(original_results) / len(original_results)}, repaired pass@1 bigger than 0: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


def count_passk_bigger_than_0_ambiguous(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = []
    repaired_results = []
    for result in results:
        if result["repaired_requirement"] is not None:
            if result["result"]["original_passk_bigger_than_0"] is not None and result["result"][
                "repaired_passk_bigger_than_0"] is not None:
                original_results.append(result["result"]["original_passk_bigger_than_0"])

                repaired_results.append(result["result"]["repaired_passk_bigger_than_0"])
    print(
        f"{model} {dataset} AMBIGUOUS original pass@1 bigger than 0: {sum(original_results) / len(original_results)}, repaired pass@1 bigger than 0: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


def count_solved_with_majority_vote(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = []
    repaired_results = []
    for result in results:
        if result["result"]["original_solved_with_majority_vote"] is not None:
            original_results.append(result["result"]["original_solved_with_majority_vote"])
        if result["result"]["repaired_solved_with_majority_vote"] is not None:
            repaired_results.append(result["result"]["repaired_solved_with_majority_vote"])
    print(
        f"{model} {dataset} original solved with majority vote: {sum(original_results) / len(original_results)}, repaired solved with majority vote: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


def count_solved_with_majority_vote_ambiguous(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = []
    repaired_results = []
    for result in results:
        if result["repaired_requirement"] is not None:
            if result["result"]["original_solved_with_majority_vote"] is not None and result["result"][
                "repaired_solved_with_majority_vote"] is not None:
                original_results.append(result["result"]["original_solved_with_majority_vote"])
                repaired_results.append(result["result"]["repaired_solved_with_majority_vote"])
    print(
        f"{model} {dataset} AMBIGUOUS original solved with majority vote: {sum(original_results) / len(original_results)}, repaired solved with majority vote: {sum(repaired_results) / len(repaired_results)}, Improvement: {sum(repaired_results) / len(repaired_results) - sum(original_results) / len(original_results)}")


def count_repaired_passk_woe(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = read_jsonl(
        f"{dirname(abspath(__file__))}/../experiment/original_result/original_result/{model}/{dataset}.jsonl")
    original_passks = []
    original_woe_passks = []
    repaired_passks = []
    repaired_woe_passks = []
    for result in results:
        if result["repaired_requirement"] is not None:
            for original in original_results:
                if original["task_id"] == result["task_id"]:
                    original_passk = original["result"]["original_passk"]
                    original_woe_passk = original["result"]["original_woe_passk"]
                    break
            if original_passk is not None and original_woe_passk is not None and result["result"][
                "repaired_passk"] is not None and result["result"]["repaired_woe_passk"] is not None:
                original_passks.append(original_passk)
                original_woe_passks.append(original_woe_passk)
                repaired_passks.append(result["result"]["repaired_passk"])
                repaired_woe_passks.append(result["result"]["repaired_woe_passk"])
    print(
        f"{model} {dataset} original pass@1: {sum(original_passks) / len(original_passks)}, original woe pass@1: {sum(original_woe_passks) / len(original_woe_passks)}, Improvement: {sum(original_passks) / len(original_passks) - sum(original_woe_passks) / len(original_woe_passks)}, repaired pass@1: {sum(repaired_passks) / len(repaired_passks)}, repaired woe pass@1: {sum(repaired_woe_passks) / len(repaired_woe_passks)}, Improvement: {sum(repaired_passks) / len(repaired_passks) - sum(repaired_woe_passks) / len(repaired_woe_passks)}")


def count_repaired_pass_rate_woe(label, model, dataset):
    results = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = read_jsonl(
        f"{dirname(abspath(__file__))}/../experiment/original_result/original_result/{model}/{dataset}.jsonl")
    original_pass_rates = []
    original_woe_pass_rates = []
    repaired_pass_rates = []
    repaired_woe_pass_rates = []
    for result in results:
        if result["repaired_requirement"] is not None:
            for original in original_results:
                if original["task_id"] == result["task_id"]:
                    original_pass_rate = original["result"]["original_pass_rate"]
                    original_woe_pass_rate = original["result"]["original_woe_pass_rate"]
                    break
            if original_pass_rate is not None and original_woe_pass_rate is not None and result["result"][
                "repaired_pass_rate"] is not None and result["result"]["repaired_woe_pass_rate"] is not None:
                original_pass_rates.append(original_pass_rate)
                original_woe_pass_rates.append(original_woe_pass_rate)
                repaired_pass_rates.append(result["result"]["repaired_pass_rate"])
                repaired_woe_pass_rates.append(result["result"]["repaired_woe_pass_rate"])
    print(
        f"{model} {dataset} original pass rate: {sum(original_pass_rates) / len(original_pass_rates)}, original woe pass rate: {sum(original_woe_pass_rates) / len(original_woe_pass_rates)}, Improvement: {sum(original_pass_rates) / len(original_pass_rates) - sum(original_woe_pass_rates) / len(original_woe_pass_rates)}, repaired pass rate: {sum(repaired_pass_rates) / len(repaired_pass_rates)}, repaired woe pass rate: {sum(repaired_woe_pass_rates) / len(repaired_woe_pass_rates)}, Improvement: {sum(repaired_pass_rates) / len(repaired_pass_rates) - sum(repaired_woe_pass_rates) / len(repaired_woe_pass_rates)}")


def count_repaired_passk_bigger_than_0_woe(label, model, dataset):
    result = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = read_jsonl(
        f"{dirname(abspath(__file__))}/../experiment/original_result/original_result/{model}/{dataset}.jsonl")
    original_passk_bigger_than_0s = []
    original_woe_passk_bigger_than_0s = []
    repaired_passk_bigger_than_0s = []
    repaired_woe_passk_bigger_than_0s = []
    for res in result:
        if res["repaired_requirement"] is not None:
            for original in original_results:
                if original["task_id"] == res["task_id"]:
                    original_passk_bigger_than_0 = original["result"]["original_passk_bigger_than_0"]
                    original_woe_passk_bigger_than_0 = original["result"]["original_woe_passk_bigger_than_0"]
                    break
            if original_passk_bigger_than_0 is not None and original_woe_passk_bigger_than_0 is not None and \
                    res["result"][
                        "repaired_passk_bigger_than_0"] is not None and res["result"][
                "repaired_woe_passk_bigger_than_0"] is not None:
                original_passk_bigger_than_0s.append(original_passk_bigger_than_0)
                original_woe_passk_bigger_than_0s.append(original_woe_passk_bigger_than_0)
                repaired_passk_bigger_than_0s.append(res["result"]["repaired_passk_bigger_than_0"])
                repaired_woe_passk_bigger_than_0s.append(res["result"]["repaired_woe_passk_bigger_than_0"])
    print(
        f"{model} {dataset} original pass@1 bigger than 0: {sum(original_passk_bigger_than_0s) / len(original_passk_bigger_than_0s)}, original woe pass@1 bigger than 0: {sum(original_woe_passk_bigger_than_0s) / len(original_woe_passk_bigger_than_0s)}, Improvement: {sum(original_passk_bigger_than_0s) / len(original_passk_bigger_than_0s) - sum(original_woe_passk_bigger_than_0s) / len(original_woe_passk_bigger_than_0s)}, repaired pass@1 bigger than 0: {sum(repaired_passk_bigger_than_0s) / len(repaired_passk_bigger_than_0s)}, repaired woe pass@1 bigger than 0: {sum(repaired_woe_passk_bigger_than_0s) / len(repaired_woe_passk_bigger_than_0s)}, Improvement: {sum(repaired_passk_bigger_than_0s) / len(repaired_passk_bigger_than_0s) - sum(repaired_woe_passk_bigger_than_0s) / len(repaired_woe_passk_bigger_than_0s)}")


def count_repaired_solved_with_majority_vote_woe(label, model, dataset):
    result = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = read_jsonl(
        f"{dirname(abspath(__file__))}/../experiment/original_result/original_result/{model}/{dataset}.jsonl")
    original_solved_with_majority_votes = []
    original_woe_solved_with_majority_votes = []
    repaired_solved_with_majority_votes = []
    repaired_woe_solved_with_majority_votes = []
    for res in result:
        if res["repaired_requirement"] is not None:
            for original in original_results:
                if original["task_id"] == res["task_id"]:
                    original_solved_with_majority_vote = original["result"]["original_solved_with_majority_vote"]
                    original_woe_solved_with_majority_vote = original["result"][
                        "original_woe_solved_with_majority_vote"]
                    break
            if original_solved_with_majority_vote is not None and original_woe_solved_with_majority_vote is not None and \
                    res["result"][
                        "repaired_solved_with_majority_vote"] is not None and res["result"][
                "repaired_woe_solved_with_majority_vote"] is not None:
                original_solved_with_majority_votes.append(original_solved_with_majority_vote)
                original_woe_solved_with_majority_votes.append(original_woe_solved_with_majority_vote)
                repaired_solved_with_majority_votes.append(res["result"]["repaired_solved_with_majority_vote"])
                repaired_woe_solved_with_majority_votes.append(res["result"]["repaired_woe_solved_with_majority_vote"])
    print(
        f"{model} {dataset} original solved with majority vote: {sum(original_solved_with_majority_votes) / len(original_solved_with_majority_votes)}, original woe solved with majority vote: {sum(original_woe_solved_with_majority_votes) / len(original_woe_solved_with_majority_votes)}, Improvement: {sum(original_solved_with_majority_votes) / len(original_solved_with_majority_votes) - sum(original_woe_solved_with_majority_votes) / len(original_woe_solved_with_majority_votes)}, repaired solved with majority vote: {sum(repaired_solved_with_majority_votes) / len(repaired_solved_with_majority_votes)}, repaired woe solved with majority vote: {sum(repaired_woe_solved_with_majority_votes) / len(repaired_woe_solved_with_majority_votes)}, Improvement: {sum(repaired_solved_with_majority_votes) / len(repaired_solved_with_majority_votes) - sum(repaired_woe_solved_with_majority_votes) / len(repaired_woe_solved_with_majority_votes)}")


def count_repaired_entropy_woe(label, model, dataset):
    result = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_results = read_jsonl(
        f"{dirname(abspath(__file__))}/../experiment/original_result/original_result/{model}/{dataset}.jsonl")
    original_entropy = []
    original_woe_entropy = []
    repaired_entropy = []
    repaired_woe_entropy = []
    for res in result:
        if res["repaired_requirement"] is not None:
            for original in original_results:
                if original["task_id"] == res["task_id"]:
                    entropy = original["original_clusters"]["entropy"] if original[
                                                                              "original_clusters"] is not None else None
                    woe_entropy = original["original_woe_clusters"]["entropy"] if original[
                                                                                      "original_woe_clusters"] is not None else None
                    break
            if entropy is not None and woe_entropy is not None and res["repaired_clusters"] is not None and res[
                "repaired_woe_clusters"] is not None:
                original_entropy.append(entropy)
                original_woe_entropy.append(woe_entropy)
                repaired_entropy.append(res["repaired_clusters"]["entropy"])
                repaired_woe_entropy.append(res["repaired_woe_clusters"]["entropy"])
    print(
        f"{model} {dataset} original entropy: {sum(original_entropy) / len(original_entropy)}, original woe entropy: {sum(original_woe_entropy) / len(original_woe_entropy)}, Improvement: {sum(original_entropy) / len(original_entropy) - sum(original_woe_entropy) / len(original_woe_entropy)}, repaired entropy: {sum(repaired_entropy) / len(repaired_entropy)}, repaired woe entropy: {sum(repaired_woe_entropy) / len(repaired_woe_entropy)}, Improvement: {sum(repaired_entropy) / len(repaired_entropy) - sum(repaired_woe_entropy) / len(repaired_woe_entropy)}")


def count_rq1(label, model, dataset):
    count_passk(label, model, dataset)
    count_passk_ambiguous(label, model, dataset)
    count_pass_rate(label, model, dataset)
    count_pass_rate_ambiguous(label, model, dataset)
    count_passk_bigger_than_0(label, model, dataset)
    count_passk_bigger_than_0_ambiguous(label, model, dataset)
    count_solved_with_majority_vote(label, model, dataset)
    count_solved_with_majority_vote_ambiguous(label, model, dataset)
    count_entropy(label, model, dataset)
    count_entropy_ambiguous(label, model, dataset)


def count_rq2(label, model, dataset):
    count_repaired_passk_woe(label, model, dataset)
    count_repaired_pass_rate_woe(label, model, dataset)
    count_repaired_passk_bigger_than_0_woe(label, model, dataset)
    count_repaired_solved_with_majority_vote_woe(label, model, dataset)
    count_repaired_entropy_woe(label, model, dataset)


def calculate_pass_k(n, c, k):
    """
       Computes pass@k metric for code generation tasks.

       Args:
           n: Total number of generated samples.
           c: Number of correct samples that pass the tests.
           k: The k in pass@k (number of attempts allowed).

       Returns:
           The estimated pass@k metric.

       Raises:
           ValueError: If the inputs are invalid.
       """
    if c == 0:
        return 0.0

    if (n - c) < k:
        return 1.0

    prob_no_pass = 1.0
    for i in range(k):
        prob_no_pass *= (n - c - i) / (n - i)

    return 1 - prob_no_pass


def calculate_test_consistency(program_str, entry_point, inputs, outputs):
    result_list = execute_inputs(program_str, inputs, entry_point)
    failed_input_output_examples, test_consistency = get_failed_input_output(result_list,
                                                                             inputs, outputs)
    return failed_input_output_examples, test_consistency


def get_exception_list():
    # list of major exception types
    exception_type = [["TypeError"], ["ValueError"], ["SyntaxError"], ["NameError"], ["IndexError"],
                      ["KeyError"], ["AttributeError"], ["ImportError"], ["ModuleNotFoundError"], ["MemoryError"],
                      ["RecursionError"], ["ZeroDivisionError"],
                      ["NotImplementedError"], ["RuntimeError"], ["AssertionError"], ["OverflowError"],
                      ["FloatingPointError"], ["IndentationError"]]
    return exception_type


def is_significant_large(prob_list):  # max_val > second_max_val * (n / (n - 1))
    prob_list = [prob / sum(prob_list) for prob in prob_list]
    sorted_prob_list = sorted(prob_list, reverse=True)
    max_val = sorted_prob_list[0]
    second_max_val = sorted_prob_list[1]
    if max_val == second_max_val:
        return False
    n = len(prob_list)
    threshold = second_max_val * (1 + 1 / (n - 1))
    return max_val > threshold


def count_rq3(label, model, dataset):
    problems = read_jsonl(f"{label}/{model}/{dataset}.jsonl")
    original_lengths = []
    repaired_lengths = []
    for problem in problems:
        if problem["repaired_requirement"] is not None:
            original_lengths.append(len(problem["requirement"].split()))
            repaired_lengths.append(len(problem["repaired_requirement"].split()))
    print(
        f"{model} {dataset} original requirement length: {sum(original_lengths) / len(original_lengths)}, repaired requirement length: {sum(repaired_lengths) / len(repaired_lengths)}, Improvement: {(sum(repaired_lengths) / len(repaired_lengths) - sum(original_lengths) / len(original_lengths)) / (sum(original_lengths) / len(original_lengths))}")


def safe_eval(val):
    class ReMatch:
        def __init__(self, span, match):
            self.span = span
            self.match = match

        def __repr__(self):
            return f"<re.Match object; span={self.span}, match=<'{self.match}'>"

    def replace_func(m):
        start = int(m.group(1))
        end = int(m.group(2))
        text = m.group(3)
        return f"ReMatch(({start}, {end}), '{text}')"

    if "re.Match object" in val:
        pattern = r"<re\.Match object; span=\((\d+),\s*(\d+)\), match='([^']+)'>"
        val = re.sub(pattern, replace_func,
                     val)
    return eval(val, {
        "np": np, "inf": float("inf"),
        "nan": float("nan"),
        "ReMatch": ReMatch,
        "ZeroDivisionError": ZeroDivisionError,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "IndexError": IndexError,
        "KeyError": KeyError,
        "AttributeError": AttributeError,
        "NameError": NameError,
        "SyntaxError": SyntaxError,
        "AssertionError": AssertionError,
        "RecursionError": RecursionError,
        "FileNotFoundError": FileNotFoundError,
        "ModuleNotFoundError": ModuleNotFoundError,
        "ImportError": ImportError,
        "MemoryError": MemoryError,
        "OverflowError": OverflowError,
        "RuntimeError": RuntimeError,
        "StopIteration": StopIteration
    })
