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


instruction_test_based_repair = "You are a coding assistant specialized in repairing buggy Python programs."


def prompt_test_based_repair(requirement, entry_point, code, failed_input_output_examples):
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
• Understand the task requirement and python program.
• Compare the actual output with the canonical output to determine why the program is faulty. Identify logical errors, syntax issues, or edge-case handling flaws.
• Provide a corrected version of the Python code that, when run on the given test input, will produce the expected (canonical) output.

Requirement:
{requirement}

Buggy Code:
{code}

Failed Test Cases:
{tests}
---

Please return the **repaired Python code**, wrapped in <code></code> tags.
"""


instruction_repair_requirement = "You are an assistant that repairs ambiguous requirements based on the reference implementation."


def prompt_repair_requirement(requirement, entry_point, program):
    return f"""
You are provided with:
1. An ambiguous description of a code generation task involving the function `{entry_point}`, which has led to multiple interpretations and consequently different generated implementations.
2. Reference implementation reflecting the intended behavior.

Your task is to follow these steps:
1. **Analyze** the correct program to clearly identify the intended behavior.
2. **Compare** this correct behavior with the ambiguous description to pinpoint specific functional differences, such as:
   - **Input/output handling** (e.g., format differences, varying data types).
   - **Assumptions made** (e.g., implicit constraints or unstated preconditions).
3. **Revise** the identified functional differences. The revised description should guide an LLM to generate code matching exactly the behavior of the provided correct program.

Important notes:
- Ensure to preserve all original examples, illustrations, input/output samples, and intermediate explanations included in the original description.
- If there is a contradiction between the correct program and the examples, prioritize the examples.
- If the description contains references to other functions, leave those sections unchanged.

Format your revised, unambiguous requirement explicitly in Python function syntax with type hints and a clear, concise docstring. Enclose your repaired requirement within `<requirement></requirement>` tags as follows:

```
<requirement>
def function_name(argument: type_hint) -> return_type_hint:
    \"\"\"Clearly revised, unambiguous description.\"\"\"
</requirement>
```

**Ambiguous Problem Description:**
```
{requirement}
```

**Reference Program:**
```
{program}
```
"""


instruction_repair_largest_cluster_requirement = "You are an assistant that repairs ambiguous requirements based on the correct implementation."


def prompt_repair_largest_cluster_requirement(requirement, entry_point, programs, specified_programs):
    programs_str = ""
    for i, p in enumerate(programs):
        programs_str += f"### Incorrect program {i}\n{p}\n"

    return f"""
You are provided with:
1. An ambiguous description of a code generation task involving the function `{entry_point}`, which has led to multiple interpretations and consequently different generated implementations.
2. One correct implementation reflecting the intended behavior.
3. Multiple incorrect implementations demonstrating alternative behaviors.

Your task is to:
1. **Analyze** the correct program to clearly identify the intended behavior.
2. **Compare** this correct behavior with the incorrect implementations to pinpoint specific functional differences, such as:
   - **Input/output handling** (e.g., format differences, varying data types).
   - **Assumptions made** (e.g., implicit constraints or unstated preconditions).
3. **Revise** the identified functional differences. The revised description should guide an LLM to generate code matching exactly the behavior of the provided correct program.

Important notes:
- Ensure to preserve all original examples, illustrations, input/output samples, and intermediate explanations included in the original description.
- If there is a contradiction between the correct program and the examples, prioritize the examples.
- If the description contains references to other functions, leave those sections unchanged.

Format your revised, unambiguous requirement explicitly in Python function syntax with type hints and a clear, concise docstring. Enclose your repaired requirement within `<requirement></requirement>` tags as follows:

```
<requirement>
def function_name(argument: type_hint) -> return_type_hint:
    \"\"\"Revised description.\"\"\"
</requirement>
```

**Ambiguous Problem Description:**
```
{requirement}
```

**Correct Program:**
```
{specified_programs}
```

**Incorrect Programs:**
```
{programs_str}
```
"""


instruction_repair_largest_cluster_requirement = "You are an assistant that repairs ambiguous requirements based on the correct implementation."


def prompt_repair_largest_cluster_requirement(requirement, entry_point, programs, specified_programs):
    programs_str = ""
    for i, p in enumerate(programs):
        programs_str += f"### Incorrect program {i}\n{p}\n"

    return f"""
You are provided with:
1. An ambiguous description of a code generation task involving the function `{entry_point}`, which has led to multiple interpretations and consequently different generated implementations.
2. One correct implementation reflecting the intended behavior.
3. Multiple incorrect implementations demonstrating alternative behaviors.

Your task is to:
1. **Analyze** the correct program to clearly identify the intended behavior.
2. **Compare** this correct behavior with the incorrect implementations to pinpoint specific functional differences, such as:
   - **Input/output handling** (e.g., format differences, varying data types).
   - **Assumptions made** (e.g., implicit constraints or unstated preconditions).
3. **Revise** the identified functional differences. The revised description should guide an LLM to generate code matching exactly the behavior of the provided correct program.

Important notes:
- Ensure to preserve all original examples, illustrations, input/output samples, and intermediate explanations included in the original description.
- If there is a contradiction between the correct program and the examples, prioritize the examples.
- If the description contains references to other functions, leave those sections unchanged.

Format your revised, unambiguous requirement explicitly in Python function syntax with type hints and a clear, concise docstring. Enclose your repaired requirement within `<requirement></requirement>` tags as follows:

```
<requirement>
def function_name(argument: type_hint) -> return_type_hint:
    \"\"\"Revised description.\"\"\"
</requirement>
```

**Ambiguous Problem Description:**
```
{requirement}
```

**Correct Program:**
```
{specified_programs}
```

**Incorrect Programs:**
```
{programs_str}
```
"""