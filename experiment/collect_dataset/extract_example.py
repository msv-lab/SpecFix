import jsonlines
import re
import ast
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from specfix.model import Model

# Allow very large integers (for Python 3.11+)
sys.set_int_max_str_digits(0)


# --- Configuration and Model Initialization ---
def load_config_and_model():
    model_name = "gpt-4o"
    return Model(model_name)


model = load_config_and_model()


# --- Utility Functions ---
def post_process(text: str) -> str:
    """Extract code from a markdown code block."""
    for pattern in (r'```python\s*(.*?)\s*```', r'```(.*?)```'):
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            return match.group(1)
    return text.strip()


def unwrap(string: str, label: str) -> str:
    """Extract content between <label> and </label>. Also post-process code blocks if needed."""
    open_tag = f"<{label}>"
    close_tag = f"</{label}>"
    if open_tag in string and close_tag in string and string.index(open_tag) < string.index(close_tag):
        string = string.split(open_tag, 1)[1].split(close_tag, 1)[0].strip()
    if "```" in string and label in {"code", "test"}:
        string = post_process(string)
    return string


# --- Prompt Templates ---
instruction_extract_example = (
    "You are an assistant that extracts examples from a programming problem description."
)
instruction_repair_response = (
    "You are an assistant that repairs a response based on a programming problem description."
)


def prompt_extract_example(requirement) -> str:
    return f"""
You are given the following programming problem description. Your task is to locate and extract *all example cases* found in the description, including sample inputs/outputs, in-text illustrations (e.g., 'for example, if...'), or standalone example sections. 

An "example" includes sample input and output pairs.

Please provide the extracted examples in the following format:
<example>
<input>EXAMPLE1 ARGUMENTS</input><output>EXAMPLE1 OUTPUTS</output>
<input>EXAMPLE2 ARGUMENTS</input><output>EXAMPLE2 OUTPUTS</output>
...
</example>

Do not include function name, only the arguments. Ensure that you keep the types of the arguments. Store inputs/outputs in one example in one list. If it is a list, nest it inside the outer list.

For example,
assert check_tuplex(("w", 3, "r", "e", "s", "o", "u", "r", "c", "e"),'r')==True should be 
<input>[("w", 3, "r", "e", "s", "o", "u", "r", "c", "e"), 'r']</input><output>[True]</output>.
assert sum_of_squares([1, 2, 3, 4, 5])==55 should be 
<input>[[1, 2, 3, 4, 5]]</input><output>[55]</output>.
assert how_many_times('', 'a') == 0 should be 
<input>['', 'a']</input><output>[0]</output>.

If there are no examples, respond with <example></example>.

Here is the problem description:
{requirement}
"""


def prompt_repair_response(description, response) -> str:
    return f"""
You are given the following programming problem description and an incorrect example extraction from the description. Your task is to repair the response based on the problem description.

All responses are in the following format:
<input>[xxx]</input><output>[xxx]</output>

There are several reasons why the response may be incorrect:
1. The response may miss quotation marks when problem descriptions require the type should be string. For example, <input>["GEEK"]</input><output>[EEKGAY]</output> should be <input>["GEEK"]</input><output>["EEKGAY"]</output>.
2. The response may miss commas. For example, <input>[25, 35]</input><output>[7 5]</output> should be <input>[25, 35]</input><output>[7, 5]</output>.
3. The response may miss brackets. For example, <input>25, 35</input><output>75</output> should be <input>[25, 35]</input><output>[75]</output>.

Please repair the response based on the problem description, wrapped in the <response></response> tag.
Here is the problem description:
{description}

Here is the incorrect response:
{response}
"""


# --- Main Extraction Function ---
def extract(problem: dict, requirement: str) -> dict:
    """
    Extracts examples from a problem description using the model. In case of
    parsing errors, attempts to repair the response.
    """
    try:
        prompt = prompt_extract_example(requirement)
        response = model.get_response(instruction_extract_example, prompt)
    except Exception as e:
        print(f"Final error during extraction: {e}")
        print(prompt_extract_example(requirement))
        response = requirement  # Fallback: use requirement text

    response = unwrap(response, "example")
    inputs_list = []
    outputs_list = []

    for example in response.splitlines():
        try:
            inp = ast.literal_eval(unwrap(example, "input"))
            output = unwrap(example, "output")
            # Replace lower-case booleans for correct evaluation
            output = output.replace("false", "False").replace("true", "True")
            oup = ast.literal_eval(output)
            if not isinstance(inp, list) or not isinstance(oup, list):
                raise ValueError("Parsed example is not a list.")
            inputs_list.append(inp)
            outputs_list.append(oup)
        except Exception:
            # Attempt to repair the response using the repair prompt
            repair_prompt = prompt_repair_response(requirement, example)
            repaired_example = model.get_response(instruction_repair_response, repair_prompt)
            repaired_example = unwrap(repaired_example, "response")
            try:
                inp = ast.literal_eval(unwrap(repaired_example, "input"))
                output = unwrap(repaired_example, "output")
                output = output.replace("false", "False").replace("true", "True")
                oup = ast.literal_eval(output)
                inputs_list.append(inp)
                outputs_list.append(oup)
            except Exception as repair_err:
                print(f"Error repairing example: {repaired_example}\nError: {repair_err}")
                # In case of an unrecoverable error, clear examples and break out.
                inputs_list.clear()
                outputs_list.clear()
                break

    problem["input_output_examples"] = str([inputs_list, outputs_list])
    return problem


# --- Main Function ---
def main():
    max_workers = 100
    results = []

    # Open dataset and output file with context managers.
    with jsonlines.open("humaneval.jsonl") as reader, \
            jsonlines.open("humaneval_example.jsonl", mode='w', flush=True) as writer:

        # Load all problems so that we can count them for tqdm.
        problems = list(reader)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all extraction tasks
            future_to_problem = {
                executor.submit(extract, problem, problem["requirement"]): problem
                for problem in problems
            }

            # Process completed futures with a progress bar.
            for future in tqdm(as_completed(future_to_problem), total=len(future_to_problem), desc="Processing"):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error processing problem: {e}")

        # Sort results based on task_id (or other key as needed)
        results.sort(key=lambda x: int(x.get("task_id", "").split("/")[-1]))

        # Write each processed problem to the output file.
        for item in results:
            writer.write(item)


def manually_extract():
    with jsonlines.open("humaneval_example.jsonl") as reader, jsonlines.open("humaneval_example1.jsonl", "w",
                                                                        flush=True) as writer:
        count = 0
        for problem in reader:
            try:
                examples = ast.literal_eval(problem["input_output_examples"])
                if examples == [[], []]:
                    print(problem["task_id"])
                    print(problem["requirement"])
                    examples = input("Enter examples: ")
                    problem["input_output_examples"] = examples
                    count += 1
            except Exception as e:
                print(problem["task_id"])
                print(problem["requirement"])
                examples = input("Enter examples: ")
                problem["input_output_examples"] = examples
            writer.write(problem)
        print(count)

if __name__ == '__main__':
    # main()
    manually_extract()
