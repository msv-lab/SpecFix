import random
import types
import re
from specfix.prompting import instruction_check_code_generation, prompt_check_code_generation
from specfix.solution_transformer import remove_comments_and_asserts


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
            target_func = [f for f in local_env.values() if isinstance(f, types.FunctionType)]
            if len(target_func) == 1:
                func = target_func[0]
            else:
                func = random.choice(target_func)
        return func(*func_args)
    except Exception as e:
        return repr(e)


def execute_inputs(func_str, inputs_list, entry_point):
    results = []
    for inputs in inputs_list:
        results.append(execute(func_str, inputs, entry_point))
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


def check_discrepancy(requirement, programs, inp, outputs, model):
    """
    Check discrepancy between the program and the requirement. Return true if the requirement is ambiguous. Return false if the program is incorrectly implemented.
    """
    print("CHECK DISCREPANCY")
    program = ""
    for i, p in enumerate(programs):
        program += "### Program " + str(i) + "\n" + p + "\n"
    output = ""
    for i, o in enumerate(outputs):
        output += "### Output " + str(i) + "\n" + repr(o) + "\n"
    response = model.get_response(instruction_check_code_generation,
                                  prompt_check_code_generation(requirement, program, inp, output))
    answer = unwrap(response, "answer")
    explanation = unwrap(response, "explanation")
    return answer, explanation


def unwrap(string, label):
    string = string.split(f"<{label}>", 1)[1].split(f"</{label}>")[
        0].strip() if f"<{label}>" in string and f"</{label}>" in string and string.index(f"<{label}>") < string.index(
        f"</{label}>") else string
    if "```" in string:
        string = post_process(string)
    if label == "code":
        try:
            string = remove_comments_and_asserts(string).strip()
        except:
            return ""
    return string


def construct_requirement(requirement, starter_code):
    return f"{starter_code}\"\"\"\n{requirement}\n\"\"\""
