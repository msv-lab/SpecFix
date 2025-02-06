"""
download_taco.py

Downloads the TACO dataset, extracts the relevant fields,
and writes the processed samples to "taco.jsonl".
"""

import json
import jsonlines
from datasets import load_dataset
from tqdm import tqdm


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
