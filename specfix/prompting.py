instruction_generate_code = "You are an assistant that generates Python code based on requirement."


def prompt_generate_code(requirement, entry_point):
    return f"""
### Question:\n
{requirement}
### Format: You will use the following starter code to write the solution {entry_point} to the problem and enclose your complete code within delimiters.
```python\n# YOUR CODE HERE\n```\n\n
### Answer: (use the provided format with backticks)\n\n
"""


def prompt_generate_code_stdin(requirement):
    return f"""
### Question:\n
{requirement}
### Format: Read the inputs from stdin solve the problem and write the answer to stdout (do not directly test on the sample inputs). Enclose your code within delimiters as follows. Ensure that when the python program runs, it reads the inputs, runs the algorithm and writes output to STDOUT.
```python\n# YOUR CODE HERE\n```\n\n
### Answer: (use the provided format with backticks)\n\n

### Answer: (use the provided format)\n\n'
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


def prompt_generate_test_stdin(requirement, entry_point):
    return f"""
Given a requirement containing a function signature and docstring, your task is to generate inputs to cover all functionalities, including normal cases and corner cases.
Don't output the function name, only the test inputs.
Note that the requirement specifies that the inputs should be provided in standard input format, which means they should be formatted as if they were read from a file or console input.
Think step by step and wrap each test input in <test></test> tags and all test inputs in <tests></tests> tags. 


# Example
## Requirements
def main():\n\"\"\"\nThere are N pieces placed on a number line. Initially, all pieces are placed at distinct coordinates.\r\nThe initial coordinates of the pieces are X_1, X_2, \\ldots, X_N.\r\nTakahashi can repeat the following operation any number of times, possibly zero.\n\nChoose an integer i such that 1 \\leq i \\leq N-3, and let M be the midpoint between the positions of the i-th and (i+3)-rd pieces in ascending order of coordinate.\r\nThen, move each of the (i+1)-th and (i+2)-th pieces in ascending order of coordinate to positions symmetric to M.\r\nUnder the constraints of this problem, it can be proved that all pieces always occupy distinct coordinates, no matter how one repeatedly performs the operation.\n\nHis goal is to minimize the sum of the coordinates of the N pieces.\r\nFind the minimum possible sum of the coordinates of the N pieces after repeating the operations.\n\nInput\n\nThe input is given from Standard Input in the following format:\nN\r\nX_1 X_2 \\ldots X_N\n\nOutput\n\nPrint the minimum possible sum of the coordinates of the N pieces after repeating the operations.\n\nConstraints\n\n\n- 4 \\leq N \\leq 2 \\times 10^5\n- 0 \\leq X_1 < X_2 < \\cdots < X_N \\leq 10^{12}\n- All input values are integers.\n\nSample Input 1\n\n4\r\n1 5 7 10\n\nSample Output 1\n\n21\r\n\nIf Takahashi chooses i = 1, the operation is performed as follows:\n\n- The coordinates of the 1st and 4th pieces in ascending order of coordinate are 1 and 10, so the coordinate of M in this operation is (1 + 10)/2 = 5.5.\n- The 2nd piece from the left moves from coordinate 5 to 5.5 + (5.5 - 5) = 6.\n- The 3rd piece from the left moves from coordinate 7 to 5.5 - (7 - 5.5) = 4.\n\nAfter this operation, the sum of the coordinates of the four pieces is 1 + 4 + 6 + 10 = 21, which is minimal. Thus, print 21.\n\nSample Input 2\n\n6\r\n0 1 6 10 14 16\n\nSample Output 2\n\n41\n\"\"\"

## Test inputs

<tests>
<test>4\n1 5 7 10</test>
<test>6\n0 1 6 10 14 16</test>
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


instruction_requirement_repair = "You are an assistant that repairs ambiguous requirements based on the identified ambiguity and analysis."


def prompt_requirement_repair_stdin(requirement, ambiguity, analysis, specified_programs,
                                    diff_outputs):
    tests_str = ""
    for i, diff_output in enumerate(diff_outputs):
        if not ('inputs' in diff_output and 'expected' in diff_output):
            continue
        inp = diff_output['inputs'][1:-1]
        exp = diff_output['expected'][1:-1]

        tests_str += (
            f"### Test {i + 1}\n"
            f"Program STDIN:\n{inp}\n"
            f"Expected STDOUT:\n{exp}\n"
        )

    return f"""
You are tasked with repairing ambiguities in code-generation task requirements, which **should** be implemented as a complete program that communicates strictly via STDIN/STDOUT**.
You will precisely repair the ambiguity in the requirement.

Given:
An ambiguous requirement:
{requirement}
Identified ambiguity location(s) that need revision:
{ambiguity}
Step-by-step analysis of the ambiguity and intended fix:
{analysis}
Reference implementation, reflecting the intended behavior (source of truth):
{specified_programs}
I/O examples:
{tests_str}

Your task:
1. Based on the identified ambiguity and the step-by-step analysis, revise the requirement to remove ambiguity, aligning it with the reference implementation and the I/O examples.
2. Ensure that the revised requirement explicitly reflects the intended behavior demonstrated by the reference implementation and the provided input-output examples.
3. Ensure the natural language description of revised requirement is concise.

Important notes:
- **Do NOT change** the examples, assertions, or input/output samples in the original requirement; **KEEP** them unmodified in the revised requirement.
- Don't output corresponding programs, only the revised requirement.
- Based on the revised requirement, the final generated code must be a **standalone program** (not a library) that:
  - Reads from STDIN once (or as specified), processes, and prints to STDOUT.
  - Produces **no extra output** besides the required results.

Output format:
- Provide the **revised requirement** wrapped in <requirement></requirement> tags.
"""


def prompt_requirement_repair(requirement, entry_point, ambiguity, analysis, specified_programs,
                              diff_outputs):
    tests_str = ""
    for i, diff_output in enumerate(diff_outputs):
        if not "inputs" in diff_output or not "expected" in diff_output:
            continue
        tests_str += f"### Test {i + 1}\nInput: {diff_output["inputs"][1:-1]}\nExpected Output: {diff_output["expected"][1:-1]}\n"
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


instruction_fault_localization = "You are an assistant that localizes the ambiguity in the requirement based on differences between reference implementation and incorrect implementations."

def prompt_fault_localization_stdin(requirement, specified_program, programs, diff_outputs):
    programs_str = ""
    for i, (p, diff_output) in enumerate(zip(programs, diff_outputs)):
        if not "inputs" in diff_output or not "outputs" in diff_output or not "expected" in diff_output:
            continue
        programs_str += f"### Incorrect implementation {i}\n{p.strip()}\n"
        programs_str += f"### Test {i}\nProgram STDIN:\n{diff_output["inputs"][1:-1]}\n**Incorrect** implementation {i} output:\n{diff_output["outputs"][1:-1]}\n**Reference** output:\n{diff_output["expected"][1:-1]}\n"

    return f"""
You are provided with:
1. An ambiguous description of a code generation task, which has led to multiple interpretations and consequently different generated implementations.
{requirement}

2. Reference implementation, reflecting the intended behavior.
{specified_program}

3. Incorrect implementations generated from the ambiguous description, demonstrating alternative behaviors.
{programs_str}

Your task is to:
1. Carefully analyze the provided requirement, identifying and clearly stating the specific wording or phrases that could be interpreted in multiple ways.
2. Analyze the reference implementation to determine the intended functionality and expected behavior.
3. Using the input-output examples, note precisely the potential sources of ambiguity that led to the divergence in outputs. Here are potential sources of ambiguity:
    - **Input/output handling** (e.g., format differences, varying data ranges).
    - **Assumptions made** (e.g., implicit constraints or unstated preconditions).

Wrap your identified ambiguity in <ambiguity></ambiguity> tags. Wrap your step-by-step analysis of the identified ambiguity in <analysis></analysis> tags.
"""

def prompt_fault_localization(requirement, entry_point, specified_program, programs, diff_outputs):
    programs_str = ""
    for i, (p, diff_output) in enumerate(zip(programs, diff_outputs)):
        if not "inputs" in diff_output or not "outputs" in diff_output or not "expected" in diff_output:
            continue
        programs_str += f"### Incorrect implementation {i}\n{p.strip()}\n"
        programs_str += f"### Test {i}\nInput:\n{diff_output["inputs"][1:-1]}\n**Incorrect** implementation {i} output:\n{diff_output["outputs"][1:-1]}\n**Reference** output:\n{diff_output["expected"][1:-1]}\n"

    return f"""
You are provided with:
1. An ambiguous description of a code generation task involving the function `{entry_point}`, which has led to multiple interpretations and consequently different generated implementations.
{requirement}

2. Reference implementation, reflecting the intended behavior.
{specified_program}

3. Incorrect implementations generated from the ambiguous description, demonstrating alternative behaviors.
{programs_str}

Your task is to:
1. Carefully analyze the provided requirement, identifying and clearly stating the specific wording or phrases that could be interpreted in multiple ways.
2. Analyze the reference implementation to determine the intended functionality and expected behavior.
3. Using the input-output examples, note precisely the potential sources of ambiguity that led to the divergence in outputs. Here are potential sources of ambiguity:
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


instruction_program_repair = "You are an assistant that repairs program based on the input output examples."


def prompt_program_repair_stdin(requirement, program, failed_input_output_examples):
    formatted_tests = "\n".join(
        f"""
### Test {i + 1}
Input:
{failed_input_output_example["inputs"][1:-1]}
Actual Output:
{failed_input_output_example["outputs"][1:-1]}
Expected Output:
{failed_input_output_example["expected"][1:-1]}
"""
        for i, failed_input_output_example in enumerate(failed_input_output_examples) if
        "inputs" in failed_input_output_example and "outputs" in failed_input_output_example and "expected" in failed_input_output_example
    )
    return f"""
You are provided with:
- An ambiguous requirement that have led to incorrectly generated code.
{requirement}

- Incorrect generated program based on the ambiguous requirement:
{program}

- I/O examples explicitly stated in the requirement and the incorrect output produced by the program:
{formatted_tests}

Your task is to:
1. Carefully analyze the provided requirement, summarize the intended functionality. Identify and clearly state the specific wording or phrases that could be interpreted in multiple ways.
2. Perform a step-by-step execution of the provided program using the explicitly stated input-output examples. At each step, note precisely how the ambiguous wording influenced the program’s logic and behavior. Here are potential sources of ambiguity:
    - **Input/output handling** (e.g., format differences, varying data ranges).
    - **Assumptions made** (e.g., implicit constraints or unstated preconditions).
3. Compare the incorrect execution trace with the intended functionality. Repair the incorrect program to align with the correct output.

Do NOT output any explanation or analysis, only the repaired Python program, wrapped in code fences.
Ensure that when the repaired python program runs, it reads the inputs, runs the algorithm and writes output to STDOUT.
```python\n# YOUR CODE HERE\n```\n\n
"""


def prompt_program_repair(requirement, entry_point, program, failed_input_output_examples):
    formatted_tests = "\n".join(
        f"""
    ### Test {i + 1}
    Input:
    {failed_input_output_example["inputs"][1:-1]}
    Actual Output:
    {failed_input_output_example["outputs"][1:-1]}
    Expected Output:
    {failed_input_output_example["expected"][1:-1]}
    """
        for i, failed_input_output_example in enumerate(failed_input_output_examples) if
        "inputs" in failed_input_output_example and "outputs" in failed_input_output_example and "expected" in failed_input_output_example
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

Format your repaired program with original function signature with type hints, wrapped in code fences.

```python
def function_name(argument: type hint) -> return type hint:
    \"\"\"Repaired program\"\"\"
```
"""
