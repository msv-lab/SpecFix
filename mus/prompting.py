instruction_generate_code = "You are an assistant that generates Python code based on requirement."


def prompt_generate_code(requirement):
    return f"""
Implement a python function that adheres to the requirements. Wrap the generated code in <code></code> tags.  Here is an example:
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

Probes 1 and 2 have different order of operations. Probe 1 removes duplicates first and then sorts the array, while Probe 2 sorts the array first and then removes duplicates.

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


instruction_probe = "You are an assistant that generates problem-solving process based on the requirement and input."


def prompt_probe(requirement):
    return f"""
Given a problem requirement, write a rough problem-solving process using three programming structures (i.e., sequential, branch, and loop structures). Wrap the output in <output></output> tags. Here is an example:

# Example

## Requirement

Write a python function to find sum of prime numbers between 1 to n.

## Output

<output>
1. Initialize a list "prime" with True values.
2. Initialize a variable "p" with 2.
3. While p * p is less than or equal to 10:
4.   If prime[p] is True:
5.     Set all the multiples of p to False.
6.   Increment the variable "p" by 1.
7. Compute the sum of the prime numbers.
8. Return the sum.
</output>

# Your task

## Requirement

{requirement}

## Output
"""


instruction_judge_discrepancy_probe = "You are an assistant that judge whether discrepancies exist between the execution probes based on requirement"


def prompt_judge_discrepancy_probe(requirement, probe):
    probe_str = ""
    for i, c in enumerate(probe):
        probe_str += f"### Probe {i + 1}\n {c}\n"

    return f"""
Given the requirement and corresponding execution probes, check whether discrepancies exist between the execution probes. Output discrepancies if exist; output "No" for no discrepancies. Wrap the judgement in the <judgement></judgement> tags. Here is an example:

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

## Judgement

<judgement>
Probes 1 and 2 have different order of operations. Probe 1 removes duplicates first and then sorts the array, while Probe 2 sorts the array first and then removes duplicates.
</judgement>

# Your task

## Requirement

{requirement}

## Probe

{probe_str}

## Judgement
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


instruction_generate_fact = "You are an assistant that generates facts and assumptions based on the requirement."


def prompt_generate_fact(requirement):
    return f"""
You are tasked with implementing a Python function based on a given requirement. Think step-by-step. Your response should include:

1. Code: The Python function, wrapped in <code></code> tags.
2. Facts and Assumptions: Facts are information can be derived explicitly from the requirement and are used in code implementation. Wrap facts in <facts></facts>` tags. Assumptions are information not explicitly stated but inferred from context or common practice and are used in code implementation. Wrap assumptions in `<assumptions></assumptions>` tags.

# Example:

## Requirement
Write a function that sorts an array while removing consecutive duplicates.

## Response:
<code>
def sort_remove_consecutive_duplicates(arr):
    return sorted(set(arr), key=arr.index)
</code>

<facts>
1. The function removes duplicates from the input array.
2. The function sorts the array
</facts>

<assumptions>
1. The function sorts the array in order of appearance.
2. The function removes duplicates first and then sorts the array.
</assumptions>

# Your Task:

## Requirement
{requirement}

## Code

## Facts
"""


def supply_facts(requirement, code, facts, assumption):
    return f"""
Given a requirement, corresponding code, facts used in implementation, and assumptions used in implementation, supply additional facts that can be explicitly derived from the requirement and used in code implementation. Supply the additional assumptions that can be inferred from the requirement and used in code implementation. Wrap the additional facts in <facts></facts> tags and the additional assumptions in <assumptions></assumptions> tags. Here is an example:

# Example

## Requirement

Write a function that sorts an array while removing consecutive duplicates.

## Code

def sort_remove_consecutive_duplicates(arr):
    return sorted(set(arr), key=arr.index)

## Facts

1. The function removes duplicates from the input array.
2. The function sorts the array.

## Assumptions

1. The function sorts the array in order of appearance.
2. The function removes duplicates first and then sorts the array.

## Additional Facts

<facts>
1. The function removes only consecutive duplicates.
2. The function returns a list.
</facts>

## Additional Assumptions

<assumptions>
1. The input array is not empty.
2. The input array contains integers.
</assumptions>    
"""