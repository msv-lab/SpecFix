instruction_generate_code = "You are an assistant that generates Python code based on requirement. Do not wrap any text in triple backticks such as ```python or ```."


def prompt_generate_code(requirement):
    return f"""
Implement a python function that adheres to the requirements. Do NOT output any explanation. Here is an example:
# Example

## Requirements

Write a function that computes the square of a given number.

## Program

def f(x):
    return x ** 2


# Your task

## Requirement

{requirement}

## Program
"""


instruction_generate_clarifying_question = "You are an assistant that asks clarifying questions based on requirements."


def prompt_generate_clarifying_question(requirement):
    return f"""    
Given requirements, find the discrepancies between requirements and ask questions to clarify. Do NOT output any explanation. Here is an example:

# Example

## Requirements

Requirement 1: Write a function that sorts array while removing the consecutive duplicates.
Requirement 2: Write a function that removes consecutive duplicates while sorting array.

## Clarifying Questions

1. What is the order of the sort and duplicate removal?

# Your task

## Requirement

{requirement}

## Clarifying Questions
"""


instruction_generate_clarifying_question_DRS = "You are an assistant that asks clarifying questions based on Discourse Representation Structures(DRS)."


def prompt_generate_clarifying_question_DRS(requirement, DRS_list):
    drs_str = ""
    for i, drs in enumerate(DRS_list):
        drs_str += f"### DRS {i + 1}\n {drs}\n"
    return f"""
Clarifying the requirement by asking clarifying questions based on Discourse Representation Structures(DRS). Do NOT output any explanation. Here is an example:
# Example

## Requirements

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

## Clarifying Questions

1. What is the order of the sort and duplicate removal?

# Your task

## Requirement

{requirement}

## DRS
{drs_str}

## Clarifying Questions
"""


instruction_repair_requirement = "You are an assistant that repairs requirements based on clarifying questions and answers."


def prompt_repair_requirement(requirement, q_a):
    return f"""
Given the clarifying question and corresponding answer, repair the requirements. Do NOT output any explanation. Here is an example:
# Example

## Requirements

Write a function that sorts array while removing the consecutive duplicates.

## Question and Answer

1. What is the order of the sort and duplicate removal?
- The order is to remove duplicates first and then sort the array.

## Repaired Requirements

Write a function that removes all consecutive duplicates in the given array and then sorts the array.

# Your task

## Requirement

{requirement}

## Question and Answer
{q_a}

## Repaired Requirements
"""


instruction_generate_test = "You are an assistant that generates Python code inputs based on requirement. Do not wrap any text in triple backticks such as ```python or ```."


def prompt_generate_test(requirement):
    return f"""
Given the requirement, generate inputs to cover all functional aspects, including normal cases, edge cases, and error handling. Save the input for one function as a list, then combine all lists into a single collection. Do not generate null or empty inputs. Do NOT output any explanation. Here is an example:

# Example

## Requirements

Write a function that sorts string while removing the consecutive duplicates.

## Test inputs

[["1234567"], ["123123"], ["1122334455"], ["5432112345"], ["000000000"]]

# Your task

## Requirement

{requirement}

## Test inputs
"""


instruction_minimize_requirement = "You are an assistant that minimizes requirements based on the functionality."


def prompt_minimize_requirement(requirement):
    return f"""
Given the requirement, minimize the requirements while keeping the functionality intact. Do NOT output any explanation. Here is an example:

# Example
    
## Requirements
    
- Input: A string `s` containing words separated by spaces.
- Output: A string with the individually reversed words.
- The function should preserve the original spacing between words only as a single space between words in the output.
- Leading and trailing spaces in the input string should be ignored.

# Minimized Requirements

Write a function to individually reverse words in a given string.

# Your task

## Requirement

{requirement}

## Minimized Requirements
"""


instruction_generate_requirement = "You are an assistant who reads code and generates requirements. "


def prompt_generate_requirement(program):
    return f"""
Write a detailed problem description based on the solution source code. Do NOT output any explanation. Here is an example:
# Example

## Program

def f(x):
    return x ** 2
    
## Problem description    

Write a function that computes the square of a given number.

# Your task

## Program

{program}

## Problem Description
"""


instruction_generate_DRS = "You are an assistant that generates Discourse Representation Structures based on requirement."


def prompt_generate_DRS(requirements):
    return f"""
Given the requirements, generate the corresponding Discourse Representation Structures, a way to represent the meaning of natural language sentences and their relationships in a structured formalism. "##########" are used as intervals between different DRS. Do NOT output any explanation. Here is an example:

# Example

## Requirements

Requirement 1: Write a function that sorts array while removing the consecutive duplicates.
Requirement 2: Write a function that removes consecutive duplicates while sorting array.

## DRS

x, y, z, t1, t2
program(x), array(y), duplicates(z), consecutive(z)
t1 < t2,
removes(x, z, y, t1), sorts(x, y, t2)
##########
x, y, z, t1, t2
program(x), array(y), duplicates(z), consecutive(z)
t1 < t2,
sorts(x, y, t1), removes(x, z, y, t2)

# Your task

## Requirement

{requirements}

## DRS
"""


instruction_simulated_answer = "You are an assistant that answers clarifying questions based on the requirement, program, and tests."


def prompt_simulated_answer(requirement, program, tests, question):
    return f""" 
You will be given a user requirement, reference program and its test cases. Your task is to answer some clarifying questions about the requirement using the information. Do NOT output any explanation.

# Example

## Requirement

Write a function to reverse words in a given string.

## Program

def reverse_words(s): 
    return ' '.join(reversed(s.split()))
    
## Tests

[
    "assert reverse_words(\"python program\")==(\"program python\")",
    "assert reverse_words(\"java language\")==(\"language java\")",
    "assert reverse_words(\"indian man\")==(\"man indian\")"
]

## Questions

1. Should the words be reversed individually or the whole string?
2. Should the blank spaces be preserved?

## Answer
1. Should the words be reversed individually or the whole string?
- The words should be reversed individually.
2. Should the blank spaces be preserved?
- Yes, the blank spaces should be preserved.

# Your task

## Requirement

{requirement}

## Program

{program}

## Tests

{tests}

## Questions

{question}

## Answer
"""


instruction_execute_requirement = "You are an assistant that generates the corresponding output based on the requirement and input."


def prompt_execute_requirement(requirement, inp):
    return f"""
Given a problem requirement and an input, generate the corresponding output. Describe step by step that how to get output from input. Output and description are separated by "==========Description==========". Here is an example:

# Example

## Requirement

Write a function that sorts array while removing the consecutive duplicates.

## Input

[2, 2, 3, 3, 3, 1, 1, 4, 4, 4, 4]

## Output

[1, 2, 3, 4]
==========Description==========
1. Remove consecutive duplicates from the array. [2, 3, 1, 4]

2. Sort the array. [1, 2, 3, 4]

# Your task

## Requirement

{requirement}

## Input

{inp}

## Output
"""


instruction_generate_clarifying_question_probe = "You are an assistant that generates clarifying questions based on execution probe."


def prompt_generate_clarifying_question_probe(requirement, probe):
    probe_str = ""
    for i, c in enumerate(probe):
        probe_str += f"### Probe {i + 1}\n {c}\n"

    return f"""
Clarifying the requirement by asking clarifying questions based on the execution probe. Do NOT output any explanation. Here is an example:

# Example

## Requirements

Write a function that sorts array while removing the consecutive duplicates.

## COT

### Probe 1

1. Remove consecutive duplicates from the array. [2, 3, 1, 4]

2. Sort the array. [1, 2, 3, 4]

### Probe 2

1. Sort the array. [1, 2, 3, 4]

2. Remove consecutive duplicates from the array. [1, 2, 3, 4]

## Clarifying Questions

1. What is the order of the sort and duplicate removal?

# Your task

## Requirement

{requirement}

## Probe

{probe_str}

## Clarifying Questions
"""


instruction_check_code_generation = "You are an assistant that checks the generated code based on the requirement."


def prompt_check_code_generation(requirement, program, inputs, outputs):
    return f"""
Given the requirement, LLM generate several programs, which output different results under same inputs. Your task is to judge whether the output discrepancy is due to ambiguous requirement. Ambiguous requirement indicates that the requirement can be interpreted in different ways.  Output "Yes" for discrepancy is due to ambiguous requirement; output "No" for discrepancy isn't due to ambiguous requirement. Here is an example:

# Example

## Requirement

Write a function that sorts array while removing the consecutive duplicates.

## Program

### Program 1

def sort_remove_consecutive_duplicates(arr):
    return sorted(set(arr), key=arr.index)
    
### Program 2

def sort_remove_consecutive_duplicates(arr):
    return [v for i, v in enumerate(sorted(arr)) if i == 0 or v != arr[i-1]]
    
## Inputs

[5, 2, 3, 2, 3]

## Outputs

### Output 1

[5, 2, 3]

### Output 2

[2, 2, 3, 5]

## Judgement

Yes

## Your task

## Requirement

{requirement}

## Program

{program}

## Inputs

{inputs}

## Outputs

{outputs}

## Judgement
"""
