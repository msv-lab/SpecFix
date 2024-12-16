

def prompt_code_generation(requirements):
    return f"""
Here are some requirements:\n{requirements}
Generate a program that adheres to these requirements. 
Do not output any text at all besides code. I do NOT want an explanation nor a preamble. Just code.
The first line of your response should be the function signature."""

def prompt_code_generation_artificial_entropy(requirements, previously_generated_programs):
    return f"""
Requirements: {requirements}\nYour task is to generate a program that adheres to these requirements.
However, avoid using any ideas, structures, or patterns found in the following previously generated programs: {previously_generated_programs}.
Think outside the box, and aim for a solution that feels fresh and novel. Do not base your logic on any previous examples.
Just return the code, starting with the function signature—no explanation or preamble is needed."""

def prompt_requirement_repair(requirements, counterexample):
    return f"""
Here are some ambiguous requirements:\n{requirements}\n 
Repair these requirements given this counter example:\n{counterexample}
Do not provide commentary on the requirements, simply provide them to me like you are describing a problem. 
Do not answer or write the code described by the requirements."""



