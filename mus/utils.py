from wrapt_timeout_decorator import *

from .prompting import instruction_check_code_generation, prompt_check_code_generation, instruction_execute_requirement, \
    prompt_execute_requirement


def post_process(content):
    return content.strip().removeprefix("```python").removeprefix("```").strip("`").strip()


@timeout(10)
def execute(func_str, func_args):
    try:
        local_env = {}
        exec(func_str, local_env)
        possible_funcs = [v for v in local_env.values() if callable(v)]
        if not possible_funcs:
            raise "No callable function found in func_str"
        func = possible_funcs[0]
        return func(*func_args)
    except Exception as e:
        return str(e)


def execute_inputs(func_str, inputs_list, timeout=10):
    results = []
    for inputs in inputs_list:
        results.append(execute(func_str, inputs))
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


def execute_requirement(requirement, inp, model):
    print("EXECUTE REQUIREMENT")
    response = model.get_response(instruction_execute_requirement,
                                  prompt_execute_requirement(requirement, inp))
    return response.replace("## Output\n", "").strip()


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
    response = response.replace("## Judgement\n", "").strip()
    return response
