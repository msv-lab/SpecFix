import copy

instruction_generate_code = "You are an assistant that generates Python code based on requirement."


def prompt_generate_code(requirement,entry_point):
    return f"""
Here is the given programming problem to solve.
{requirement}
Please implement the `{entry_point}` function and make sure that it matches the signature and functionality described in the requirement. 
Ensure to include necessary imports.
Don't output any explanation or comments, only the function implementation.
Think step by step and wrap all generated code in <code></code> tags.
"""


instruction_find_discrepancy = "You are an assistant that finds discrepancies between the requirements."


def prompt_find_discrepancy(requirement):
    return f"""    
Given requirements, find the discrepancies between requirements. Wrap the discrepancies in the <discrepancy></discrepancy> tags. Here is an example:

# Example

## Requirements

Requirement 1: Write a function that sorts array then removes the consecutive duplicates.
Requirement 2: Write a function that removes consecutive duplicates while sorting array.

## Discrepancy

<discrepancy>
The requirement1 specifies to remove duplicates first and then sort the array, while requirement2 doesn't specify the order of operations.
</discrepancy>

# Your task

## Requirement

{requirement}

## Discrepancy
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


instruction_minimize_requirement = "You are an assistant that minimizes requirements."


def prompt_minimize_requirement(original_requirement, repaired_requirement):
    return f"""
Given an original requirement and a repaired requirement, minimize the repaired requirements to get a minimal edit distance from original code while keep the functionality of repaired requirement. Wrap the minimized requirement in <requirement></requirement> tags. Here is an example:

# Example

## Original Requirement

Write a function to reverse words in a given string.

## Repaired Requirement
    
- Input: A string `s` containing words separated by spaces.
- Output: A string with the individually reversed words.
- The function should preserve the original spacing between words only as a single space between words in the output.
- Leading and trailing spaces in the input string should be ignored.

# Minimized Requirements

<requirement>
Write a function to individually reverse words in a given string.
</requirement>

# Your task

## Requirement

### Original Requirement

{original_requirement}

### Repaired Requirement

{repaired_requirement}

## Minimized Requirements
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


instruction_generate_clarifying_question = "You are an assistant that generates clarifying questions to clarify the requirement."


def prompt_generate_clarifying_question(requirement, discrepancies):
    return f"""
given the requirement and discrepancies, generate a clarifying question to clarify the requirement. Wrap the generated question in <question></question> tags. Here is an example:

# Example

## Requirement

Write a function that sorts array while removing the consecutive duplicates.

## Discrepancies

Discrepancy 1: The requirement specifies to remove duplicates first and then sort the array.
Discrepancy 2: The requirement doesn't specify the order of operations.

## Clarifying Question

<question>
What is the order of the sort and duplicate removal?
</question>

# Your task

## Requirement

{requirement}

## Discrepancies

{discrepancies}

## Clarifying Question
"""


instruction_simulated_answer = "You are an assistant that answers clarifying questions based on the requirement, program, and tests."


def prompt_simulated_answer(requirement, program, tests, question):
    return f""" 
You will be given a user requirement, reference program and its test cases. Your task is to answer some clarifying questions about the requirement using the information. Wrap the answer in <answer></answer> tags. Here is an example:

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

<answer>
1. Should the words be reversed individually or the whole string?
- The words should be reversed individually.
2. Should the blank spaces be preserved?
- Yes, the blank spaces should be preserved.
</answer>

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


instruction_check_code_generation = "You are an assistant that checks the generated code based on the requirement."


def prompt_check_code_generation(requirement, program, inputs, outputs):
    return f"""
You are given a requirement and several programs that produce different outputs for the same inputs. Your task is to determine if the discrepancy in outputs is caused by an ambiguous requirement. A requirement is considered ambiguous if it can be interpreted in multiple ways due to missing or unclear information (e.g., vague definitions, unspecified relationships, or incomplete instructions).  
  
1. If the output discrepancy arises from an ambiguous requirement, answer "Yes".  
2. Otherwise, answer "No".  
3. Provide a step-by-step explanation for your judgment.  
  
Format your final response in the following tags:  

<answer>Yes or No</answer>
<explanation>Your step-by-step reasoning</explanation>

Use the example below as a reference:
 
# Example 
 
#Requirement
Write a function that sorts an array while removing the consecutive duplicates.
 
## Programs 
 
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

<answer>
Yes
</answer>
<explanation>
Program 1 removes duplicates before sorting, while Program 2 sorts first and then removes duplicates. Since the requirement doesn't specify the sequence of these two operations, the discrepancy is due to an ambiguous requirement.
</explanation>

 
# Your task  
 
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


### Clarify GPT clone prompting
# Note: I have added the tags part of the prompt to the end of each clarify gpt prompt for parsing. 

# instruction_generate_test_clarify_gpt = "You will be given a user requirement containing a function signature and a docstring. Your task is to generate some complex, difficult, or corner-case test inputs for this requirement. Gather all test cases into a general list. Wrap the collection in <test></test> tags."

# _: generate initial code from requirement
def prompt_generate_initial_code_clarify_gpt(requirement):
    print(f"INITIAL CODE GENERATION:")
    
    openai_messages = copy.deepcopy(initial_code_generation_prompt)
    openai_messages.append({
        'role': 'user',
        'content': f'### User Requirement:{requirement}'
                    f'\n\n### Code Solution:\n{{<code>insert answers here.</code>}}'
    })
    
    # print("GENERATE CODE PROMPT\n", openai_messages)
    return openai_messages


# A: generate tests
def prompt_generate_test_clarify_gpt(requirement, n_shot):
    print(f"TEST GENERATION [{n_shot}]:")
    openai_messages = copy.deepcopy(generate_prompt[n_shot])
    openai_messages.append({
        'role': 'user',
        'content': f'### User Requirement:{requirement}'
                    f'\n\n### Test Inputs:\n{{<test>insert here.</test>}}'
    })
    # print("GENERATING TESTS PROMPT\n", openai_messages)
    return openai_messages


# instruction_generate_clarifying_question_clarify_gpt = "You will be given a user requirement and its candidate solutions. Your task is to clarify this requirement by asking clarifying questions. Specifically, you will first analyze the functionality of each solution. Then, by comparing their differences, you can determine which parts in the requirement are ambiguous and ask targeted clarification questions. Wrap the generated questions in <question></question> tags."

# B: Ask clarifying questions
def prompt_generate_clarifying_question_clarify_gpt(requirement, inconsistent_solutions, n_shot):
    print(f"ASK QUESTIONS [{n_shot}]:")
    
    openai_messages = copy.deepcopy(askcq_prompt[n_shot])
    sol_str = ""
    for i, sol in enumerate(inconsistent_solutions):
         sol_str += f"Solution {i}:\n {sol}\n" 
         
    openai_messages.append({
        'role': 'user',
        'content': f'### User Requirement:{requirement}'
                    f'\n### Inconsistent Solutions:\n{sol_str}'
                    f'\n\n### Analysis and Clarifying Questions:\n{{insert here.}}'
    })
    
    # print("ASK QUESTIONS PROMPT: \n", openai_messages)
    return openai_messages


# instruction_repair_requirement_clarify_gpt = "You will be given a user requirement and its test cases. Your task is to answer some clarifying questions using the information provided in the given requirement and tests. Reply only with the answers, do not repeat the code and questions. Wrap the repaired requirement in <requirement></requirement> tags."

# C: Answer questions and repair requirement. Note tests are appended to the requirement in our case. Prompt will be nearly the exact same.
def prompt_repair_requirement_clarify_gpt(requirement, clarifying_questions, n_shot):
    print(f"CLARIFY [{n_shot}]:")
    
    openai_messages = copy.deepcopy(answercq_prompt[n_shot])
    
    openai_messages.append({
        'role': 'user',
        'content': f'### User Requirement:{requirement}'
                    # f'\n\n### Test Cases:{tests}' # No need for this becasue our tests are public in our requirements
                    f'\n\n### Clarifying Questions:{clarifying_questions}'
                    f'\n\n### Answers:\n{{<answers>insert here.</answers>}}'
    })
    
    # print("ANSWER QUESTIONS PROMPT: \n", openai_messages)
    return openai_messages


# instruction_generate_code_clarify_gpt = "You will be given a user requirement containing a function signature and a docstring. Please read the docstring, understand the user's intention, and respond only with a correct, efficient Python function. Do not import libraries other than those provided in the function signature; do not write explanations or assertions; simply provide only the code. Wrap the generated code in <code></code> tags."

# D: Generate code from clarified requirements
def prompt_generate_code_clarify_gpt(requirement, n_shot):
    print(f"CODE GENERATION [{n_shot}]:")
    
    openai_messages = copy.deepcopy(synthesize_prompt[n_shot])
    openai_messages.append({
        'role': 'user',
        'content': f'### User Requirement:{requirement}'
                    f'\n\n### Code Solution:\n{{<code>insert answers here.</code>}}'
    })
    
    # print("GENERATE CODE PROMPT\n", openai_messages)
    return openai_messages

# def prompt_repair_requirement_clarify_gpt(requirement, clarifying_questions):


#     print(f"""
# ### User Requirement:
# {requirement}
# ### Clarifying Questions:
# {clarifying_questions}
# ### Code Solution:
# """)
#     return f"""
# ### User Requirement:
# {requirement}
# ### Clarifying Questions:
# {clarifying_questions}
# ### Code Solution:
# """



initial_code_generation_prompt = [{
    'role': 'system',
    'content': 'You will be given a user requirement.'
                'Strictly follow the function signature provided in the requirement, '
                'Respond only with a correct, efficient Python function. '
                'Do not write explanations or assertions; simply provide only the code. '
                'Wrap the generated code in <code></code> tags.' # I ADDED THIS LINE. NOT ORIGINAL CLARIFYGPT
}]

# NOTE: This is missing from ClarifyGPT's code base, although mentioned in the paper. Do they actually do any test input generation??

generate_prompt = {
    'zero_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement containing a function signature and a docstring. '
                    'Your task is to generate some complex, difficult, or corner-case test inputs for this requirement. '
                    'Gather all test cases into a general list. '
                    'Wrap the collection in <test></test> tags.' # I ADDED THIS LINE. NOT ORIGINAL CLARIFYGPT
         }],
    

    'one_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement containing a function signature and a docstring. '
                    'Your task is to generate some complex, difficult, or corner-case test inputs for this requirement. '
                    'Gather all test cases into a general list. '
                    'Wrap the collection in <test></test> tags.' # I ADDED THIS LINE. NOT ORIGINAL CLARIFYGPT
        },
        {
        'role': 'user',
        'content': '### User Requirement:'
                    '\nimport collections as ct'
                    '\ndef merge_dictionaries_three(dict1,dict2,dict3):'
                    '\n     \" Write a function to merge three dictionaries into a signle dictionary. \"'
                    '\n\n### Test Inputs:\n{{<test>insert here.</test>}}'
        },
        {'role': 'assistant',
         'content': '### Test Inputs:'
                    '\n```<test>\n'
                    '\n['
                    '\n({"a": 1}, {"b": 2}, {"c": 3}),'
                    '\n({"a": 1, "b": 2}, {"b": 3, "c": 4}, {"c": 5, "d": 6}),'
                    '\n({"a": [1, 2]}, {"a": [3, 4], "b": [5]}, {"a": [6], "c": [7, 8]}),'
                    '\n({"a": 1, "b": "hello"}, {"b": [2, 3], "c": {"key": "value"}}, {"d": 3.14, "a": None}),'
                    '\n({}, {}, {}),'
                    '\n({"a": 1}, {}, {"b": 2}),'
                    '\n({"a": {"x": 1}}, {"b": {"y": 2}}, {"c": {"z": 3}, "a": {"w": 4}}),'
                    '\n({f"key{i}": i for i in range(1000)},'
                    '\n{f"key{i}": i * 2 for i in range(500, 1500)},'
                    '\n{f"key{i}": i * 3 for i in range(1000, 2000)}),'
                    '\n({1: "one", (2, 3): "tuple"}, {"1": "str_one", "key": "value"}, {None: "none", False: "false"}),'
                    '\n({"a": True}, {"b": False}, {"c": True, "a": False}),'
                    '\n]'
                    '\n</test>```'
         },
    ],
}

askcq_prompt = {
    'zero_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement and its candidate solutions. '
                    'The user requirement is not clear, leading developers to interpret it differently. '
                    'Thus, the candidate solutions writtent by these developers have different functionalities, and some of them are wrong.'
                    '\nYour task is to clarify this requirement by asking clarifying questions. '
                    'Specifically, you first analyze how each developer understands the requirement. '
                    'Then, by comparing their different understandings of the requirement, '
                    'you can determine which statements in the requirement are not clear, and ask clarification questions for those statements. '
                    'Wrap only the generated questions (and not the analysis) in <question></question> tags.', # I ADDED THIS, NOT CLARIFY GPT
    }],

    'one_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement and its candidate solutions. '
                    'The user requirement is not clear, leading developers to interpret it differently. '
                    'Thus, the candidate solutions writtent by these developers have different functionalities, and some of them are wrong.'
                    '\nYour task is to clarify this requirement by asking clarifying questions. '
                    'Specifically, you first analyze how each developer understands the requirement. '
                    'Then, by comparing their different understandings of the requirement, '
                    'you can determine which statements in the requirement are not clear, and ask clarification questions for those statements.',
        },
        {'role': 'user',
         'content': "User Requirement:"
                    "\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    '''\n    Write a function to merge three dictionaries into a single dictionary.\n    '''"
                    "\nSolution 0:\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    merged_dict = ct.ChainMap(dict1, dict2, dict3)\n    return dict(merged_dict)"
                    "\nSolution 1:\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    return ct.ChainMap(dict1, dict2, dict3)"
                    "\nSolution 2:\ndef merge_dictionaries_three(dict1, dict2, dict3):\n    return {**dict1, **dict2, **dict3}"
         },
        {'role': 'assistant',
         'content': '### Analysis:'
                    '\nThe requirement is to merge three dictionaries into a single dictionary.'
                    '\n\nSolution 0:\n- Solution 0 uses the `ChainMap` class from the `collections` module to merge the dictionaries.\n- It creates a `ChainMap` object with the three input dictionaries and then converts it to a regular dictionary using the `dict()` function.'
                    '\n\nSolution 1:\n- Solution 1 also uses the `ChainMap` class from the `collections` module to merge the dictionaries.\n- It directly returns the `ChainMap` object without converting it to a regular dictionary.'
                    '\n\nSolution 2:\n- Solution 2 merges the dictionaries using the dictionary unpacking operator (`**`).\n- It creates a new dictionary by unpacking the three input dictionaries.'
                    '\n\n### Clarifying Questions:'
                    '\n1. What should be the type of the output? `ChainMap` object or a regular dictionary?'
                    '\n2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?'
                    '\n3. Can you provide an input-output example to help us better understand your requirement?'
         },
    ],

    'two_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement and its candidate solutions. '
                    'The user requirement is not clear, leading developers to interpret it differently. '
                    'Thus, the candidate solutions writtent by these developers have different functionalities, and some of them are wrong.'
                    '\nYour task is to clarify this requirement by asking clarifying questions. '
                    'Specifically, you first analyze how each developer understands the requirement. '
                    'Then, by comparing their different understandings of the requirement, '
                    'you can determine which statements in the requirement are not clear, and ask clarification questions for those statements.',
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\ndef lateralsuface_cylinder(r,h):\n    '''\n    Write a function to find the lateral surface area of a cylinder.\n    '''"
                    "\nSolution 0:\ndef lateralsuface_cylinder(r,h):\n    return 2 * 3.1415 * r * h"
                    "\nSolution 1:\nimport math\ndef lateralsuface_cylinder(r,h):\n    return 2 * math.pi * r * h"
         },
        {'role': 'assistant',
         'content': '### Analysis:'
                    '\nThe requirement is to write a function to find the lateral surface area of a cylinder.'
                    '\n\nSolution 0:\n- Solution 0 calculates the lateral surface area of a cylinder using an approximation of the value of π (approximately 3.1415).\n- It calculates the lateral surface area of a cylinder using the formula: 2 * 3.1415 * r * h.'
                    '\n\nSolution 1:\n- Solution 1 imports the math module and uses the precise value of π from the math module to calculate the lateral surface area of the cylinder.\n- It calculates the lateral surface area of a cylinder using the formula: 2 * π * r * h.'
                    '\n\n### Clarifying Questions:'
                    '\n1. What do the input parameters `r` and `h` mean respectively?'
                    '\n2. Is it acceptable to use an approximation for the value of π, or should the exact value be used?'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    '''\n    Write a function to merge three dictionaries into a single dictionary.\n    '''"
                    "\nSolution 0:\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    merged_dict = ct.ChainMap(dict1, dict2, dict3)\n    return dict(merged_dict)"
                    "\nSolution 1:\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    return ct.ChainMap(dict1, dict2, dict3)"
                    "\nSolution 2:\ndef merge_dictionaries_three(dict1, dict2, dict3):\n    return {**dict1, **dict2, **dict3}"
         },
        {'role': 'assistant',
         'content': '### Analysis:'
                    '\nThe requirement is to merge three dictionaries into a single dictionary.'
                    '\n\nSolution 0:\n- Solution 0 uses the `ChainMap` class from the `collections` module to merge the dictionaries.\n- It creates a `ChainMap` object with the three input dictionaries and then converts it to a regular dictionary using the `dict()` function.'
                    '\n\nSolution 1:\n- Solution 1 also uses the `ChainMap` class from the `collections` module to merge the dictionaries.\n- It directly returns the `ChainMap` object without converting it to a regular dictionary.'
                    '\n\nSolution 2:\n- Solution 2 merges the dictionaries using the dictionary unpacking operator (`**`).\n- It creates a new dictionary by unpacking the three input dictionaries.'
                    '\n\n### Clarifying Questions:'
                    '\n1. What should be the type of the output? `ChainMap` object or a regular dictionary?'
                    '\n2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?'
                    '\n3. Can you provide an input-output example to help us better understand your requirement?'
         },
    ],

    'three_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement and its candidate solutions. '
                    'The user requirement is not clear, leading developers to interpret it differently. '
                    'Thus, the candidate solutions writtent by these developers have different functionalities, and some of them are wrong.'
                    '\nYour task is to clarify this requirement by asking clarifying questions. '
                    'Specifically, you first analyze how each developer understands the requirement. '
                    'Then, by comparing their different understandings of the requirement, '
                    'you can determine which statements in the requirement are not clear, and ask clarification questions for those statements.',
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\ndef lateralsuface_cylinder(r,h):\n    '''\n    Write a function to find the lateral surface area of a cylinder.\n    '''"
                    "\nSolution 0:\ndef lateralsuface_cylinder(r,h):\n    return 2 * 3.1415 * r * h"
                    "\nSolution 1:\nimport math\ndef lateralsuface_cylinder(r,h):\n    return 2 * math.pi * r * h"
         },
        {'role': 'assistant',
         'content': '### Analysis:'
                    '\nThe requirement is to write a function to find the lateral surface area of a cylinder.'
                    '\n\nSolution 0:\n- Solution 0 calculates the lateral surface area of a cylinder using an approximation of the value of π (approximately 3.1415).\n- It calculates the lateral surface area of a cylinder using the formula: 2 * 3.1415 * r * h.'
                    '\n\nSolution 1:\n- Solution 1 imports the math module and uses the precise value of π from the math module to calculate the lateral surface area of the cylinder.\n- It calculates the lateral surface area of a cylinder using the formula: 2 * π * r * h.'
                    '\n\n### Clarifying Questions:'
                    '\n1. What do the input parameters `r` and `h` mean respectively?'
                    '\n2. Is it acceptable to use an approximation for the value of π, or should the exact value be used?'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\ndef max_val(listval):\n    '''\n    Write a function to find the maximum value in a given heterogeneous list.\n    '''"
                    "\nSolution 0:\ndef max_val(listval):\n    return max(listval)"
                    "\nSolution 1:\ndef max_val(listval):\n    return max(listval)"
         },
        {'role': 'assistant',
         'content': '### Analysis:'
                    '\nThe requirement is to write a function to find the maximum value in a given heterogeneous list.'
                    '\n\nSolution 0:\n- Solution 0 uses the built-in `max()` function to find the maximum value in the given list.\n- It directly returns the result of the `max()` function.'
                    '\n\nSolution 1:\n- Solution 1 also uses the built-in `max()` function to find the maximum value in the given list.\n- It also directly returns the result of the `max()` function.'
                    '\n\n### Clarifying Questions:'
                    '\n1. What do you mean by a "heterogeneous list"? Does it mean that the list can contain elements of different types (e.g., integers, strings, etc.)?'
                    '\n2. If the list can contain different types of elements, does the function only need to focus on the int elements and return the maximum interger in these int elements?'
                    '\n3. Can you provide an example of a heterogeneous list and its expected maximum value?'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    '''\n    Write a function to merge three dictionaries into a single dictionary.\n    '''"
                    "\nSolution 0:\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    merged_dict = ct.ChainMap(dict1, dict2, dict3)\n    return dict(merged_dict)"
                    "\nSolution 1:\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    return ct.ChainMap(dict1, dict2, dict3)"
                    "\nSolution 2:\ndef merge_dictionaries_three(dict1, dict2, dict3):\n    return {**dict1, **dict2, **dict3}"
         },
        {'role': 'assistant',
         'content': '### Analysis:'
                    '\nThe requirement is to merge three dictionaries into a single dictionary.'
                    '\n\nSolution 0:\n- Solution 0 uses the `ChainMap` class from the `collections` module to merge the dictionaries.\n- It creates a `ChainMap` object with the three input dictionaries and then converts it to a regular dictionary using the `dict()` function.'
                    '\n\nSolution 1:\n- Solution 1 also uses the `ChainMap` class from the `collections` module to merge the dictionaries.\n- It directly returns the `ChainMap` object without converting it to a regular dictionary.'
                    '\n\nSolution 2:\n- Solution 2 merges the dictionaries using the dictionary unpacking operator (`**`).\n- It creates a new dictionary by unpacking the three input dictionaries.'
                    '\n\n### Clarifying Questions:'
                    '\n1. What should be the type of the output? `ChainMap` object or a regular dictionary?'
                    '\n2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?'
                    '\n3. Can you provide an input-output example to help us better understand your requirement?'
         },
    ],
}


answercq_prompt = {
    'zero_shot': [
        {'role': 'system',
         'content': 'You will receive a user requirement and its clarifying questions. '
                    'Your task is to answer these clarifying questions using the information provided in the given requirement. '
                    'In cases where the requirement does not contain specific information required to answer certain questions, '
                    'you should provide reasonable answers based on your own understanding or knowledge. '
                    'Reply only with the answers, do not repeat the requirement and questions. '
                    'Wrap the repaired requirement in <answers></answers> tags.' # I ADDED THIS, NOT CLARIFYGPT
         }],

    'one_shot': [
        {'role': 'system',
         'content': 'You will receive a user requirement and its clarifying questions. '
                    'Your task is to answer these clarifying questions using the information provided in the given requirement. '
                    'In cases where the requirement does not contain specific information required to answer certain questions, '
                    'you should provide reasonable answers based your own understanding or knowledge. '
                    'Reply only with the answers, do not repeat the requirement and questions.'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    '''\n    Write a function to merge three dictionaries into a single dictionary.\n    '''"
                    "\n\n### Clarifying Questions:"
                    "\n1. What should be the type of the output? `ChainMap` object or a regular dictionary?"
                    "\n2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?"
                    "\n3. Can you provide an input-output example to help us better understand your requirement?"
                    "\n\n### Answers:\n{insert answers here}"
         },
        {'role': 'assistant',
         'content': "### Answers:"
                    "\n1. The merged dictionaries should be a regular dictionary."
                    "\n2. Yes, the merged dictionary should contain all key-value pairs from all three input dictionaries, and when there are overlapping keys, the value from the first dictionary in the input sequence should take precedence."
                    "\n3. Yes, here is an input-output example: assert merge_dictionaries_three({\"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, {\"L\": \"lavender\", \"B\": \"Blue\"}, {\"G\": \"Green\", \"W\": \"White\"}) == {'B': 'Black', 'P': 'Pink', 'R': 'Red', 'G': 'Green', 'L': 'lavender', 'W': 'White'}"
         },
    ],

    'one_shot_w_test': [
            {'role': 'system',
             'content': 'You will receive a Python function and its test cases. '
                        'Your task is to answer some clarifying questions using the information provided in the given function and tests. '
                        'Reply only with the answers, do not repeat the code and questions.'
             },
            {'role': 'user',
             'content': "Python Function:"
                        "\n'''\nWrite a function to merge three dictionaries into a single dictionary.\n'''"
                        "\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    merged_dict = ct.ChainMap(dict1, dict2, dict3)\n    return dict(merged_dict)"
                        "\nTest Cases:"
                        "\nassert merge_dictionaries_three({ \"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, { \"G\": \"Green\", \"W\": \"White\" },{ \"O\": \"Orange\", \"W\": \"White\", \"B\": \"Black\" })=={'B': 'Black', 'R': 'Red', 'P': 'Pink', 'G': 'Green', 'W': 'White', 'O': 'Orange'}"
                        "\nassert merge_dictionaries_three({ \"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, { \"G\": \"Green\", \"W\": \"White\" },{\"L\":\"lavender\",\"B\":\"Blue\"})=={'W': 'White', 'P': 'Pink', 'B': 'Black', 'R': 'Red', 'G': 'Green', 'L': 'lavender'}"
                        "\nassert merge_dictionaries_three({ \"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" },{\"L\":\"lavender\",\"B\":\"Blue\"},{ \"G\": \"Green\", \"W\": \"White\" })=={'B': 'Black', 'P': 'Pink', 'R': 'Red', 'G': 'Green', 'L': 'lavender', 'W': 'White'}"
                        "\n\n### Clarifying Questions:"
                        "\n1. What should be the type of the output? `ChainMap` object or a regular dictionary?"
                        "\n2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?"
                        "\n3. Can you provide an input-output example to help us better understand your requirement?"
                        "\n\n### Answers:\n{insert answers here}"
             },
            {'role': 'assistant',
             'content': "### Answers:"
                        "\n1. The merged dictionaries should be a regular dictionary."
                        "\n2. Yes, the merged dictionary should contain all key-value pairs from all three input dictionaries, and when there are overlapping keys, the value from the first dictionary in the input sequence should take precedence."
                        "\n3. Yes, here is an input-output example: assert merge_dictionaries_three({\"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, {\"L\": \"lavender\", \"B\": \"Blue\"}, {\"G\": \"Green\", \"W\": \"White\"}) == {'B': 'Black', 'P': 'Pink', 'R': 'Red', 'G': 'Green', 'L': 'lavender', 'W': 'White'}"
             },
        ],

    'two_shot': [
        {'role': 'system',
         'content': 'You will receive a user requirement and its clarifying questions. '
                    'Your task is to answer these clarifying questions using the information provided in the given requirement. '
                    'In cases where the requirement does not contain specific information required to answer certain questions, '
                    'you should provide reasonable answers based your own understanding or knowledge. '
                    'Reply only with the answers, do not repeat the requirement and questions.'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\ndef lateralsuface_cylinder(r,h):\n    '''\n    Write a function to find the lateral surface area of a cylinder.\n    '''"
                    "\n\n### Clarifying Questions:"
                    "\n1. What do the input parameters `r` and `h` mean respectively?"
                    "\n2. Is it acceptable to use an approximation for the value of π, or should the exact value be used?"
                    "\n\n### Answers:\n{insert answers here}"
         },
        {'role': 'assistant',
         'content': '### Answers:'
                    '\n1. The input parameter `r` represents the radius of the cylinder, `h` represents the height of the cylinder.'
                    '\n2. Of course, it is acceptable to use an approximation for the value of π, like 3.1415.'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    '''\n    Write a function to merge three dictionaries into a single dictionary.\n    '''"
                    "\n\n### Clarifying Questions:"
                    "\n1. What should be the type of the output? `ChainMap` object or a regular dictionary?"
                    "\n2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?"
                    "\n3. Can you provide an input-output example to help us better understand your requirement?"
                    "\n\n### Answers:\n{insert answers here}"
         },
        {'role': 'assistant',
         'content': "### Answers:"
                    "\n1. The merged dictionaries should be a regular dictionary."
                    "\n2. Yes, the merged dictionary should contain all key-value pairs from all three input dictionaries, and when there are overlapping keys, the value from the first dictionary in the input sequence should take precedence."
                    "\n3. Yes, here is an input-output example: assert merge_dictionaries_three({\"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, {\"L\": \"lavender\", \"B\": \"Blue\"}, {\"G\": \"Green\", \"W\": \"White\"}) == {'B': 'Black', 'P': 'Pink', 'R': 'Red', 'G': 'Green', 'L': 'lavender', 'W': 'White'}"
         },
    ],

    'two_shot_w_test': [
            {'role': 'system',
             'content': 'You will receive a Python function and its test cases. '
                        'Your task is to answer some clarifying questions using the information provided in the given function and tests. '
                        'Reply only with the answers, do not repeat the code and questions.'
             },
            {'role': 'user',
             'content': "Python Function:"
                        "\n'''\nWrite a function to find the lateral surface area of a cylinder.\n'''"
                        "\ndef lateralsuface_cylinder(r,h):\n    return 2 * 3.1415 * r * h"
                        "\nTest Cases:"
                        "\nassert math.isclose(lateralsuface_cylinder(10,5), 314.15000000000003, rel_tol=0.001)"
                        "\nassert math.isclose(lateralsuface_cylinder(4,5), 125.66000000000001, rel_tol=0.001)"
                        "\nassert math.isclose(lateralsuface_cylinder(4,10), 251.32000000000002, rel_tol=0.001)"
                        "\n\n### Clarifying Questions:"
                        "\n1. What do the input parameters `r` and `h` mean respectively?"
                        "\n2. Is it acceptable to use an approximation for the value of π, or should the exact value be used?"
                        "\n\n### Answers:\n{insert answers here}"
             },
            {'role': 'assistant',
             'content': '### Answers:'
                        '\n1. The input parameter `r` represents the radius of the cylinder, `h` represents the height of the cylinder.'
                        '\n2. Of course, it is acceptable to use an approximation for the value of π, like 3.1415.'
             },
            {'role': 'user',
             'content': "Python Function:"
                        "\n'''\nWrite a function to merge three dictionaries into a single dictionary.\n'''"
                        "\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    merged_dict = ct.ChainMap(dict1, dict2, dict3)\n    return dict(merged_dict)"
                        "\nTest Cases:"
                        "\nassert merge_dictionaries_three({ \"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, { \"G\": \"Green\", \"W\": \"White\" },{ \"O\": \"Orange\", \"W\": \"White\", \"B\": \"Black\" })=={'B': 'Black', 'R': 'Red', 'P': 'Pink', 'G': 'Green', 'W': 'White', 'O': 'Orange'}"
                        "\nassert merge_dictionaries_three({ \"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, { \"G\": \"Green\", \"W\": \"White\" },{\"L\":\"lavender\",\"B\":\"Blue\"})=={'W': 'White', 'P': 'Pink', 'B': 'Black', 'R': 'Red', 'G': 'Green', 'L': 'lavender'}"
                        "\nassert merge_dictionaries_three({ \"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" },{\"L\":\"lavender\",\"B\":\"Blue\"},{ \"G\": \"Green\", \"W\": \"White\" })=={'B': 'Black', 'P': 'Pink', 'R': 'Red', 'G': 'Green', 'L': 'lavender', 'W': 'White'}"
                        "\n\n### Clarifying Questions:"
                        "\n1. What should be the type of the output? `ChainMap` object or a regular dictionary?"
                        "\n2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?"
                        "\n3. Can you provide an input-output example to help us better understand your requirement?"
                        "\n\n### Answers:\n{insert answers here}"
             },
            {'role': 'assistant',
             'content': "### Answers:"
                        "\n1. The merged dictionaries should be a regular dictionary."
                        "\n2. Yes, the merged dictionary should contain all key-value pairs from all three input dictionaries, and when there are overlapping keys, the value from the first dictionary in the input sequence should take precedence."
                        "\n3. Yes, here is an input-output example: assert merge_dictionaries_three({\"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, {\"L\": \"lavender\", \"B\": \"Blue\"}, {\"G\": \"Green\", \"W\": \"White\"}) == {'B': 'Black', 'P': 'Pink', 'R': 'Red', 'G': 'Green', 'L': 'lavender', 'W': 'White'}"
             },
        ],

    'three_shot': [
        {'role': 'system',
         'content': 'You will receive a user requirement and its clarifying questions. '
                    'Your task is to answer these clarifying questions using the information provided in the given requirement. '
                    'In cases where the requirement does not contain specific information required to answer certain questions, '
                    'you should provide reasonable answers based your own understanding or knowledge. '
                    'Reply only with the answers, do not repeat the requirement and questions.'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\ndef lateralsuface_cylinder(r,h):\n    '''\n    Write a function to find the lateral surface area of a cylinder.\n    '''"
                    "\n\n### Clarifying Questions:"
                    "\n1. What do the input parameters `r` and `h` mean respectively?"
                    "\n2. Is it acceptable to use an approximation for the value of π, or should the exact value be used?"
                    "\n\n### Answers:\n{insert answers here}"
         },
        {'role': 'assistant',
         'content': '### Answers:'
                    '\n1. The input parameter `r` represents the radius of the cylinder, `h` represents the height of the cylinder.'
                    '\n2. Of course, it is acceptable to use an approximation for the value of π, like 3.1415.'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\ndef max_val(listval):\n    '''\n    Write a function to find the maximum value in a given heterogeneous list.\n    '''"
                    "\n\n### Clarifying Questions:"
                    "\n1. What do you mean by a \"heterogeneous list\"? Does it mean that the list can contain elements of different types (e.g., integers, strings, etc.)?"
                    "\n2. If the list can contain different types of elements, does the function only need to focus on the int elements and return the maximum interger in these int elements?"
                    "\n3. Can you provide an example of a heterogeneous list and its expected maximum value?"
                    "\n\n### Answers:\n{insert answers here}"
         },
        {'role': 'assistant',
         'content': "### Answers:"
                    "\n1. A \"heterogeneous list\" means that the list can contain elements of different types, such as integers, strings, etc."
                    "\n2. Yes, the function should focus on the int elements and return the maximum interger in these int elements."
                    "\n3. Yes, here is an example: Input:['Python', 30, 20, 40, 50, 'version'], Output:50."
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    '''\n    Write a function to merge three dictionaries into a single dictionary.\n    '''"
                    "\n\n### Clarifying Questions:"
                    "\n1. What should be the type of the output? `ChainMap` object or a regular dictionary?"
                    "\n2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?"
                    "\n3. Can you provide an input-output example to help us better understand your requirement?"
                    "\n\n### Answers:\n{insert answers here}"
         },
        {'role': 'assistant',
         'content': "### Answers:"
                    "\n1. The merged dictionaries should be a regular dictionary."
                    "\n2. Yes, the merged dictionary should contain all key-value pairs from all three input dictionaries, and when there are overlapping keys, the value from the first dictionary in the input sequence should take precedence."
                    "\n3. Yes, here is an input-output example: assert merge_dictionaries_three({\"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, {\"L\": \"lavender\", \"B\": \"Blue\"}, {\"G\": \"Green\", \"W\": \"White\"}) == {'B': 'Black', 'P': 'Pink', 'R': 'Red', 'G': 'Green', 'L': 'lavender', 'W': 'White'}"
         },
    ],

    'three_shot_w_test': [
            {'role': 'system',
             'content': 'You will receive a Python function and its test cases. '
                        'Your task is to answer some clarifying questions using the information provided in the given function and tests. '
                        'Reply only with the answers, do not repeat the code and questions.'
             },
            {'role': 'user',
             'content': "Python Function:"
                        "\n'''\nWrite a function to find the lateral surface area of a cylinder.\n'''"
                        "\ndef lateralsuface_cylinder(r,h):\n    return 2 * 3.1415 * r * h"
                        "\nTest Cases:"
                        "\nassert math.isclose(lateralsuface_cylinder(10,5), 314.15000000000003, rel_tol=0.001)"
                        "\nassert math.isclose(lateralsuface_cylinder(4,5), 125.66000000000001, rel_tol=0.001)"
                        "\nassert math.isclose(lateralsuface_cylinder(4,10), 251.32000000000002, rel_tol=0.001)"
                        "\n\n### Clarifying Questions:"
                        "\n1. What do the input parameters `r` and `h` mean respectively?"
                        "\n2. Is it acceptable to use an approximation for the value of π, or should the exact value be used?"
                        "\n\n### Answers:\n{insert answers here}"
             },
            {'role': 'assistant',
             'content': '### Answers:'
                        '\n1. The input parameter `r` represents the radius of the cylinder, `h` represents the height of the cylinder.'
                        '\n2. Of course, it is acceptable to use an approximation for the value of π, like 3.1415.'
             },
            {'role': 'user',
             'content': "Python Function:"
                        "\n'''\nWrite a function to find the maximum value in a given heterogeneous list.\n'''"
                        "\ndef max_val(listval):\n     max_val = max(i for i in listval if isinstance(i, int)) \n     return(max_val)"
                        "\nTest Cases:"
                        "\nassert max_val(['Python', 3, 2, 4, 5, 'version'])==5"
                        "\nassert max_val(['Python', 15, 20, 25])==25"
                        "\nassert max_val(['Python', 30, 20, 40, 50, 'version'])==50"
                        "\n\n### Clarifying Questions:"
                        "\n1. What do you mean by a \"heterogeneous list\"? Does it mean that the list can contain elements of different types (e.g., integers, strings, etc.)?"
                        "\n2. If the list can contain different types of elements, does the function only need to focus on the int elements and return the maximum interger in these int elements?"
                        "\n3. Can you provide an example of a heterogeneous list and its expected maximum value?"
                        "\n\n### Answers:\n{insert answers here}"
             },
            {'role': 'assistant',
             'content': "### Answers:"
                        "\n1. A \"heterogeneous list\" means that the list can contain elements of different types, such as integers, strings, etc."
                        "\n2. Yes, the function should focus on the int elements and return the maximum interger in these int elements."
                        "\n3. Yes, here is an example: Input:['Python', 30, 20, 40, 50, 'version'], Output:50."
             },
            {'role': 'user',
             'content': "Python Function:"
                        "\n'''\nWrite a function to merge three dictionaries into a single dictionary.\n'''"
                        "\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    merged_dict = ct.ChainMap(dict1, dict2, dict3)\n    return dict(merged_dict)"
                        "\nTest Cases:"
                        "\nassert merge_dictionaries_three({ \"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, { \"G\": \"Green\", \"W\": \"White\" },{ \"O\": \"Orange\", \"W\": \"White\", \"B\": \"Black\" })=={'B': 'Black', 'R': 'Red', 'P': 'Pink', 'G': 'Green', 'W': 'White', 'O': 'Orange'}"
                        "\nassert merge_dictionaries_three({ \"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, { \"G\": \"Green\", \"W\": \"White\" },{\"L\":\"lavender\",\"B\":\"Blue\"})=={'W': 'White', 'P': 'Pink', 'B': 'Black', 'R': 'Red', 'G': 'Green', 'L': 'lavender'}"
                        "\nassert merge_dictionaries_three({ \"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" },{\"L\":\"lavender\",\"B\":\"Blue\"},{ \"G\": \"Green\", \"W\": \"White\" })=={'B': 'Black', 'P': 'Pink', 'R': 'Red', 'G': 'Green', 'L': 'lavender', 'W': 'White'}"
                        "\n\n### Clarifying Questions:"
                        "\n1. What should be the type of the output? `ChainMap` object or a regular dictionary?"
                        "\n2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?"
                        "\n3. Can you provide an input-output example to help us better understand your requirement?"
                        "\n\n### Answers:\n{insert answers here}"
             },
            {'role': 'assistant',
             'content': "### Answers:"
                        "\n1. The merged dictionaries should be a regular dictionary."
                        "\n2. Yes, the merged dictionary should contain all key-value pairs from all three input dictionaries, and when there are overlapping keys, the value from the first dictionary in the input sequence should take precedence."
                        "\n3. Yes, here is an input-output example: assert merge_dictionaries_three({\"R\": \"Red\", \"B\": \"Black\", \"P\": \"Pink\" }, {\"L\": \"lavender\", \"B\": \"Blue\"}, {\"G\": \"Green\", \"W\": \"White\"}) == {'B': 'Black', 'P': 'Pink', 'R': 'Red', 'G': 'Green', 'L': 'lavender', 'W': 'White'}"
             },
        ],
}


synthesize_prompt = {
    'zero_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement and its clarification. '
                    'The clarification aims to enhance the clarity of the requirement and should be duly noted. '
                    'Strictly follow the function signature provided in the requirement, '
                    'respond only with a correct, efficient Python function. '
                    'Do not write explanations or assertions; simply provide only the code. '
                    'Wrap the generated code in <code></code> tags.' # I ADDED THIS LINE. NOT ORIGINAL CLARIFYGPT
         }],

    'one_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement containing a function signature and a docstring. '
                    'Please read the docstring, understand the user\'s intention, and respond only with a correct, efficient Python function. '
                    'Do not import libraries other than those provided in the function signature; '
                    'do not write explanations or assertions; simply provide only the code. '
         },
        {'role': 'user',
         'content': 'User Requirement:'
                    '\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    \'\'\'\n    Write a function to merge three dictionaries into a single dictionary.'
                    '\n    Clarification:'
                    '\n    1. What should be the type of the output? `ChainMap` object or a regular dictionary?'
                    '\n    - The merged dictionaries should be a regular dictionary.'
                    '\n    2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?'
                    '\n    - Yes, the merged dictionary should contain all key-value pairs from all three input dictionaries, and when there are overlapping keys, the value from the first dictionary in the input sequence should take precedence.'
                    '\n    3. Can you provide an input-output example to help us better understand your requirement?'
                    '\n    - Yes, here is an input-output example: assert merge_dictionaries_three({"R": "Red", "B": "Black", "P": "Pink"}, {"L": "lavender", "B": "Blue"}, {"G": "Green", "W": "White"}) == {\'B\': \'Black\', \'P\': \'Pink\', \'R\': \'Red\', \'G\': \'Green\', \'L\': \'lavender\', \'W\': \'White\'}\n    \'\'\'\n'
         },
        {'role': 'assistant',
         'content': 'def merge_dictionaries_three(dict1,dict2, dict3):\n    merged_dict = ct.ChainMap(dict1, dict2, dict3)\n    return dict(merged_dict)'
         },
    ],

    'two_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement containing a function signature and a docstring. '
                    'Please read the docstring, understand the user\'s intention, and respond only with a correct, efficient Python function. '
                    'Do not import libraries other than those provided in the function signature; '
                    'do not write explanations or assertions; simply provide only the code.'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\ndef lateralsuface_cylinder(r,h):\n    '''\n    Write a function to find the lateral surface area of a cylinder."
                    "\n    Clarification:"
                    "\n    1. What do the input parameters `r` and `h` mean respectively?"
                    "\n    - The input parameter `r` represents the radius of the cylinder, `h` represents the height of the cylinder."
                    "\n    2. Is it acceptable to use an approximation for the value of π, or should the exact value be used?"
                    "\n    - Of course, it is acceptable to use an approximation for the value of π, like 3.1415.\n    '''"
         },
        {'role': 'assistant',
         'content': "def lateralsuface_cylinder(r,h):\n    return 2 * 3.1415 * r * h"
         },
        {'role': 'user',
         'content': 'User Requirement:'
                    '\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    \'\'\'\n    Write a function to merge three dictionaries into a single dictionary.'
                    '\n    Clarification:'
                    '\n    1. What should be the type of the output? `ChainMap` object or a regular dictionary?'
                    '\n    - The merged dictionaries should be a regular dictionary.'
                    '\n    2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?'
                    '\n    - Yes, the merged dictionary should contain all key-value pairs from all three input dictionaries, and when there are overlapping keys, the value from the first dictionary in the input sequence should take precedence.'
                    '\n    3. Can you provide an input-output example to help us better understand your requirement?'
                    '\n    - Yes, here is an input-output example: assert merge_dictionaries_three({"R": "Red", "B": "Black", "P": "Pink"}, {"L": "lavender", "B": "Blue"}, {"G": "Green", "W": "White"}) == {\'B\': \'Black\', \'P\': \'Pink\', \'R\': \'Red\', \'G\': \'Green\', \'L\': \'lavender\', \'W\': \'White\'}\n    \'\'\''
         },
        {'role': 'assistant',
         'content': 'def merge_dictionaries_three(dict1,dict2, dict3):\n    merged_dict = ct.ChainMap(dict1, dict2, dict3)\n    return dict(merged_dict)'
         },
    ],

    'three_shot': [
        {'role': 'system',
         'content': 'You will be given a user requirement containing a function signature and a docstring. '
                    'Please read the docstring, understand the user\'s intention, and respond only with a correct, efficient Python function. '
                    'Do not import libraries other than those provided in the function signature; '
                    'do not write explanations or assertions; simply provide only the code.'
         },
        {'role': 'user',
         'content': "User Requirement:"
                    "\ndef lateralsuface_cylinder(r,h):\n    '''\n    Write a function to find the lateral surface area of a cylinder."
                    "\n    Clarification:"
                    "\n    1. What do the input parameters `r` and `h` mean respectively?"
                    "\n    - The input parameter `r` represents the radius of the cylinder, `h` represents the height of the cylinder."
                    "\n    2. Is it acceptable to use an approximation for the value of π, or should the exact value be used?"
                    "\n    - Of course, it is acceptable to use an approximation for the value of π, like 3.1415.\n    '''"},
        {'role': 'assistant',
         'content': "def lateralsuface_cylinder(r,h):\n    return 2 * 3.1415 * r * h"
         },
        {'role': 'user',
         'content': 'User Requirement:'
                    '\ndef max_val(listval):\n    \'\'\'\n    Write a function to find the maximum value in a given heterogeneous list.'
                    '\n    Clarification:'
                    '\n    1. What do you mean by a "heterogeneous list"? Does it mean that the list can contain elements of different types (e.g., integers, strings, etc.)?'
                    '\n    - A "heterogeneous list" means that the list can contain elements of different types, such as integers, strings, etc.'
                    '\n    2. If the list can contain different types of elements, does the function only need to focus on the int elements and return the maximum interger in these int elements?'
                    '\n    - Yes, the function should focus on the int elements and return the maximum interger in these int elements.'
                    '\n    3. Can you provide an example of a heterogeneous list and its expected maximum value?'
                    '\n    - Yes, here is an example: Input:[\'Python\', 30, 20, 40, 50, \'version\'], Output:50.\n    \'\'\''
         },
        {'role': 'assistant',
         'content': 'def max_val(listval):\n     max_val = max(i for i in listval if isinstance(i, int)) \n     return(max_val)'
         },
        {'role': 'user',
         'content': 'User Requirement:'
                    '\nimport collections as ct\ndef merge_dictionaries_three(dict1,dict2, dict3):\n    \'\'\'\n    Write a function to merge three dictionaries into a single dictionary.'
                    '\n    Clarification:'
                    '\n    1. What should be the type of the output? `ChainMap` object or a regular dictionary?'
                    '\n    - The merged dictionaries should be a regular dictionary.'
                    '\n    2. Should the merged dictionary contain all key-value pairs from all three input dictionaries, and what should happen if there are overlapping keys?'
                    '\n    - Yes, the merged dictionary should contain all key-value pairs from all three input dictionaries, and when there are overlapping keys, the value from the first dictionary in the input sequence should take precedence.'
                    '\n    3. Can you provide an input-output example to help us better understand your requirement?'
                    '\n    - Yes, here is an input-output example: assert merge_dictionaries_three({"R": "Red", "B": "Black", "P": "Pink"}, {"L": "lavender", "B": "Blue"}, {"G": "Green", "W": "White"}) == {\'B\': \'Black\', \'P\': \'Pink\', \'R\': \'Red\', \'G\': \'Green\', \'L\': \'lavender\', \'W\': \'White\'}\n    \'\'\''
         },
        {'role': 'assistant',
         'content': 'def merge_dictionaries_three(dict1,dict2, dict3):\n    merged_dict = ct.ChainMap(dict1, dict2, dict3)\n    return dict(merged_dict)'
         },
    ],
}


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
