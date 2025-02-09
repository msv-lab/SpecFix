instruction_generate_code = "You are an assistant that generates Python code based on requirement."


def prompt_generate_code(requirement):
    return f"""
Implement a python function that adheres to the requirements. Include imports that are used in the implementation. Wrap the generated code in <code></code> tags. Here is an example:
# Example

## Requirement

Write a function that sorts array then removing the consecutive duplicates.

## Code

<code>
def sort_remove_consecutive_duplicates(arr):
    return sorted(set(arr), key=arr.index)
</code>

# Your task

## Requirement

{requirement}

## Code
"""


instruction_find_discrepancy_DRS = "You are an assistant that finds discrepancies between the Discourse Representation Structures(DRS)."


def prompt_find_discrepancy_DRS(requirement, DRS_list):
    drs_str = ""
    for i, drs in enumerate(DRS_list):
        drs_str += f"### DRS {i + 1}\n {drs}\n"
    return f"""
Given requirement and corresponding DRS, find the discrepancies between DRSs. Wrap the discrepancies in the <discrepancy></discrepancy> tags. Here is an example:
# Example

## Requirement

Write a function that sorts array while removing the consecutive duplicates.

## DRS

### DRS 1

x, y, z, t1, t2
program(x), array(y), duplicates(z), consecutive(z)
t1 < t2,
removes(x, z, y, t1), sorts(x, y, t2)

### DRS 2

x, y, z, t1, t2
program(x), array(y), duplicates(z), consecutive(z)
t1 < t2,
sorts(x, y, t1), removes(x, z, y, t2)

## Discrepancy

<discrepancy>
The order of operation (i.e., sort and remove) is different in DRS1 and DRS2. DRS1 specifies to remove duplicates first and then sort the array, while DRS2 specifies to sort the array first and then remove duplicates.
</discrepancy>

# Your task

## Requirement

{requirement}

## DRS
{drs_str}

## Discrepancy
"""


instruction_repair_requirement = "You are an assistant that repairs requirements based on clarifying questions and answers."


def prompt_repair_requirement(requirement, q_a):
    return f"""
Given the clarifying question and corresponding answer, repair the requirements. Wrap the repaired requirement in <requirement></requirement> tags. Here is an example:
# Example

## Requirements

Write a function that sorts array while removing the consecutive duplicates.

## Question and Answer

1. What is the order of the sort and duplicate removal?
- The order is to remove duplicates first and then sort the array.

## Repaired Requirements

<requirement>
Write a function that removes all consecutive duplicates in the given array and then sorts the array.
</requirement>

# Your task

## Requirement

{requirement}

## Question and Answer
{q_a}

## Repaired Requirements
"""


instruction_generate_test = "You are an assistant that generates Python code inputs based on requirement."


def prompt_generate_test(requirement):
    return f"""
Given the requirement, generate inputs to cover all functional aspects, including normal cases, edge cases, and error handling. Store each test case in a list as function input. If an parameter type is list, it is nested inside the outer list. Gather all test cases into a general list. Wrap the collection in <test></test> tags. Here is an example:

# Example

## Requirements

Write a function that sorts a list and select the kth smallest element.

## Test inputs

<test>
[[[1, 2, 3, 2, 3], 2], [[1, 2, 3, 4, 5], 3], [[1, 2, 3, 4, 5], 1]]
</test>

# Your task

## Requirement

{requirement}

## Test inputs
"""


instruction_generate_requirement = "You are an assistant who reads code and generates requirements. "


def prompt_generate_requirement(program):
    return f"""
Write a detailed problem description based on the solution source code. Wrap the generate requirement in <requirement></requirement> tags. Here is an example:
# Example

## Program

def f(x):
    return x ** 2
    
## Problem requirement    

<requirement>
Write a function that computes the square of a given number.
</requirement>

# Your task

## Program

{program}

## Problem requirement
"""


instruction_generate_DRS = "You are an assistant that generates Discourse Representation Structures based on requirement."


def prompt_generate_DRS(requirements):
    return f"""
Given the requirements, generate the corresponding Discourse Representation Structures, a way to represent the meaning of natural language sentences and their relationships in a structured formalism. Wrap the generated DRS in <drs></drs> tags. "##########" are used as intervals between different DRS. Here is an example:

# Example

## Requirements

Requirement 1: Write a function that sorts array while removing the consecutive duplicates.
Requirement 2: Write a function that removes consecutive duplicates while sorting array.

## DRS

<drs>
x, y, z, t1, t2
program(x), array(y), duplicates(z), consecutive(z)
t1 < t2,
removes(x, z, y, t1), sorts(x, y, t2)
##########
x, y, z, t1, t2
program(x), array(y), duplicates(z), consecutive(z)
t1 < t2,
sorts(x, y, t1), removes(x, z, y, t2)
</drs>

# Your task

## Requirement

{requirements}

## DRS
"""


instruction_classification = "You are an assistant that classifies the requirement whether it is ambiguous or not."


def prompt_classification(requirement):
    return f"""
Given a requirement and corresponding code, determine if the requirement is ambiguous. A requirement is considered ambiguous if it can be interpreted in multiple ways due to missing or unclear information (e.g., vague definitions, unspecified relationships, or incomplete instructions). Think step-by-step. Your response should include:

1. If the requirement is ambiguous, answer "Yes".
2. Otherwise, answer "No".
3. Provide Your step-by-step reasoning for your judgment.

Format your final response in the following tags:
<answer>Yes or No</answer>
<reasoning>Your step-by-step reasoning</reasoning>

# Requirement
{requirement}
"""


instruction_vanilla_repair = "You are an assistant that repairs ambiguous requirements."


def prompt_vanilla_repair(requirement):
    return f"""
Given an ambiguous requirement, repair the requirement to remove ambiguity. Wrap the repaired requirement in <requirement></requirement> tags.
{requirement}
"""


instruction_test_based_repair = "You are a programming assistant specialized in debugging and fixing Python code."


def prompt_test_based_repair(requirement, code, failed_semantic_input_output):
    tests = ""
    for i, (inp, output, canonical_output) in enumerate(failed_semantic_input_output):
        tests += f"### Test {i + 1}\nInput: {inp}\nOutput: {output}\nExpected: {canonical_output}\n"
    return f"""
You are a coding assistant specialized in repairing buggy Python programs.

Below is a Python program along with:
1. Task requirement that describes the program's intended functionality and input/output requirements.
2. The buggy Python code.
3. Failed test cases, including 
    - Input values that produce incorrect output.
    - Actual output produced by the program.
    - Expected (canonical) output.

Please:
• Understand the task requirement and python program.
• Compare the actual output with the canonical output to determine why the program is faulty. Identify logical errors, syntax issues, or edge-case handling flaws.
• Provide a corrected version of the Python code that, when run on the given test input, will produce the correct (canonical) output.
• Keep the structure and logic of the original code as much as possible unless changes are necessary for correctness.

---
Requirement:
{requirement}

Buggy Code:
{code}

Failed Test Cases:
{tests}
---

Please return the repaired Python code, wrapped in <code></code> tags.
"""


instruction_inverse_requirement = "You are an assistant that generates a task description based on the Python program."


def prompt_inverse_requirement(program):
    return f"""
You are given a Python program. Your task is to generate a detailed, clear, and concise description of the task the program is designed to perform. The description should include the following:

Purpose: What is the overall goal of the program?
Key Operations: What are the main operations or steps the program performs?
Inputs: What inputs does the program require?
Outputs: What outputs does the program produce?
Expected Behavior: How does the program handle different inputs or conditions? (e.g., any special cases or error handling)
Below is the Python code:
{program}
Please provide a task description of the program is designed to accomplish based on the above criteria, wrapped in <requirement></requirement> tags.
"""


instruction_repair_largest_cluster_requirement = "You are an assistant that repairs the requirement based on the different programs."


def prompt_repair_largest_cluster_requirement(requirement, programs, specified_programs):
    programs_str = ""
    for i, p in enumerate(programs):
        programs_str += f"### Program {i}\n{p}\n"

    return f"""
You are tasked with repairing a programming problem description to ensure it unambiguously leads to a specific code implementation. Below is the original problem description, multiple code versions generated for it, and the target code version I want the LLM to generate. Follow these steps:

1. **Identify Ambiguities:** Analyze the original problem description for ambiguities, missing constraints, or underspecified requirements that allowed for multiple interpretations (leading to different code versions).

2. **Compare Code Differences:** Examine the differences between the target code (SPECIFIED_CODE) and other versions (OTHER_VERSIONS). Highlight divergences in:
   - Input/output handling (e.g., format, data types)
   - Edge cases or error handling (e.g., missing constraints)
   - Assumptions made (e.g., constraints not explicitly stated)

3. **Revise Requirements:** Repair the original problem description by:
   - Adding precise constraints to eliminate alternative approaches seen in OTHER_VERSIONS.
   - Specifying edge cases or input/output formats to match SPECIFIED_CODE.

4. **Output Format:**
   - Repaired Problem Description: A revised problem statement that enforces the target implementation, wrapped in <requirement></requirement> tags.
   - Do not return the code itself—focus solely on repairing the problem description. Prioritize clarity and specificity while preserving the original intent.
---

**Original Problem Description:**
{requirement}

**SPECIFIED_CODE:**
{specified_programs}

**OTHER_VERSIONS:**
{programs_str}
"""



