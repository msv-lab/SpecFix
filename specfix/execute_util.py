import ast
import sys
import faulthandler
import platform
import multiprocessing
from datetime import datetime
import signal
from io import StringIO
from unittest.mock import patch, mock_open
from types import ModuleType
from enum import Enum
from decimal import Decimal
from typing import Any, Callable, List, Optional, Sequence, Tuple, Union
import time
import re

# ---------------------------------------------------------------------
# Pre-import string injected into user code
# ---------------------------------------------------------------------
import_string = (
    "from string import *\nfrom re import *\nfrom datetime import *\nfrom collections import *\n"
    "from heapq import *\nfrom bisect import *\nfrom copy import *\nfrom math import *\nfrom random import *\n"
    "from statistics import *\nfrom itertools import *\nfrom functools import *\nfrom operator import *\n"
    "from io import *\nfrom sys import *\nfrom json import *\nfrom builtins import *\nfrom typing import *\n"
    "import string\nimport re\nimport datetime\nimport collections\nimport heapq\nimport bisect\nimport copy\n"
    "import math\nimport random\nimport statistics\nimport itertools\nimport functools\nimport operator\n"
    "import io\nimport sys\nimport json\nsys.setrecursionlimit(50000)\n"
)


# =====================================================================
# Utilities
# =====================================================================

def truncatefn(s: Any, length: int = 300) -> str:
    s = s if isinstance(s, str) else str(s)
    if len(s) <= length:
        return s
    return s[: length // 2] + "...(truncated) ..." + s[-length // 2:]


class CODE_TYPE(Enum):
    call_based = 0
    standard_input = 1


class TimeoutException(Exception):
    """Raised when alarm-based timeout triggers."""
    pass


def timeout_handler(signum, frame):
    # print("timeout occured: alarm went off")  # keep quiet in production
    raise TimeoutException


class Capturing(list):
    """
    Context manager that captures stdout into a single string (at index 0).
    Append-only; preserves previous behavior.
    """

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        # Make closing the StringIO a no-op
        self._stringio.close = lambda x: 1
        return self

    def __exit__(self, *args):
        self.append(self._stringio.getvalue())
        del self._stringio
        sys.stdout = self._stdout


class MockBuffer:
    def __init__(self, inputs: str):
        self.inputs = inputs.encode("utf-8")

    def read(self, *args):
        return self.inputs

    def readline(self, *args):
        return self.inputs.split(b"\n")[0] + b"\n"


class MockStdinWithBuffer:
    """
    Custom mock for sys.stdin that also provides .buffer to satisfy solutions that
    read from sys.stdin.buffer.*.
    """

    def __init__(self, inputs: str):
        self.inputs = inputs
        self._stringio = StringIO(inputs)
        self.buffer = MockBuffer(inputs)

    def read(self, *args):
        return self.inputs

    def readline(self, *args):
        return self._stringio.readline(*args)

    def readlines(self, *args):
        return self.inputs.split("\n")

    def __getattr__(self, name):
        return getattr(self._stringio, name)


# ---------------------------------------------------------------------
# IPC (de)serialization helpers to avoid pickling errors
# ---------------------------------------------------------------------
def _safe_eval_ipc(val: str):
    """
    Minimal safe eval used inside subprocess to reconstruct certain objects
    that were serialized for IPC (e.g., <re.Match object; span=(s, e), match='...'>).
    Only supports converting such tokens (optionally nested in list/dict literals)
    back into lightweight ReMatch objects.
    """

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

    # Support both match='text' and match=<'text'> forms
    pattern = r"<re\.Match object; span=\((\d+),\s*(\d+)\), match=(?:<)?'([^']+)'(?:>)?>"
    if "re.Match object" in val:
        val = re.sub(pattern, replace_func, val)
    # Very small eval environment
    env = {
        "ReMatch": ReMatch,
        "None": None,
        "True": True,
        "False": False,
    }
    return eval(val, env)  # noqa: S307 (controlled inputs from our own serializer)


def _deserialize_ipc(obj):
    """
    Recursively deserialize objects that were normalized for IPC back into
    usable Python objects inside the subprocess.
    """
    if isinstance(obj, str):
        s = obj.strip()
        # Heuristic: looks like a list/dict/tuple literal or a ReMatch token
        if s.startswith("[") or s.startswith("{") or s.startswith("(") or "<re.Match object" in s or s.startswith(
                "ReMatch("):
            try:
                return _safe_eval_ipc(s)
            except Exception:
                return obj
        return obj
    if isinstance(obj, list):
        return [_deserialize_ipc(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_deserialize_ipc(x) for x in obj)
    if isinstance(obj, set):
        return set(_deserialize_ipc(x) for x in obj)
    if isinstance(obj, dict):
        return {_deserialize_ipc(k): _deserialize_ipc(v) for k, v in obj.items()}
    return obj


def _serialize_ipc(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, getattr(re, 'Match', ())):  # type: ignore[arg-type]
        try:
            sp = obj.span()
            mt = obj.group(0)
            return f"<re.Match object; span=({sp[0]}, {sp[1]}), match='{mt}'>"
        except Exception:
            return str(obj)
    if hasattr(obj, 'span') and hasattr(obj, 'match') and obj.__class__.__name__ in {"ReMatch", "SafeReMatch"}:
        try:
            sp = obj.span if isinstance(obj.span, (tuple, list)) else tuple(obj.span)
            mt = obj.match
            return f"<re.Match object; span=({sp[0]}, {sp[1]}), match='{mt}'>"
        except Exception:
            return str(obj)
    if isinstance(obj, tuple):
        return [_serialize_ipc(x) for x in obj]
    if isinstance(obj, list):
        return [_serialize_ipc(x) for x in obj]
    if isinstance(obj, set):
        return sorted([_serialize_ipc(x) for x in obj], key=lambda x: str(x))
    if isinstance(obj, dict):
        return {str(_serialize_ipc(k)): _serialize_ipc(v) for k, v in obj.items()}
    return str(obj)


def clean_if_name(code: str) -> str:
    """Remove a trailing `if __name__ == '__main__':` block if present."""
    try:
        astree = ast.parse(code)
        last_block = astree.body[-1]
        if isinstance(last_block, ast.If):
            condition = last_block.test
            if ast.unparse(condition).strip() == "__name__ == '__main__'":
                code = ast.unparse(astree.body[:-1]) + "\n" + ast.unparse(last_block.body)  # type: ignore
    except Exception:
        pass
    return code


def make_function(code: str) -> str:
    """
    Wrap arbitrary code (minus imports) into a function `wrapped_function()`,
    preceded by `import_string` and the original import statements.
    """
    try:
        import_stmts = []
        all_other_stmts = []
        astree = ast.parse(code)
        for stmt in astree.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                import_stmts.append(stmt)
            else:
                all_other_stmts.append(stmt)

        function_ast = ast.FunctionDef(
            name="wrapped_function",
            args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=all_other_stmts,
            decorator_list=[],
            lineno=-1,
        )
        main_code = (
                import_string
                + "\n"
                + ast.unparse(import_stmts)  # type: ignore
                + "\n"
                + ast.unparse(function_ast)  # type: ignore
        )
        return main_code
    except Exception:
        # Fallback: return original code unmodified
        return code


def call_method(method: Callable, inputs: Union[str, List[str]]):
    """
    Invoke `method()` with patched stdin/open so solutions can read from input.
    `inputs` may be a single string or list of lines.
    """
    if isinstance(inputs, list):
        inputs = "\n".join(inputs)

    inputs_line_iterator = iter(inputs.split("\n"))
    mock_stdin = MockStdinWithBuffer(inputs)

    @patch("builtins.open", mock_open(read_data=inputs))
    @patch("sys.stdin", mock_stdin)
    @patch("sys.stdin.readline", lambda *args: next(inputs_line_iterator))
    @patch("sys.stdin.readlines", lambda *args: inputs.split("\n"))
    @patch("sys.stdin.read", lambda *args: inputs)
    def _inner_call_method(_method):
        try:
            return _method()
        except SystemExit:
            # Some solutions call sys.exit(); ignore to keep harness alive.
            return None

    return _inner_call_method(method)


def get_function(compiled_sol: Any, fn_name: str):
    try:
        assert hasattr(compiled_sol, fn_name)
        return getattr(compiled_sol, fn_name)
    except Exception:
        return None


def compile_code(code: str, timeout: int):
    """Compile/exec code into a module or a Solution instance (for LeetCode-style code)."""
    signal.alarm(timeout)
    try:
        tmp_sol = ModuleType("tmp_sol", "")
        exec(code, tmp_sol.__dict__)
        if "class Solution" in code:
            compiled_sol = tmp_sol.Solution()
        else:
            compiled_sol = tmp_sol
        assert compiled_sol is not None
        return compiled_sol
    finally:
        signal.alarm(0)


def convert_line_to_decimals(line: str) -> Tuple[bool, List[Decimal]]:
    try:
        decimal_line = [Decimal(elem) for elem in line.split()]
    except Exception:
        return False, []
    return True, decimal_line


def get_stripped_lines(val: str) -> List[str]:
    val = val.strip()
    return [val_line.strip() for val_line in val.split("\n")]


# =====================================================================
# NEW: Output collection (no correctness checks)
# =====================================================================

def _temp_exec_one_input(func_str, inputs, entry_point, timeout, result_list):
    """
    Worker: ensure one result (string/return value) is written for each input.
    """
    try:
        try:
            if hasattr(signal, "SIGALRM"):
                signal.signal(signal.SIGALRM, timeout_handler)
        except Exception:
            pass

        reliability_guard()

        if entry_point:
            outputs, _ = get_execution_output_call_based(
                func_str, inputs, entry_point, timeout=timeout
            )
        else:
            outputs, _ = get_execution_output_stdio(
                func_str, inputs, timeout=timeout
            )

        n = len(inputs)

        # outputs and errors must match the length of inputs; if upstream misaligned, align here as a fallback.
        if len(outputs) != n:
            # Pad missing parts to the required length; default to TimeoutError for safety and distinguishability.
            outputs = list(outputs) + ["TimeoutError"] * (n - len(outputs))
        result_list.extend(outputs[:n])

    except Exception as e:
        # Unhandled exception inside the child process: return the same error type for all inputs.
        n = len(inputs)
        result_list.extend([e.__class__.__name__] * n)


def get_execution_output(
        func_str: str,
        inputs,
        entry_point: str,
        timeout: int = 10,
):
    manager = multiprocessing.Manager()
    result_list = manager.list()

    p = multiprocessing.Process(
        target=_temp_exec_one_input,
        args=(func_str, inputs, entry_point, timeout, result_list),
    )
    p.start()

    p.join(timeout=timeout)
    if p.is_alive():
        # Parent process overall timeout: kill the child process.
        p.kill()

    results = list(result_list)

    n = len(inputs)
    if len(results) < n:
        results.extend(["TimeoutError"] * (n - len(results)))

    return results


def get_execution_output_call_based(
        code: str,
        all_inputs: Sequence[Sequence[Any]],
        fn_name: str,
        timeout: int,
) -> Tuple[List[Any], List[Any]]:
    """
    For each input, return an output (or None) and an error dict; length == len(all_inputs).
    """
    n = len(all_inputs)
    predictions: List[Any] = [None] * n
    errors: List[Any] = [None] * n

    compiled = compile_code(import_string + "\n\n" + code, timeout)
    if compiled is None:
        predictions = ["CompileError" for _ in range(n)]
        errors = ["CompileError" for _ in range(n)]
        return predictions, errors

    method = get_function(compiled, fn_name)
    if method is None:
        predictions = ["FunctionNotFoundError" for _ in range(n)]
        errors = ["FunctionNotFoundError" for _ in range(n)]
        return predictions, errors

    for i, args in enumerate(all_inputs):
        faulthandler.enable()
        signal.alarm(timeout)
        try:
            out = method(*args)
            signal.alarm(0)

            if isinstance(out, tuple):
                out = list(out)
            predictions[i] = out
            errors[i] = None
        except Exception as e:
            signal.alarm(0)
            predictions[i] = None
            # Treat timeout uniformly as TimeoutError; otherwise return the exception class name.
            if "timeoutexception" in repr(e).lower():
                predictions[i] = "TimeoutError"
                errors[i] = "TimeoutError"
            else:
                predictions[i] = e.__class__.__name__
                errors[i] = e.__class__.__name__
        finally:
            faulthandler.disable()
            signal.alarm(0)

    return predictions, errors


def get_execution_output_stdio(
        code: str,
        all_inputs: Sequence[Sequence[Any]],
        timeout: int,
) -> Tuple[List[Any], List[Any]]:
    """
    Same contract as call-based: guarantee equal lengths.
    """
    n = len(all_inputs)
    outputs: List[Optional[str]] = [None] * n
    errors: List[Optional[str]] = [None] * n
    code = make_function(clean_if_name(code))

    compiled = compile_code(code, timeout)
    if compiled is None:
        outputs = ["CompileError" for _ in range(n)]
        errors = ["CompileError" for _ in range(n)]
        return outputs, errors

    method = get_function(compiled, "wrapped_function")
    if method is None:
        outputs = ["FunctionNotFoundError" for _ in range(n)]
        errors = ["FunctionNotFoundError" for _ in range(n)]
        return outputs, errors

    for i, inp in enumerate(all_inputs):
        faulthandler.enable()
        signal.alarm(timeout)
        with Capturing() as cap:
            try:
                call_method(method, inp)
                signal.alarm(0)
                faulthandler.disable()
            except Exception as e:
                signal.alarm(0)
                faulthandler.disable()
                if "timeoutexception" in repr(e).lower():
                    outputs[i] = "TimeoutError"
                    errors[i] = "TimeoutError"
                else:
                    outputs[i] = e.__class__.__name__
                    errors[i] = e.__class__.__name__
                continue

        captured = cap[0] if len(cap) > 0 else ""
        outputs[i] = captured
        errors[i] = None
    return outputs, errors


# =====================================================================
# Graders (now built on top of the output functions above)
# =====================================================================

def grade_call_based(
        code: str,
        all_inputs: Sequence[Sequence[Any]],
        all_outputs: Sequence[Any],
        fn_name: str,
        timeout: int,
):
    predictions, errors = get_execution_output_call_based(
        code=code, all_inputs=all_inputs, fn_name=fn_name, timeout=timeout
    )

    all_results: List[bool] = []
    all_errors: List[dict] = []
    for pred, inp, exp, err in zip(predictions, all_inputs, all_outputs, errors):
        if err:
            all_results.append(False)
            all_errors.append({
                "inputs": truncatefn(inp),
                "outputs": truncatefn([pred]),
                "expected": truncatefn(exp),
            })
            continue

        ok = ([pred] == exp)
        all_results.append(ok)
        if ok:
            all_errors.append({})
        else:
            all_errors.append({
                "inputs": truncatefn(inp),
                "outputs": truncatefn([pred]),
                "expected": truncatefn(exp),
            })

    return all_results, all_errors


def grade_stdio(
        code: str,
        all_inputs: Sequence[Union[str, List[str]]],
        all_outputs: Sequence[List[str]],
        timeout: int,
):
    predictions, errs = get_execution_output_stdio(code=code, all_inputs=all_inputs, timeout=timeout)

    all_results: List[bool] = []
    all_errors: List[dict] = []

    for pred, inp, exp, err in zip(predictions, all_inputs, all_outputs, errs):
        if err:
            all_results.append(False)
            all_errors.append({
                "inputs": truncatefn(inp),
                "outputs": truncatefn([pred]),
                "expected": truncatefn(exp),
            })
            continue

        pred_lines = get_stripped_lines(pred)
        exp_lines = get_stripped_lines(exp[0])

        error_info = {
            "inputs": truncatefn(inp),
            "outputs": truncatefn(pred_lines),
            "expected": truncatefn(exp_lines),
        }

        if len(pred_lines) != len(exp_lines):
            all_results.append(False)
            all_errors.append(error_info)
            continue

        # Compare line-by-line with Decimal fallback
        for idx_line, (p_line, e_line) in enumerate(zip(pred_lines, exp_lines)):
            if p_line == e_line:
                continue

            # Try numeric (Decimal) comparison when not exactly equal
            ok_p, dec_p = convert_line_to_decimals(p_line)
            ok_e, dec_e = convert_line_to_decimals(e_line)
            if ok_p and ok_e and dec_p == dec_e:
                continue

            all_results.append(False)
            all_errors.append(error_info)
            break
        else:
            all_results.append(True)
            all_errors.append({})

    return all_results, all_errors


# =====================================================================
# Orchestration (unchanged behavior)
# =====================================================================

def _temp_run(func_str, inputs, outputs, entry_point, debug, result, metadata_list, timeout):
    # Reconstruct objects that were normalized for IPC
    try:
        inputs = _deserialize_ipc(inputs)
    except Exception:
        pass
    try:
        outputs = _deserialize_ipc(outputs)
    except Exception:
        pass
    res, metadata = run_test(func_str, inputs, outputs, entry_point, debug, timeout)
    result.append(res)
    metadata_list.append(metadata)


def check_correctness(func_str, inputs, outputs, entry_point, timeout=5, debug=False):
    # Normalize inputs/outputs to avoid sending unpicklable objects (e.g., re.Match) to subprocess

    safe_inputs = _serialize_ipc(inputs)
    safe_outputs = _serialize_ipc(outputs)

    manager = multiprocessing.Manager()
    result = manager.list()
    metadata_list = manager.list()
    p = multiprocessing.Process(
        target=_temp_run,
        args=(func_str, safe_inputs, safe_outputs, entry_point, debug, result, metadata_list, timeout),
    )
    p.start()
    p.join(timeout=(timeout + 1) * len(inputs) + 5)
    if p.is_alive():
        p.kill()
    if not result:
        # consider that all tests failed
        result = [[-1 for _ in range(len(inputs))]]
        metadata_list = [{"error_code": -3, "all_error_infos": "global timeout or worker crashed"}]
        if debug:
            print("global timeout")
    return result[0], metadata_list[0]


def run_test(func_str, inputs, outputs, entry_point, debug=False, timeout=5):
    """
    If `entry_point` provided → call-based; else → stdio.
    Returns (results, metadata).
    """
    signal.signal(signal.SIGALRM, timeout_handler)
    reliability_guard()

    if debug:
        print(f"start = {datetime.now().time()}")

    which_type = CODE_TYPE.call_based if entry_point else CODE_TYPE.standard_input
    if debug:
        print(f"loaded input_output = {datetime.now().time()}")

    if debug:
        print(f"loading test code = {datetime.now().time()}")

    if which_type == CODE_TYPE.call_based:
        signal.alarm(timeout)
        try:
            results, metadata = grade_call_based(
                code=func_str,
                all_inputs=inputs,
                all_outputs=outputs,
                fn_name=entry_point,
                timeout=timeout,
            )
            return results, metadata
        except Exception as e:
            return [False] * len(inputs), [e.__class__.__name__] * len(inputs)
        finally:
            signal.alarm(0)

    else:  # standard_input
        signal.alarm(timeout)
        try:
            results, metadata = grade_stdio(
                code=func_str,
                all_inputs=inputs,
                all_outputs=outputs,
                timeout=timeout,
            )
            return results, metadata
        except Exception as e:
            return [False] * len(inputs), [e.__class__.__name__] * len(inputs)
        finally:
            signal.alarm(0)


def reliability_guard(maximum_memory_bytes: Optional[int] = None):
    """
    WARNING: Not a security sandbox. Disables/destructors to reduce risk.
    """
    if maximum_memory_bytes is not None:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (maximum_memory_bytes, maximum_memory_bytes))
        resource.setrlimit(resource.RLIMIT_DATA, (maximum_memory_bytes, maximum_memory_bytes))
        if not platform.uname().system == "Darwin":
            resource.setrlimit(resource.RLIMIT_STACK, (maximum_memory_bytes, maximum_memory_bytes))

    faulthandler.disable()

    import builtins
    builtins.quit = None

    import os
    os.environ["OMP_NUM_THREADS"] = "1"

    # Disable process & filesystem mutators
    os.kill = None
    os.system = None
    os.putenv = None
    os.remove = None
    os.removedirs = None
    os.rmdir = None
    os.fchdir = None
    os.setuid = None
    os.fork = None
    os.forkpty = None
    os.killpg = None
    os.rename = None
    os.renames = None
    os.truncate = None
    os.replace = None
    os.unlink = None
    os.fchmod = None
    os.fchown = None
    os.chmod = None
    os.chown = None
    os.chroot = None
    os.fchdir = None
    os.lchflags = None
    os.lchmod = None
    os.lchown = None
    os.getcwd = None
    os.chdir = None

    import shutil
    shutil.rmtree = None
    shutil.move = None
    shutil.chown = None

    import subprocess
    subprocess.Popen = None  # type: ignore

    __builtins__["help"] = None  # type: ignore

    sys.modules["ipdb"] = None
    sys.modules["joblib"] = None
    sys.modules["resource"] = None
    sys.modules["psutil"] = None
    sys.modules["tkinter"] = None
