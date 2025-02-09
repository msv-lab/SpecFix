"""
remove_examples.py

Provides functions to remove examples from programming problem descriptions.
It offers a “hardcoded” removal for texts containing certain phrases as well as an
LLM‑assisted removal. It also includes a function to process an ambiguous taco file.
"""

import sys
from specfix.utils import unwrap
from specfix.model import Model
from concurrent.futures import ThreadPoolExecutor, as_completed
import jsonlines
from tqdm import tqdm

# Allow arbitrarily large integer strings (if needed)
sys.set_int_max_str_digits(0)

# --- Model Configuration ---
model_name = "qwen-plus"
model = Model(model_name)

# --- Removal Instruction and Prompts ---
instruction_remove_example = "You are an assistant that removes examples from a programming problem description."


def remove_example_geeksforgeeks(origin: str) -> str:
    """
    Remove the example block from a GeeksforGeeks-style problem description.
    If the markers are not found, return the original text.
    """
    lindex = origin.find("Example 1")
    rindex = origin.find("Your Task:  \nYou dont need to read input or print anything.")
    if lindex == -1 or rindex == -1:
        return origin
    return origin[:lindex] + origin[rindex:]


def prompt_remove_example(origin: str) -> str:
    """
    Return a prompt instructing the LLM to remove all examples from the problem description.
    """
    prompt = (
            "Remove all examples from the provided programming problem description, including sample inputs/outputs, "
            "in-text illustrations (e.g., 'for example, if...'), or standalone example sections. Retain all other content "
            "such as the problem statement, constraints, notes, and explanations that are not explicitly part of an example. "
            "Do not modify, rephrase, or delete any non-example text. Wrap the modified description in <requirement></requirement> tags.\n"
            + origin
    )
    return prompt


def remove_example(requirement: str) -> str:
    """
    Remove examples from the requirement using an LLM.
    """
    response = model.get_response(instruction_remove_example, prompt_remove_example(requirement))
    return unwrap(response, "requirement")


def taco_ambiguous_collection():
    """
    Process ambiguous taco data from "taco_lite.jsonl" by removing examples from the requirement.
    The function writes the processed objects into "taco_lite_woe.jsonl".
    """

    def process_obj(idx, obj):
        req = obj.get('requirement', "")
        # If the requirement contains the specific marker, use the hardcoded removal;
        # otherwise, use the LLM-assisted removal.
        if "Your Task:  \nYou dont need to read input or print anything." in req:
            obj['requirement'] = remove_example_geeksforgeeks(req)
        else:
            obj['requirement'] = remove_example(req)
        return idx, obj

    with jsonlines.open("taco_lite.jsonl") as reader, \
            jsonlines.open("taco_lite_woe.jsonl", "w", flush=True) as writer:
        objs = list(reader)
        processed_objs = [None] * len(objs)

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(process_obj, idx, obj) for idx, obj in enumerate(objs)]
            for future in tqdm(as_completed(futures), total=len(objs), desc="Processing"):
                idx, result_obj = future.result()
                processed_objs[idx] = result_obj

        for obj in processed_objs:
            writer.write(obj)


if __name__ == "__main__":
    taco_ambiguous_collection()
