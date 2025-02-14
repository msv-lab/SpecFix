import ast
import sys
import jsonlines
from datasets import load_dataset
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from specfix.utils import unwrap, execute_inputs, compare
from specfix.model import Model
from specfix.solution_transformer import transform_code

sys.set_int_max_str_digits(0)
model_name = "qwen-plus"
model = Model(model_name)


def collect_taco():
    print("Loading dataset...")
    dataset = load_dataset("BAAI/TACO", split="train")

    output_file = "taco.jsonl"

    print("Processing dataset...")

    with jsonlines.open(output_file, "w") as writer:
        data = {}
        for sample in tqdm(dataset, desc="Processing samples"):
            data["requirement"] = sample["question"]
            data["solutions"] = json.loads(sample["solutions"])
            input_output = json.loads(sample["input_output"])
            data["inputs"] = input_output["inputs"]
            data["outputs"] = input_output["outputs"]
            data["starter_code"] = sample["starter_code"]

            writer.write(data)

    print(f"Dataset successfully processed and saved to {output_file}")


def remove_example_geeksforgeeks(origin):
    lindex = origin.find("Example 1")
    rindex = origin.find("Your Task:  \nYou dont need to read input or print anything.")
    return origin[:lindex] + origin[rindex:]


instruction_remove_example = "You are an assistant that removes examples from a programming problem description."


def prompt_remove_example(origin):
    prompt = """
    Remove all examples from the provided programming problem description, including sample inputs/outputs, in-text illustrations (e.g., 'for example, if...'), or standalone example sections. Retain all other content such as the problem statement, constraints, notes, and explanations that are not explicitly part of an example. Do not modify, rephrase, or delete any non-example text.
    Wrap the modified description in <requirement></requirement> tags.
    """ + origin
    return prompt


def remove_example(requirement):
    response = model.get_response(instruction_remove_example, prompt_remove_example(requirement))
    return unwrap(response, "requirement")


def taco_ambiguous_collection():
    def process_obj(idx, obj):
        if "Your Task:  \nYou dont need to read input or print anything." in obj['requirement']:
            obj['requirement'] = remove_example_geeksforgeeks(obj['requirement'])
        else:
            obj['requirement'] = remove_example(obj['requirement'])
        return (idx, obj)

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


instruction_revise = "You are an assistant that revises inputs and outputs format for a programming problem."


def prompt_revise(requirement, inputs, outputs):
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


def revise_data(requirement, inputs, outputs, instruction, prompt_func, programs, entry_point, validator,
                max_retries=3):
    print("REVISING")
    original_inputs = inputs
    original_outputs = outputs
    valid_programs = []
    for program in programs:
        try:
            valid_programs.append(transform_code(program))
        except:
            pass

    # initial revision
    if not validator(inputs):
        inputs = [[inp] for inp in inputs]
    if not validator(outputs):
        outputs = [[out] for out in outputs]
    for program in valid_programs:
        results = execute_inputs(program, inputs, entry_point)
        if compare(results, outputs):
            return inputs, outputs, program

    # LLM revision
    for attempt in range(1, max_retries + 1):
        try:
            response = model.get_response(instruction, prompt_func(requirement, original_inputs, original_outputs))
            inputs = unwrap(response, "input")
            outputs = unwrap(response, "output")
            parsed_inputs = ast.literal_eval(inputs)
            parsed_outputs = ast.literal_eval(outputs)

            if len(parsed_inputs) == 0:
                raise ValueError("Empty inputs after parsing")

            if not validator(parsed_inputs):
                raise ValueError("Input validation failed")

            filtered_inputs = [item for item in parsed_inputs if item != []]

            if len(parsed_outputs) == 0:
                raise ValueError("Empty outputs after parsing")

            if not validator(parsed_outputs):
                raise ValueError("Output validation failed")

            filtered_outputs = [item for item in parsed_outputs if item != []]
            if not filtered_inputs or not filtered_outputs:
                raise ValueError("Empty inputs or outputs after filtering")

            for program in valid_programs:
                results = execute_inputs(program, filtered_inputs, entry_point)
                if compare(results, filtered_outputs):
                    print(f"Success after {attempt} attempt(s)")
                    return filtered_inputs, filtered_outputs, program
            return filtered_inputs, filtered_outputs, None

        except Exception as e:
            print(f"Attempt {attempt} failed: {str(e)}")
            if attempt == max_retries:
                return None, None, None


def cut_inputs_outputs(inputs, outputs):
    while len(str(inputs)) > 10000 or len(str(outputs)) > 10000:
        inputs = inputs[:len(inputs) - 1]
        outputs = outputs[:len(outputs) - 1]
    return inputs, outputs


def process_entry(obj):
    if not obj.get('requirement'):
        # if not obj.get('requirement') or len(obj['requirement']) > 2000:
        return None
    if any("\n" in inp for inp in obj['inputs'] if isinstance(inp, str)):
        return None
    if any("\n" in out for out in obj['outputs'] if isinstance(out, str)):
        return None

    inputs, outputs = cut_inputs_outputs(obj['inputs'], obj['outputs'])
    # inputs, outputs = obj['inputs'], obj['outputs']
    if len(inputs) < 3:
        return None
    starter_code = obj["starter_code"]
    target_solutions = []
    for code in obj['solutions']:
        if "stdin" not in code and "input(" not in code and "print(" not in code:
            target_solutions.append(code)
    entry_point = starter_code[starter_code.find("def ") + 4:starter_code.find("(", starter_code.find("def ") + 4)]
    inputs, outputs, program = revise_data(obj["requirement"], inputs, outputs, instruction_revise, prompt_revise,
                                           target_solutions, entry_point,
                                           lambda x: isinstance(x, list) and all(isinstance(i, list) for i in x), 3)

    if not program:
        return None

    obj['canonical_solution'] = program.replace(entry_point, entry_point.lower())
    obj.pop('solutions')
    obj["requirement"] = obj["requirement"].replace(entry_point, entry_point.lower())
    obj['entry_point'] = entry_point.lower()
    obj['inputs'] = inputs
    obj['outputs'] = outputs

    for line in obj['canonical_solution'].split("\n"):
        if f"def {obj["entry_point"]}(" in line:
            def_line = line.strip()
            obj['starter_code'] = def_line
            obj['requirement'] = f"{def_line}\n\"\"\"{obj['requirement'].strip()}\n\"\"\""
            break

    return obj


def clean_taco():
    with jsonlines.open("taco.jsonl") as reader:
        objs = list(reader)
    print(f"Loaded {len(objs)} entries")

    with jsonlines.open("taco_clean.jsonl", "a", flush=True) as writer:
        for i, obj in tqdm(enumerate(objs), total=len(objs), desc="Cleaning entries"):
            print("Processing", i)
            obj = process_entry(obj)
            if obj:
                writer.write(obj)


# clean_taco()
# collect_taco()
taco_ambiguous_collection()
