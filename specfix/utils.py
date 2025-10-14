import ast
import inspect
import math
import re
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

import jsonlines
import numpy as np
from evalplus.data import (
    get_human_eval_plus,
    get_human_eval_plus_hash,
    get_mbpp_plus,
    get_mbpp_plus_hash,
)
from evalplus.evaluate import get_groundtruth

from specfix.execute_util import get_stripped_lines
from specfix.solution_transformer import remove_comments_and_asserts


JsonDict = Dict[str, Any]
MetricResult = Tuple[float, float, float]
NestedPath = Sequence[str]
Predicate = Callable[[JsonDict], bool]

MAJOR_EXCEPTIONS: Tuple[Tuple[str, ...], ...] = (
    ("TypeError",),
    ("ValueError",),
    ("SyntaxError",),
    ("NameError",),
    ("IndexError",),
    ("KeyError",),
    ("AttributeError",),
    ("ImportError",),
    ("ModuleNotFoundError",),
    ("MemoryError",),
    ("RecursionError",),
    ("ZeroDivisionError",),
    ("NotImplementedError",),
    ("RuntimeError",),
    ("AssertionError",),
    ("OverflowError",),
    ("FloatingPointError",),
    ("IndentationError",),
    ("TimeoutError",),
)

_SAFE_EVAL_GLOBALS: Dict[str, Any] = {
    "np": np,
    "inf": float("inf"),
    "nan": float("nan"),
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
    "StopIteration": StopIteration,
}


def extract_exception_type(stderr: str) -> str:
    """Return the innermost exception type from stderr text."""
    if not stderr:
        return "Error"

    lines = stderr.strip().splitlines()
    for line in reversed(lines):
        candidate = line.strip()
        if not candidate:
            continue
        lowered = candidate.lower()
        if lowered.startswith("during handling of the above exception") or lowered.startswith(
            "the above exception was the direct cause of the following exception"
        ):
            continue
        match = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)(?::|\s*$)", candidate
        )
        if match:
            return match.group(1).split(".")[-1]
    return "Error"


def unwrap(
    document: str, label: str, *, multiple: bool = False, default: str = ""
) -> Union[str, List[str]]:
    """Extract text enclosed in <label> tags; handles fenced code blocks for code/test."""

    def process_extracted(extracted: str) -> str:
        snippet = extracted.strip()

        if label in {"code", "test"} and "```" in snippet:
            python_pattern = re.compile(r"```python\s*(.*?)\s*```", re.DOTALL)
            match = python_pattern.search(snippet)
            if match:
                snippet = match.group(1)
            else:
                generic_pattern = re.compile(r"```(.*?)```", re.DOTALL)
                match = generic_pattern.search(snippet)
                if match:
                    snippet = match.group(1)

        if label == "code":
            try:
                return remove_comments_and_asserts(snippet)
            except Exception:
                return ""

        return snippet

    if not document:
        return default if not multiple else []

    if label == "code":
        return process_extracted(document)

    pattern = re.compile(rf"<{re.escape(label)}>(.*?)</{re.escape(label)}>", re.DOTALL)

    if multiple:
        return [process_extracted(match.group(1)) for match in pattern.finditer(document)]

    match = pattern.search(document)
    return process_extracted(match.group(1)) if match else default


def compare(a: Any, b: Any) -> bool:
    """Recursively compare two possibly nested values with tolerance for floats."""
    try:
        if a == "TimeoutError" or b == "TimeoutError":
            return True

        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            if len(a) != len(b):
                return False
            return all(compare(x, y) for x, y in zip(a, b))

        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return math.isclose(a, b, rel_tol=0.001)

        if isinstance(a, str) and isinstance(b, str):
            a_clean = a.strip()
            b_clean = b.strip()
            if "\n" in a_clean or "\n" in b_clean:
                return compare(get_stripped_lines(a_clean), get_stripped_lines(b_clean))
            return a_clean == b_clean

        return a == b
    except Exception:
        return False


def wilson_lower(p_obs: float, n: int, z: float = 1.96) -> float:
    """Compute the lower bound of a Wilson score interval."""
    if n <= 0 or not (0 <= p_obs <= 1):
        return 0.0

    x = round(p_obs * n)
    x = max(0, min(x, n))

    denominator = 1 + (z**2) / n
    centre_adjusted = x / n + (z**2) / (2 * n)
    adjusted_variance = (x * (n - x) / n**3) + (z**2) / (4 * n**2)

    if adjusted_variance <= 0:
        return max(0.0, x / n - z / (2 * n))

    adjust = z * math.sqrt(adjusted_variance)
    lower_bound = (centre_adjusted - adjust) / denominator

    return max(lower_bound, 0.0)


def construct_output_file(cwd: str, model_name: str, dataset: str, task: str) -> str:
    """Create an output directory hierarchy and return the jsonl file path."""
    time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    target_dir = Path(cwd) / task / model_name / time_stamp
    target_dir.mkdir(parents=True, exist_ok=True)
    return str(target_dir / f"{dataset}.jsonl")


def get_parameter_number(requirement: str, entry_point: str) -> int:
    """Return the number of annotated parameters for the given entry point."""
    signature_marker = f"def {entry_point}("
    for line in requirement.splitlines():
        if signature_marker in line:
            param_segment = line.split("(", 1)[1].split(")", 1)[0]
            return param_segment.count(":")
    return 0


def read_jsonl(file_name: str) -> List[JsonDict]:
    with jsonlines.open(file_name) as reader:
        return list(reader)


def get_evalplus_inputs_outputs(data_name: str) -> Tuple[List[Any], List[Any]]:
    if data_name not in {"humaneval", "mbpp"}:
        raise ValueError(f"Unsupported dataset: {data_name}")

    data = get_human_eval_plus() if data_name == "humaneval" else get_mbpp_plus()
    hash_value = (
        get_human_eval_plus_hash() if data_name == "humaneval" else get_mbpp_plus_hash()
    )
    expected_outputs = get_groundtruth(data, hash_value, [])

    inputs: List[Any] = []
    outputs: List[Any] = []
    for key, problem in data.items():
        plus_input = problem.get("plus_input") or {}
        base_input = problem.get("base_input")
        inputs.append((base_input + plus_input) if plus_input else base_input)
        combined_outputs = expected_outputs[key]["base"] + expected_outputs[key]["plus"]
        outputs.append([[output] for output in combined_outputs])
    return inputs, outputs


def get_livecodebench_inputs_outputs(path: str) -> Tuple[List[Any], List[Any]]:
    problems = read_jsonl(path)
    inputs: List[Any] = []
    outputs: List[Any] = []
    for problem in problems:
        tests = ast.literal_eval(problem["tests"])
        inputs.append(tests[0])
        outputs.append(tests[1])
    return inputs, outputs


def get_inputs_outputs(data_name: str, path: Optional[str] = None) -> Tuple[List[Any], List[Any]]:
    loaders: Dict[str, Callable[[], Tuple[List[Any], List[Any]]]] = {
        "humaneval": lambda: get_evalplus_inputs_outputs("humaneval"),
        "mbpp": lambda: get_evalplus_inputs_outputs("mbpp"),
    }
    if data_name == "livecodebench":
        if path is None:
            raise ValueError("Path is required for livecodebench data.")
        return get_livecodebench_inputs_outputs(path)
    if data_name not in loaders:
        raise ValueError(f"Unsupported data name: {data_name}")
    return loaders[data_name]()


def deepcopy_crosshair(program: str, entry_point: str) -> str:
    try:
        namespace: Dict[str, Any] = {}
        exec(program, namespace)

        target_func = namespace[entry_point]
        sig = inspect.signature(target_func)
        params = sig.parameters

        mutable_containers = {list, dict, set, tuple, List, Dict, Set, Tuple}
        needs_deepcopy: List[str] = []
        type_hints: List[str] = []

        for name, param in params.items():
            annotation = param.annotation
            type_str = "Any"

            if getattr(annotation, "__origin__", None) in mutable_containers:
                needs_deepcopy.append(name)
                args = [a.__name__ for a in getattr(annotation, "__args__", [])]
                type_str = f"{annotation.__origin__.__name__}[{', '.join(args)}]"
            elif annotation in mutable_containers:
                needs_deepcopy.append(name)
                type_str = annotation.__name__ if isinstance(annotation, type) else annotation._name
            elif annotation != param.empty:
                type_str = annotation.__name__ if isinstance(annotation, type) else str(annotation)

            type_hints.append(f"{name}: {type_str}")

        copy_lines = [f"{name}_copy = copy.deepcopy({name})" for name in needs_deepcopy]
        arg_list = [f"{name}_copy" if name in needs_deepcopy else name for name in params]
        body_lines = copy_lines + [f"return {entry_point}({', '.join(arg_list)})"]
        indented_body = textwrap.indent("\n".join(body_lines), "    ")

        final_program = textwrap.dedent(
            f"""
            import copy

            {program}

            def f({', '.join(type_hints)}):
            {indented_body}
            """
        ).strip()
        return final_program
    except Exception:
        return ""


def crosshair_compare(program1: str, program2: str, entry_point: str) -> Union[bool, str]:
    print("Crosshair compare")
    with tempfile.TemporaryDirectory() as tmpdirname:
        program1_path = Path(tmpdirname) / "program1.py"
        program2_path = Path(tmpdirname) / "program2.py"

        processed_program1 = deepcopy_crosshair(program1, entry_point).strip()
        processed_program2 = deepcopy_crosshair(program2, entry_point).strip()
        if not processed_program1 or not processed_program2:
            return False

        program1_path.write_text(processed_program1)
        program2_path.write_text(processed_program2)

        try:
            result = subprocess.run(
                [
                    "crosshair",
                    "diffbehavior",
                    "program1.f",
                    "program2.f",
                    "--exception_equivalence",
                    "SAME_TYPE",
                    "--per_condition_timeout",
                    "10",
                ],
                capture_output=True,
                text=True,
                cwd=tmpdirname,
            )
            return result.returncode == 0
        except Exception:
            return "CrosshairError"


def unify_model_name(model_name: str) -> str:
    mapped = {
        "deepseek-chat": "deepseek-v3",
        "deepseek-v3-241226": "deepseek-v3",
        "deepseek-v3-1226": "deepseek-v3",
        "deepseek-v3-241226-deprecated": "deepseek-v3",
        "deepseek-v3-250324": "deepseek-v3",
        "deepseek-reasoner": "deepseek-r1",
        "gpt-4o-2024-11-20": "gpt-4o",
        "gpt-4o-mini-2024-07-18": "gpt-4o-mini",
        "o4-mini-2025-04-16": "o4-mini",
    }
    base_name = model_name.split("/")[-1].lower()
    return mapped.get(base_name, base_name)


@dataclass(frozen=True)
class MetricConfig:
    message: str
    original_path: NestedPath
    repaired_path: NestedPath
    predicate: Optional[Predicate] = None
    fallback_to_original: bool = False
    independent: bool = False


def _always_true(_: JsonDict) -> bool:
    return True


def _has_repaired_requirement(result: JsonDict) -> bool:
    return result.get("repaired_requirement") is not None


def _get_nested_value(item: JsonDict, path: NestedPath) -> Optional[Any]:
    current: Any = item
    for key in path:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(key)
        else:
            current = getattr(current, key, None)
    return current


def _collect_aligned_values(results: Iterable[JsonDict], config: MetricConfig) -> Tuple[List[float], List[float]]:
    predicate = config.predicate or _always_true
    originals: List[float] = []
    repaired: List[float] = []

    for result in results:
        if not predicate(result):
            continue
        original_value = _get_nested_value(result, config.original_path)
        if original_value is None:
            continue
        repaired_value = _get_nested_value(result, config.repaired_path)
        if repaired_value is None and not config.fallback_to_original:
            continue
        originals.append(original_value)
        repaired.append(original_value if repaired_value is None else repaired_value)
    return originals, repaired


def _collect_independent_values(
    results: Iterable[JsonDict], config: MetricConfig
) -> Tuple[List[float], List[float]]:
    predicate = config.predicate or _always_true
    originals: List[float] = []
    repaired: List[float] = []

    for result in results:
        if not predicate(result):
            continue
        original_value = _get_nested_value(result, config.original_path)
        if original_value is not None:
            originals.append(original_value)
        repaired_value = _get_nested_value(result, config.repaired_path)
        if repaired_value is not None:
            repaired.append(repaired_value)
    return originals, repaired


def _summarize_metric(original_values: List[float], repaired_values: List[float], message: str) -> MetricResult:
    if not original_values:
        raise ValueError(f"No original values available for metric '{message}'.")
    if not repaired_values:
        raise ValueError(f"No repaired values available for metric '{message}'.")

    original_mean = mean(original_values)
    repaired_mean = mean(repaired_values)
    improvement = repaired_mean - original_mean
    print(message.format(original=original_mean, repaired=repaired_mean, improvement=improvement))
    return original_mean, repaired_mean, improvement


def _compute_metric(results: Iterable[JsonDict], config: MetricConfig) -> MetricResult:
    collector = _collect_independent_values if config.independent else _collect_aligned_values
    original_values, repaired_values = collector(results, config)
    return _summarize_metric(original_values, repaired_values, config.message)


_METRIC_CONFIGS: Dict[str, MetricConfig] = {
    "entropy": MetricConfig(
        message="original entropy: {original}, repaired entropy: {repaired}, Improvement: {improvement}",
        original_path=("original_clusters", "entropy"),
        repaired_path=("repaired_clusters", "entropy"),
        fallback_to_original=True,
    ),
    "entropy_amb": MetricConfig(
        message="AMBIGUOUS original entropy: {original}, repaired entropy: {repaired}, Improvement: {improvement}",
        original_path=("original_clusters", "entropy"),
        repaired_path=("repaired_clusters", "entropy"),
        predicate=_has_repaired_requirement,
        independent=True,
    ),
    "passk": MetricConfig(
        message="original pass@1: {original}, repaired pass@1: {repaired}, Improvement: {improvement}",
        original_path=("result", "original_passk"),
        repaired_path=("result", "repaired_passk"),
        fallback_to_original=True,
    ),
    "passk_amb": MetricConfig(
        message="AMBIGUOUS original pass@1: {original}, repaired pass@1: {repaired}, Improvement: {improvement}",
        original_path=("result", "original_passk"),
        repaired_path=("result", "repaired_passk"),
        predicate=_has_repaired_requirement,
    ),
    "pass_rate": MetricConfig(
        message="original pass rate: {original}, repaired pass rate: {repaired}, Improvement: {improvement}",
        original_path=("result", "original_pass_rate"),
        repaired_path=("result", "repaired_pass_rate"),
        fallback_to_original=True,
    ),
    "pass_rate_amb": MetricConfig(
        message="AMBIGUOUS original pass rate: {original}, repaired pass rate: {repaired}, Improvement: {improvement}",
        original_path=("result", "original_pass_rate"),
        repaired_path=("result", "repaired_pass_rate"),
        predicate=_has_repaired_requirement,
    ),
    "passk_gt0": MetricConfig(
        message="original pass@1 bigger than 0: {original}, repaired pass@1 bigger than 0: {repaired}, Improvement: {improvement}",
        original_path=("result", "original_passk_bigger_than_0"),
        repaired_path=("result", "repaired_passk_bigger_than_0"),
        fallback_to_original=True,
    ),
    "passk_gt0_amb": MetricConfig(
        message="AMBIGUOUS original pass@1 bigger than 0: {original}, repaired pass@1 bigger than 0: {repaired}, Improvement: {improvement}",
        original_path=("result", "original_passk_bigger_than_0"),
        repaired_path=("result", "repaired_passk_bigger_than_0"),
        predicate=_has_repaired_requirement,
    ),
    "majority": MetricConfig(
        message="original solved with majority vote: {original}, repaired solved with majority vote: {repaired}, Improvement: {improvement}",
        original_path=("result", "original_solved_with_majority_vote"),
        repaired_path=("result", "repaired_solved_with_majority_vote"),
        fallback_to_original=True,
    ),
    "majority_amb": MetricConfig(
        message="AMBIGUOUS original solved with majority vote: {original}, repaired solved with majority vote: {repaired}, Improvement: {improvement}",
        original_path=("result", "original_solved_with_majority_vote"),
        repaired_path=("result", "repaired_solved_with_majority_vote"),
        predicate=_has_repaired_requirement,
    ),
}


def count_entropy(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["entropy"])


def count_entropy_ambiguous(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["entropy_amb"])


def count_passk(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["passk"])


def count_passk_ambiguous(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["passk_amb"])


def count_pass_rate(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["pass_rate"])


def count_pass_rate_ambiguous(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["pass_rate_amb"])


def count_passk_bigger_than_0(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["passk_gt0"])


def count_passk_bigger_than_0_ambiguous(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["passk_gt0_amb"])


def count_solved_with_majority_vote(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["majority"])


def count_solved_with_majority_vote_ambiguous(results: Iterable[JsonDict]) -> MetricResult:
    return _compute_metric(results, _METRIC_CONFIGS["majority_amb"])


_RQ1_SUMMARY_ORDER: List[Tuple[str, str]] = [
    ("passk", "pass@1"),
    ("passk_amb", "pass@1 ambiguous"),
    ("pass_rate", "pass rate"),
    ("pass_rate_amb", "pass rate ambiguous"),
    ("passk_gt0", "pass@1 > 0"),
    ("passk_gt0_amb", "pass@1 > 0 ambiguous"),
    ("majority", "majority vote"),
    ("majority_amb", "majority vote ambiguous"),
    ("entropy", "entropy"),
    ("entropy_amb", "entropy ambiguous"),
]


def _average_metric(values: Iterable[MetricResult]) -> MetricResult:
    items = list(values)
    if not items:
        raise ValueError("No metrics collected to average.")
    count = len(items)
    original = sum(item[0] for item in items) / count
    repaired = sum(item[1] for item in items) / count
    improvement = sum(item[2] for item in items) / count
    return original, repaired, improvement


def count_rq1(label: str, model: str, dataset: str) -> None:
    metrics: Dict[str, List[MetricResult]] = {name: [] for name, _ in _RQ1_SUMMARY_ORDER}
    base_dir = Path(label) / model
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {base_dir}")

    for subdir in sorted(base_dir.iterdir()):
        if subdir.name.startswith("."):
            continue
        results_path = subdir / f"{dataset}.jsonl"
        if not results_path.is_file():
            continue
        results = read_jsonl(str(results_path))
        print(f"{model} {dataset} {subdir.name}")
        for name, _ in _RQ1_SUMMARY_ORDER:
            metrics[name].append(_compute_metric(results, _METRIC_CONFIGS[name]))

    print("====================OVERALL RESULTS====================")
    for name, label_name in _RQ1_SUMMARY_ORDER:
        original, repaired, improvement = _average_metric(metrics[name])
        print(
            f"{label_name}: original = {original}, repaired = {repaired}, improvement = {improvement}"
        )


def count_rq2(label: str, model: str, dataset: str) -> None:
    def read_results(base_dir: str) -> List[JsonDict]:
        root = Path(base_dir) / model
        if not root.is_dir():
            return []
        items: List[JsonDict] = []
        for sub in sorted(root.iterdir()):
            if sub.name.startswith("."):
                continue
            path = sub / f"{dataset}.jsonl"
            if path.is_file():
                items.extend(read_jsonl(str(path)))
        return items

    def print_summary(orig: List[float], rep1: List[float], rep2: List[float], name1: str) -> None:
        if not orig or not rep1 or not rep2:
            raise ValueError(f"Incomplete data for {model} {dataset} {name1}")
        print(
            f"{model} {dataset} "
            f"original passk: {mean(orig):.4f}, "
            f"{name1} passk: {mean(rep1):.4f}, "
            f"specfix passk: {mean(rep2):.4f}"
        )

    def align_triplicated_metrics(
        original: List[Optional[float]],
        repaired_first: List[Optional[float]],
        repaired_second: List[Optional[float]],
    ) -> Tuple[List[float], List[float], List[float]]:
        orig_len = len(original) // 3
        first_len = len(repaired_first) // 3
        second_len = len(repaired_second) // 3

        segments = zip(
            original[:orig_len],
            repaired_first[:first_len],
            repaired_first[first_len : 2 * first_len],
            repaired_first[2 * first_len : 3 * first_len],
            repaired_second[:second_len],
            repaired_second[second_len : 2 * second_len],
            repaired_second[2 * second_len : 3 * second_len],
        )

        filtered = [
            (o, a, b, c, d, e, f)
            for o, a, b, c, d, e, f in segments
            if None not in (o, a, b, c, d, e, f)
        ]
        if not filtered:
            return [], [], []

        orig_vals, a_vals, b_vals, c_vals, d_vals, e_vals, f_vals = map(list, zip(*filtered))
        return orig_vals, a_vals + b_vals + c_vals, d_vals + e_vals + f_vals

    if label == "vanilla":
        original_items = read_jsonl(
            f"experiment/original_result/original_result/{model}/{dataset}.jsonl"
        )
        original_map = {item["task_id"]: item for item in original_items}
        vanilla_items = read_jsonl(
            f"experiment/vanilla_repair/vanilla_repair/{model}/20250724200225/{dataset}.jsonl"
        )

        target_ids: List[Any] = []
        for entry in vanilla_items:
            if entry.get("ambiguity") != "Yes":
                continue
            clusters = original_map.get(entry["task_id"], {}).get("original_clusters") or {}
            entropy = clusters.get("entropy", 0)
            weighted_consistency = clusters.get("weighted_test_consistency", 0)
            if entropy > 0 or (0 <= weighted_consistency < 1):
                target_ids.append(entry["task_id"])
        print(len(target_ids))

        original_passk = [
            original_map[task]["result"]["original_passk"] for task in target_ids if task in original_map
        ]
        vanilla_passk = [
            entry["result"]["repaired_passk"] for entry in vanilla_items if entry["task_id"] in target_ids
        ]
        specfix_passk = [
            result["result"]["repaired_passk"]
            for result in read_results("experiment/test_based_repair/entropy_repair")
            if result["task_id"] in target_ids
        ]

        aligned = align_triplicated_metrics(original_passk * 3, vanilla_passk * 3, specfix_passk)
        if all(aligned):
            print_summary(*aligned, name1="vanilla")

    elif label == "clarifygpt":
        clarify_results = read_results("experiment/clarifygpt/clarifygpt_repair")
        filtered = [
            result for result in clarify_results if result.get("original_clusters", {}).get("entropy", 0) > 0
        ]
        original_passk = [result["result"]["original_passk"] for result in filtered]
        clarify_passk = [result["result"]["repaired_passk"] for result in filtered]
        task_ids = list({result["task_id"] for result in filtered})
        print(len(task_ids))
        specfix_passk = [
            result["result"]["repaired_passk"]
            for result in read_results("experiment/test_based_repair/entropy_repair")
            if result["task_id"] in task_ids
        ]
        aligned = align_triplicated_metrics(original_passk, clarify_passk, specfix_passk)
        if all(aligned):
            print_summary(*aligned, name1="clarifygpt")

    elif label == "mufix":
        specfix_results = [
            result
            for result in read_results("experiment/test_based_repair/entropy_repair")
            if result.get("result", {}).get("repaired_passk") is not None
        ]
        task_ids = list({result["task_id"] for result in specfix_results})
        print(len(task_ids))
        specfix_passk = [result["result"]["repaired_passk"] for result in specfix_results]
        original_passk = [result["result"]["original_passk"] for result in specfix_results]
        mufix_results = read_results("experiment/mufix/mufix")
        mufix_passk = [
            result["result"]["repaired_passk"] for result in mufix_results if result["task_id"] in task_ids
        ]
        aligned = align_triplicated_metrics(original_passk, mufix_passk, specfix_passk)
        if all(aligned):
            print_summary(*aligned, name1="mufix")

    else:
        raise ValueError(f"Unknown label: {label}")


def calculate_pass_k(n: int, c: int, k: int) -> float:
    """
    Compute the pass@k metric.

    Args:
        n: Total number of generated samples.
        c: Number of correct samples that pass the tests.
        k: The number of attempts allowed.
    """
    if n <= 0:
        raise ValueError("n must be positive.")
    if c < 0 or c > n:
        raise ValueError("c must be between 0 and n.")
    if k <= 0:
        raise ValueError("k must be positive.")

    if c == 0:
        return 0.0
    if (n - c) < k:
        return 1.0

    prob_no_pass = 1.0
    for i in range(k):
        prob_no_pass *= (n - c - i) / (n - i)
    return 1 - prob_no_pass


def get_exception_list() -> List[List[str]]:
    return [list(exception) for exception in MAJOR_EXCEPTIONS]


def is_significant_large(prob_list: Sequence[float]) -> bool:
    """Return True if the max probability significantly exceeds the second largest."""
    if not prob_list:
        return False
    total = sum(prob_list)
    if total <= 0:
        return False

    normalized = [prob / total for prob in prob_list]
    sorted_probs = sorted(normalized, reverse=True)
    if len(sorted_probs) == 1:
        return True
    max_val, second_max = sorted_probs[0], sorted_probs[1]
    if max_val == second_max:
        return False
    n = len(sorted_probs)
    threshold = second_max * (1 + 1 / (n - 1))
    return max_val > threshold


def count_rq3(label: str, model: str, dataset: str) -> None:
    original_words: List[int] = []
    repaired_words: List[int] = []
    base_dir = Path(label) / model
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {base_dir}")

    for subdir in sorted(base_dir.iterdir()):
        if subdir.name.startswith("."):
            continue
        results_path = subdir / f"{dataset}.jsonl"
        if not results_path.is_file():
            continue
        results = read_jsonl(str(results_path))
        for result in results:
            if result.get("repaired_requirement") is not None:
                original_words.append(len(result["requirement"].split()))
                repaired_words.append(len(result["repaired_requirement"].split()))

    if not original_words or not repaired_words:
        raise ValueError("Insufficient data to count requirement word statistics.")

    original_mean = mean(original_words)
    repaired_mean = mean(repaired_words)
    improvement = (repaired_mean - original_mean) / original_mean if original_mean else float("inf")
    print(
        f"{model} {dataset} original requirement words: {original_mean}, "
        f"repaired requirement words: {repaired_mean}, "
        f"Improvement: {improvement}"
    )


def safe_eval(val: Any) -> Any:
    class ReMatch:
        def __init__(self, span: Tuple[int, int], match: str) -> None:
            self.span = span
            self.match = match

        def __repr__(self) -> str:  # pragma: no cover - debug-only repr
            return f"<re.Match object; span={self.span}, match=<'{self.match}'>"

    def replace_func(match: re.Match) -> str:
        start = int(match.group(1))
        end = int(match.group(2))
        text = match.group(3)
        return f"ReMatch(({start}, {end}), '{text}')"

    try:
        if isinstance(val, str) and "re.Match object" in val:
            pattern = r"<re\.Match object; span=\((\d+),\s*(\d+)\), match=(?:<)?'([^']+)'(?:>)?>"
            val = re.sub(pattern, replace_func, val)
        safe_globals = dict(_SAFE_EVAL_GLOBALS)
        safe_globals["ReMatch"] = ReMatch
        return eval(val, safe_globals)
    except Exception as exc:
        print(f"Error evaluating value: {val}, Error: {exc}")
        return str(val)


def normalize_stdout(stdout: str) -> str:
    return "\n".join(line.rstrip() for line in stdout.replace("\r", "\n").split("\n")).strip()


def summarize_result(
    problem: JsonDict,
    repaired_requirement: Optional[str],
    original_clusters: Any,
    repaired_clusters: Any,
    original_result: JsonDict,
    repaired_result: Optional[JsonDict],
) -> JsonDict:
    def _cluster_attr(cluster_obj: Any, attr: str) -> Optional[Any]:
        if cluster_obj is None:
            return None
        if isinstance(cluster_obj, dict):
            return cluster_obj.get(attr)
        return getattr(cluster_obj, attr, None)

    original_passk = original_result.get("passk")
    repaired_passk = repaired_result.get("passk") if repaired_result else None

    summary: JsonDict = {
        "task_id": problem["task_id"],
        "original_requirement": problem["requirement"],
        "repaired_requirement": repaired_requirement,
        "original_clusters": original_clusters,
        "repaired_clusters": repaired_clusters,
    }

    result_summary: JsonDict = {
        "original_passk": original_passk,
        "original_avg_pass_rate": original_result.get("avg_pass_rate"),
        "original_nzpassk": (original_passk > 0) if original_passk is not None else None,
        "original_majority_passk": original_result.get("majority_passk"),
        "original_entropy": _cluster_attr(original_clusters, "entropy"),
        "repaired_pass_rate": None,
        "repaired_passk": repaired_passk,
        "repaired_avg_pass_rate": None,
        "repaired_nzpassk": (repaired_passk > 0) if repaired_passk is not None else None,
        "repaired_majority_passk": None,
        "repaired_entropy": _cluster_attr(repaired_clusters, "entropy"),
    }

    if repaired_result is not None:
        result_summary.update(
            {
                "repaired_pass_rate": repaired_result.get("pass_rate"),
                "repaired_avg_pass_rate": repaired_result.get("avg_pass_rate"),
                "repaired_majority_passk": repaired_result.get("majority_passk"),
            }
        )

    summary["result"] = result_summary
    return summary
