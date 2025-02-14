"""
download_taco.py

Downloads the TACO dataset, extracts the relevant fields,
and writes the processed samples to "taco.jsonl".
"""

import json
import jsonlines
from datasets import load_dataset
from tqdm import tqdm
from evalplus.data import get_mbpp_plus, get_human_eval_plus


def collect_humaneval_mbpp():
    humaneval = get_human_eval_plus()
    mbpp = get_mbpp_plus()

    with jsonlines.open("humaneval.jsonl", "w", flush=True) as writer:
        for key in humaneval.keys():
            result = {}
            problem = humaneval[key]
            result["task_id"] = problem["task_id"]
            result["requirement"] = problem["prompt"]
            result["entry_point"] = problem["entry_point"]
            result["canonical_solution"] = problem["prompt"] + problem["canonical_solution"]
            writer.write(result)

    with jsonlines.open("mbpp.jsonl", "w", flush=True) as writer:
        for key in mbpp.keys():
            result = {}
            problem = mbpp[key]
            result["task_id"] = problem["task_id"]
            result["requirement"] = problem["prompt"]
            result["entry_point"] = problem["entry_point"]
            result["canonical_solution"] = problem["canonical_solution"].strip()
            writer.write(result)


def collect_taco():
    """Download and process the TACO dataset and save it to taco.jsonl."""
    print("Loading dataset...")
    dataset = load_dataset("BAAI/TACO", split="train")
    output_file = "taco.jsonl"
    print("Processing dataset...")

    with jsonlines.open(output_file, "w") as writer:
        for sample in tqdm(dataset, desc="Processing samples"):
            # Create a fresh dictionary for each sample
            data = {
                "requirement": sample["question"],
                "solutions": json.loads(sample["solutions"]),
            }
            # Unpack the JSON string stored in "input_output"
            data.update(json.loads(sample["input_output"]))
            data["starter_code"] = sample["starter_code"]
            writer.write(data)

    print(f"Dataset successfully processed and saved to {output_file}")


if __name__ == "__main__":
    collect_taco()
