"""
clean_taco.py

Filters and cleans the taco dataset. It processes each taco entry,
verifies/revises the inputs/outputs (via an LLM if needed), and writes canonical_solution to "taco_clean.jsonl".
"""

import ast
import configparser
import jsonlines
import sys
from tqdm import tqdm

from specfix.utils import unwrap, execute_inputs, compare
from specfix.model import Model
from specfix.solution_transformer import transform_code

# Allow arbitrarily large integer strings (if needed)
sys.set_int_max_str_digits(0)

# --- Model Configuration ---
config = configparser.ConfigParser()
config.read('../../.config')
model_name = "qwen-plus"
api_key = ""
if "qwen" in model_name:
    api_key = config['API_KEY']['qwen_key']
elif "gpt" in model_name or "o1" in model_name:
    api_key = config['API_KEY']['openai_key']
model = Model(model_name, api_key, 0)

# --- Revision Instruction and Prompt ---
instruction_revise = "You are an assistant that revises inputs and outputs format for a programming problem."


def prompt_revise(requirement, inputs, outputs):
    """Return a prompt to have the LLM revise the input/output format."""
    return f"""
You are given the following inputs and outputs for a programming problem. Your task is to revise the format of inputs and outputs. Don't output any explanations or additional information.

# Inputs
Based on problem description, judge the input type first. Store inputs in one example in one list. If a parameter type is list, nest it inside the outer list. Maintain original types. 
Examples:
- "AABBBCBBAC" -> ["AABBBCBBAC"]
- "846903" -> ["846903"]
- [1, 2, 3] -> [[1, 2, 3]]
- 's = "846903"' -> ["846903"]

Gather all inputs into a general list. Wrap the collection in <input></input> tags.

# Outputs
Based on problem description, judge the output type first. Sometimes, example outputs types are not consistent with the problem description.
Store outputs in one example in one list. Capitalize boolean values. If output type is list, nest it inside the outer list.
Examples:
- 3 -> [3]
- 'Circular' -> ['Circular']
- true -> [True]
- [1, 2, 3] -> [[1, 2, 3]]

Gather all outputs into a general list. Wrap the collection in <output></output> tags.

# Your task
Problem Description:
{requirement}

Inputs: {inputs}
Outputs: {outputs}
"""


def revise_data(requirement, inputs, outputs, instruction, prompt_func, programs, entry_point, validator, max_retries=3):
    """
    Revise the input/output format using a set of candidate programs and an LLM if needed.
    Returns (revised_inputs, revised_outputs, program) on success; otherwise, returns (None, None, None).
    """
    print("REVISING")
    original_inputs = inputs
    original_outputs = outputs
    valid_programs = []
    for prog in programs:
        try:
            valid_programs.append(transform_code(prog))
        except Exception:
            continue

    # Initial revision: if the inputs/outputs are not valid, wrap each element in a list.
    if not validator(inputs):
        inputs = [[inp] for inp in inputs]
    if not validator(outputs):
        outputs = [[out] for out in outputs]
    for prog in valid_programs:
        results = execute_inputs(prog, inputs, entry_point)
        if compare(results, outputs):
            return inputs, outputs, prog

    # LLM-assisted revision
    for attempt in range(1, max_retries + 1):
        try:
            response = model.get_response(instruction, prompt_func(requirement, original_inputs, original_outputs))
            revised_inputs = unwrap(response, "input")
            revised_outputs = unwrap(response, "output")
            parsed_inputs = ast.literal_eval(revised_inputs)
            parsed_outputs = ast.literal_eval(revised_outputs)

            if not parsed_inputs:
                raise ValueError("Empty inputs after parsing")
            if not validator(parsed_inputs):
                raise ValueError("Input validation failed")
            filtered_inputs = [item for item in parsed_inputs if item != []]

            if not parsed_outputs:
                raise ValueError("Empty outputs after parsing")
            if not validator(parsed_outputs):
                raise ValueError("Output validation failed")
            filtered_outputs = [item for item in parsed_outputs if item != []]

            if not filtered_inputs or not filtered_outputs:
                raise ValueError("Empty inputs or outputs after filtering")

            for prog in valid_programs:
                results = execute_inputs(prog, filtered_inputs, entry_point)
                if compare(results, filtered_outputs):
                    print(f"Success after {attempt} attempt(s)")
                    return filtered_inputs, filtered_outputs, prog
            return filtered_inputs, filtered_outputs, None

        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                return None, None, None


def cut_inputs_outputs(inputs, outputs):
    """
    Reduce the size of inputs and outputs until their string representations are
    shorter than the specified limit.
    """
    while len(str(inputs)) > 10000 or len(str(outputs)) > 10000:
        inputs = inputs[:-1]
        outputs = outputs[:-1]
    return inputs, outputs


def process_entry(obj):
    """
    Process a single taco entry:
      - Reject entries with missing requirements or newlines in inputs/outputs.
      - Cut inputs/outputs if they are too large.
      - Revise the I/O format (and the candidate solutions) via revise_data.
      - Lowercase the entry point name and update the requirement and starter code.
    Returns the processed object or None if the entry is invalid.
    """
    if not obj.get('requirement'):
        return None
    if any("\n" in inp for inp in obj.get('inputs', []) if isinstance(inp, str)):
        return None
    if any("\n" in out for out in obj.get('outputs', []) if isinstance(out, str)):
        return None

    inputs, outputs = cut_inputs_outputs(obj['inputs'], obj['outputs'])
    if len(inputs) < 3:
        return None

    starter_code = obj.get("starter_code", "")
    target_solutions = [
        code for code in obj.get('solutions', [])
        if "stdin" not in code and "input(" not in code and "print(" not in code
    ]

    # Extract the entry point from starter_code
    def_idx = starter_code.find("def ")
    if def_idx == -1:
        return None
    start = def_idx + 4
    end = starter_code.find("(", start)
    if end == -1:
        return None
    entry_point = starter_code[start:end].strip()

    revised_inputs, revised_outputs, program = revise_data(
        obj["requirement"], inputs, outputs, instruction_revise, prompt_revise,
        target_solutions, entry_point,
        lambda x: isinstance(x, list) and all(isinstance(i, list) for i in x),
        max_retries=3
    )

    if not program:
        return None

    # Replace the entry point with its lowercase version.
    canonical_solution = program.replace(entry_point, entry_point.lower())
    obj['canonical_solution'] = canonical_solution
    obj.pop('solutions', None)
    obj["requirement"] = obj["requirement"].replace(entry_point, entry_point.lower())
    obj['entry_point'] = entry_point.lower()
    obj['inputs'] = revised_inputs
    obj['outputs'] = revised_outputs

    # Update the starter_code and requirement with the function definition line and a docstring.
    for line in canonical_solution.split("\n"):
        if f"def {obj['entry_point']}(" in line:
            def_line = line.strip()
            obj['starter_code'] = def_line
            obj['requirement'] = f"{def_line}\n\"\"\"{obj['requirement'].strip()}\n\"\"\""
            break

    return obj


def clean_taco():
    """
    Process all taco entries from "taco.jsonl", filter out non-compliant entries,
    and write the cleaned ones to "taco_clean.jsonl".
    """
    with jsonlines.open("taco.jsonl") as reader:
        objs = list(reader)
    print(f"Loaded {len(objs)} entries")
    with jsonlines.open("taco_clean.jsonl", "w", flush=True) as writer:
        for i, obj in tqdm(enumerate(objs), total=len(objs), desc="Cleaning entries"):
            processed = process_entry(obj)
            if processed:
                writer.write(processed)


if __name__ == "__main__":
    clean_taco()
