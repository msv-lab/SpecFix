instruction_generate_code = "You are an assistant that generates Python code based on requirement."


def prompt_generate_code(requirement, entry_point):
    return f"""
Here is the given programming problem to solve.
{requirement}
Please implement the `{entry_point}` function and make sure that it matches the signature and functionality described in the requirement. 
Ensure to include necessary imports for function signature and function body.
Don't output any explanation or comments, only the function implementation.
Think step by step and wrap all generated code in <code></code> tags.
"""


instruction_generate_test = "You are an assistant that generates Python code inputs based on requirement."


def prompt_generate_test(requirement, entry_point, para_number):
    return f"""
Given a requirement containing a function signature and docstring, your task is to generate inputs for function {entry_point} to cover all functionalities, including normal cases and corner cases.
Ensure the type and number of argument are matching the function signature. In this requirement, the argument number is {para_number}.
Don't output the function name, only the test inputs. If there are multiple arguments, separate them with commas.
Think step by step and wrap each test input in <test></test> tags and all test inputs in <tests></tests> tags. 

# Example
## Requirements

def is_anagram(test, original):
\"\"\"
An **anagram** is the result of rearranging the letters of a word to produce a new word.

**Note:** anagrams are case insensitive

Complete the function to return `true` if the two arguments given are anagrams of each other; return `false` otherwise.
\"\"\"


## Test inputs

<tests>
<test>'listen', 'silent'</test>
<test>'hello', 'llohe'</test>
<test>'LISTEN', 'SILENT'</test>
</tests>

# Your task

## Requirement

{requirement}

## Test inputs
"""


instruction_classification = "You are an assistant that classifies the requirement whether it is ambiguous or not."


def prompt_classification(requirement):
    return f"""
Are the requirement ambiguous, i.e. leave room for multiple reasonable interpretations or contain contradictions, when considering the intended functionality? In your evaluation, consider how the program is expected to handle edge cases like extreme values. Exclude considerations related to handling invalid inputs or addressing aspects unrelated to functionality, such as performance.

1. If the requirement is ambiguous, answer "Yes".
2. If the requirement is unambiguous, answer "No".
4. Provide Your step-by-step reasoning for your judgment.

Format your final response in the following tags:
<answer>Yes or No</answer>
<reasoning>Your step-by-step reasoning</reasoning>

# Requirement
{requirement}
"""


instruction_vanilla_repair = "You are an assistant that repairs ambiguous requirements."


def prompt_vanilla_repair(requirement):
    return f"""
Given an ambiguous requirement, repair the requirement to remove ambiguity. 
{requirement}

Format your final repaired requirement with Python function syntax with type hints and a concise docstring, wrapped in <requirement></requirement> tags. 
<requirement>
def function_name(argument: type hint):->type hint 
        \"\"\"repaired requirement\"\"\"
</requirement>
"""


instruction_program_repair = "You are an assistant that repairs the buggy code based on the failed test cases."


def prompt_program_repair(requirement, entry_point, code, failed_input_output_examples):
    tests = ""
    for i, (inp, output, canonical_output) in enumerate(failed_input_output_examples):
        inp = str(inp)[1:-1]
        output = str(output)[1:-1]
        canonical_output = str(canonical_output)[1:-1]
        tests += f"### Test {i + 1}\nInput: {inp}\nActual Output: {output}\nExpected Output: {canonical_output}\n"
    return f"""
Below is a Python program along with:
1. Task requirement that describes the program {entry_point}'s intended functionality and input/output requirements.
2. The buggy Python code.
3. Failed test cases, including 
    - Input values that produce incorrect output.
    - Actual output produced by the program.
    - Expected (canonical) output.

Your task is to:
• **Analyze** the task requirement carefully to understand the intended behavior of the function.
• **Examine** the provided test cases, comparing the actual output with the expected output to clearly identify the underlying issue(s) such as logic errors, incorrect calculations, edge-case mishandling, or syntax issues.
• **Fix** the Python function, ensuring the revised code passes all the provided test cases by generating the correct outputs.

Requirement:
{requirement}

Buggy Code:
{code}

Failed Test Cases:
{tests}
---

Please return the **repaired Python code**, wrapped in <code></code> tags.
"""


instruction_reverse_requirement = "You are an assistant that repairs ambiguous requirements based on the reference implementation."


def prompt_reverse_requirement(requirement, entry_point, program):
    return f"""
You are provided with:
1. An ambiguous description of a code generation task involving the function `{entry_point}`, which has led to multiple interpretations and consequently different generated implementations.
{requirement}
2. Reference implementation reflecting the intended behavior.
{program}

Your task is to follow these steps:
1. Carefully analyze the provided requirement, identifying and clearly stating the specific wording or phrases that could be interpreted in multiple ways.
2. Analyze the reference implementation to determine the intended functionality and expected behavior.
3. **Revise** the sentences related to functional differences. Ensure the natural language description of revised requirement is concise.

Important notes:
- **Do NOT change** the examples, assertions, input/output samples in the original requirement and **KEEP** them in the revised requirement.
- If the ambiguous requirement contains description of other functions, keep those descriptions in the revised requirement.
- Don't output corresponding programs, only the revised requirement.

Format the requirement explicitly in Python function signature with type hints and a docstring. Enclose your repaired requirement within `<requirement></requirement>` tags as follows:

```
<requirement>
def function_name(argument: type_hint) -> return_type_hint:
    \"\"\"Clearly revised, unambiguous description.\"\"\"
</requirement>
```
"""


instruction_largest_cluster_repair = "You are an assistant that repairs ambiguous requirements based on the identified ambiguity and analysis."


def prompt_largest_cluster_repair(requirement, entry_point, ambiguity, analysis, specified_programs,
                                  diff_outputs):
    tests_str = ""
    for i, diff_output in enumerate(diff_outputs):
        tests_str += f"### Test {i + 1}\nInput: {diff_output[0]}\nExpected Output: {diff_output[2]}\n"
    return f"""
You are tasked with repairing ambiguities in code-generation task requirements involving the function `{entry_point}` that have led to incorrectly generated code.
You will precisely repair the ambiguity in the requirement.

Given:
An ambiguous requirement:
{requirement}
Identified ambiguity location that need revision:
{ambiguity}
Step-by-step analysis:
{analysis}
Reference implementation, reflecting the intended behavior:
{specified_programs}
Input and expected output examples:
{tests_str}

Your task:
1. Based on the identified ambiguity location and step-by-step analysis, revise the requirement to remove ambiguity, aligning with the reference implementation and the expected output. 
2. Ensure that the revised requirement explicitly reflects the intended behavior demonstrated by the reference implementation and the provided input-output examples.
3. Ensure the natural language description of revised requirement is concise.

Important notes:
- **Do NOT change** the examples, assertions, input/output samples in the original requirement and **KEEP** them in the revised requirement.
- If the ambiguous requirement contains description of other functions, keep those descriptions in the revised requirement.
- Don't output corresponding programs, only the revised requirement.

Format the revised requirement explicitly in Python function syntax with type hints and a docstring, wrapped in <requirement></requirement> tags.
"""


instruction_largest_cluster_localization = "You are an assistant that localizes the ambiguity in the requirement based on differences between reference implementation and incorrect implementations."


def prompt_largest_cluster_localization(requirement, entry_point, specified_program, programs, diff_outputs):
    programs_str = ""
    for i, (p, diff_output) in enumerate(zip(programs, diff_outputs)):
        programs_str += f"### Incorrect implementation {i}\n{p}\n"
        programs_str += f"###Test {i}\nInput: {diff_output[0]}\n**Incorrect** implementation {i} output: {diff_output[1]}\n**Reference** output: {diff_output[2]}\n"

    return f"""
You are provided with:
1. An ambiguous description of a code generation task involving the function `{entry_point}`, which has led to multiple interpretations and consequently different generated implementations.
{requirement}
2. Reference implementation, reflecting the intended behavior.
{specified_program}
3. Incorrect implementations generated from the ambiguous description, demonstrating alternative behaviors. The outputs of incorrect implementations differ from reference output.
{programs_str}

Your task is to:
1. Carefully analyze the provided requirement, identifying and clearly stating the specific wording or phrases that could be interpreted in multiple ways.
2. Analyze the reference implementation to determine the intended functionality and expected behavior.
2. Using the input-output examples, note precisely the potential sources of ambiguity that led to the divergence in outputs. Here are potential sources of ambiguity:
    - **Input/output handling** (e.g., format differences, varying data ranges).
    - **Assumptions made** (e.g., implicit constraints or unstated preconditions).

Wrap your identified ambiguity in <ambiguity></ambiguity> tags. Wrap your step-by-step analysis of the identified ambiguity in <analysis></analysis> tags.
"""


instruction_remove_example = "You are an assistant that removes examples from the requirement."


def prompt_remove_example(requirement):
    prompt = f"""
    Remove all examples from the provided programming problem description, including sample inputs/outputs, and standalone example sections (including assertion statement). 
    
    Do not modify, rephrase, or delete any non-example text.
    Don't delete function signature or imports at the beginning of requirement. 
    
    Wrap the modified description in <requirement></requirement> tags.
    
    Here is the given programming requirement:
    {requirement}
    """
    return prompt


instruction_test_based_repair_program = "You are an assistant that repairs program based on the input output examples."


def prompt_test_based_repair_program(requirement, entry_point, program, failed_input_output_examples):
    formatted_tests = "\n".join(
        f"""### Test {i + 1}
        Input: {str(inp)[1:-1]}
        Actual Output: {str(output)[1:-1]}
        Expected Output: {str(canonical_output)[1:-1]}"""
        for i, (inp, output, canonical_output) in enumerate(failed_input_output_examples)
    )
    return f"""
You are provided with:
- An ambiguous requirement involving the function `{entry_point}` that have led to incorrectly generated code.
{requirement}
- Incorrect generated program based on the ambiguous requirement:
{program}
- Input-output examples explicitly stated in the requirement and the incorrect output produced by the program:
{formatted_tests}

Your task is to:
1. Carefully analyze the provided requirement, summarize the intended functionality. Identify and clearly state the specific wording or phrases that could be interpreted in multiple ways.
2. Perform a step-by-step execution of the provided program using the explicitly stated input-output examples. At each step, note precisely how the ambiguous wording influenced the program’s logic and behavior. Here are potential sources of ambiguity:
    - **Input/output handling** (e.g., format differences, varying data ranges).
    - **Assumptions made** (e.g., implicit constraints or unstated preconditions).
3. Compare the incorrect execution trace with the intended functionality. Repair the incorrect program to align with the correct output.

Format your repaired program with original function signature with type hints, wrapped in <code></code> tags.

<code>
def function_name(argument: type hint) -> return type hint:
    \"\"\"Repaired program\"\"\"
</code>
"""


instruction_execution_repair = "You are an assistant that repairs ambiguous requirement by analyzing execution."


def prompt_execution_repair(requirement, entry_point, ambiguity, analysis, failed_input_output_examples):
    tests = ""
    for i, (inp, output, canonical_output) in enumerate(failed_input_output_examples):
        inp = str(inp)[1:-1]
        output = str(output)[1:-1]
        canonical_output = str(canonical_output)[1:-1]
        tests += f"### Test {i + 1}\nInput: {inp}\nExpected Output: {canonical_output}\n"

    return f"""
You are tasked with repairing ambiguities in code-generation task requirements involving the function `{entry_point}` that have led to incorrectly generated code.
You will analyze the execution step by step to precisely repair the ambiguity in the requirement.

Given:
An ambiguous requirement:
{requirement}
Identified ambiguity location that need revision:
{ambiguity}
Step-by-step analysis of the execution:
{analysis}
Correct input-output examples explicitly stated in the requirement:
{tests}

Your task:
1. Based on the identified ambiguity location and step-by-step analysis, revise the requirement to remove ambiguity and align with the correct output.
2. Ensure that the revised requirement explicitly reflects the correct behavior demonstrated by the provided input-output examples.
3. Ensure that the revised requirement is concise to reflect the intended functionality.

Important notes:
- **Do NOT change** the examples, assertions, input/output samples in the original requirement and **KEEP** them in the revised requirement.
- If the description contains implementation of other functions, remain those sections unchanged.
- Don't output the implementation, only the requirement.

Format the revised requirement explicitly in Python function syntax with type hints and a docstring, wrapped in <requirement></requirement> tags.
"""


instruction_execution_localization = "You are an assistant that localizes the ambiguity in the requirement based on execution analysis."


def prompt_execution_localization(requirement, entry_point, program, failed_input_output_examples):
    tests = ""
    for i, (inp, output, canonical_output) in enumerate(failed_input_output_examples):
        inp = str(inp)[1:-1]
        output = str(output)[1:-1]
        canonical_output = str(canonical_output)[1:-1]
        tests += f"### Test {i + 1}\nInput: {inp}\nActual Output: {output}\nExpected Output: {canonical_output}\n"
    return f"""
You are tasked with diagnosing ambiguities in code-generation task requirements involving the function `{entry_point}` that have led to incorrectly generated code.

Given:

An ambiguous requirement:
{requirement}

Generated program based on the ambiguous requirement:
{program}

Correct input-output examples explicitly stated in the requirement and the incorrect output produced by the program:
{tests}

Your task:
1. Carefully analyze the provided requirement, summarize the intended functionality. Identify and clearly state the specific wording or phrases that could be interpreted in multiple ways.
2. Perform a step-by-step execution of the provided program using the explicitly stated input-output examples. At each step, note precisely how the ambiguous wording influenced the program’s logic and behavior. Here are potential sources of ambiguity:
    - **Input/output handling** (e.g., format differences, varying data ranges).
    - **Assumptions made** (e.g., implicit constraints or unstated preconditions).
3. Compare the incorrect execution trace with the intended functionality. Clearly pinpoint the exact moment during execution where ambiguity in the requirement caused the deviation from the correct output.

Wrap your identified ambiguity location in <ambiguity></ambiguity> tags. Wrap your step-by-step analysis in <analysis></analysis> tags.
"""


instruction_cluster_localization = "You are an assistant that localizes the ambiguity in the requirement based on the different programs."


def prompt_cluster_localization(requirement, entry_point, programs):
    return f"""
You are provided with:
1. An ambiguous description of a code generation task involving the function `{entry_point}`, which has led to multiple interpretations and consequently different generated implementations.
{requirement}
2. Multiple programs generated from the ambiguous description, demonstrating alternative behaviors.
{programs}

Your task is to:
1. Carefully analyze the provided requirement, summarize the intended functionality, and identify the potential ambiguous phrases that could be interpreted in multiple ways.
2. Analyze the provided programs and summarize the functionality of each implementation. Identify the specific differences in behavior between the programs.
3. Compare the different programs to the requirement and identify the specific phrases or sections that led to the divergence in behavior. Here are potential sources of ambiguity:
    - **Input/output handling** (e.g., format differences, varying data ranges).
    - **Assumptions made** (e.g., implicit constraints or unstated preconditions).

Do not output the implementation, only the requirement.

Wrap your identified ambiguity locations in <ambiguity></ambiguity> tags. Wrap your step-by-step analysis in <analysis></analysis> tags.
"""


instruction_cluster_repair = "You are an assistant that repairs ambiguous requirements based on the identified ambiguity and analysis."


def prompt_cluster_repair(requirement, entry_point, ambiguity, analysis, input_output_examples):
    tests_str = ""
    for i, (inp, output) in enumerate(zip(input_output_examples[0], input_output_examples[1])):
        tests_str += f"### Test {i + 1}\nInput: {str(inp)[1:-1]}\nExpected Output: {str(output)[1:-1]}\n"
    return f"""
You are tasked with repairing ambiguities in code-generation task requirements involving the function `{entry_point}` that have led to incorrectly generated code.
You will precisely repair the ambiguity in the requirement.

Given:
An ambiguous requirement:
{requirement}
Identified ambiguity location that need revision:
{ambiguity}
Step-by-step analysis:
{analysis}

Your task:
1. Based on the original requirement and input-output-examples, using identified ambiguity location and step-by-step analysis, revise the requirement to remove ambiguity and align with the correct output.
2. Ensure that the revised requirement explicitly reflects the correct behavior demonstrated by the provided input-output examples.
3. Ensure the natural language description of revised requirement is concise.

Important notes:
- **Do NOT change** the examples, assertions, input/output samples in the original requirement and **KEEP** them in the revised requirement.
- If the ambiguous requirement contains description of other functions, keep those descriptions in the revised requirement.
- Don't output corresponding programs, only the revised requirement.

Format the revised requirement explicitly in Python function syntax with type hints and a docstring, wrapped in <requirement></requirement> tags.
"""
