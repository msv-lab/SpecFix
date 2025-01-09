# MUS

This repository provides a Python-based tool for **Minimal Unambiguous Requirements**(MUS) using language model APIs (
e.g., OpenAI or Qwen). It contains an end-to-end workflow for:

1. Generating multiple candidate programs for a given requirement.
2. Testing these programs in parallel to identify clusters of functionally equivalent implementations.
3. Automatically refining requirements based on clarifications and test outputs to guide subsequent code generation, in
   a loop until convergence or until a maximum number of iterations is reached.
4. Tracking and reporting on accuracy metrics (e.g., success rate, iteration count).

## Table of Contents

- [Dataset](#dataset)
- [Installation](#installation)
- [Usage](#usage)
    - [Command-Line Arguments](#command-line-arguments)
- [Prompt](#prompt)
- [Contributing](#contributing)

## Dataset

We use three datasets in our experiments: Humaneval+, MBPP+, and TACO_lite. Humaneval+ and MBPP+ can be accessed from
third library evalplus. TACO_lite is a dataset that is automatically removed examples or explanations, introducing
ambiguity.
You can find TACO_lite in `dataset` folder.

## Installation

1. Clone the repository (or copy the script) to your local environment:
   ```bash
   git clone https://github.com/msv-lab/mus.git
   cd mus
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Make sure you have the following libraries installed (they might already be in the `requirements.txt`):
   - `openai`
   - `jsonlines`
   - `evalplus`

## Usage

After installing the requirements, run the main script with the appropriate command-line arguments:

```bash
python main.py --dataset <dataset_name> \
               --dataset_path <path_to_data> \
               --api-key <YOUR_OPENAI_API_KEY> \
               --model <openai_or_qwen_model_name> \
               --temperature <model_temperature> \
               --num-programs <N> \
               --max-iterations <max_iterations>
```

### Command-Line Arguments

- **`--dataset`** (str): Name of the dataset to load (e.g., `taco`, `humaneval`, `mbpp`).
- **`--dataset_path`** (str): Path to the dataset JSONL or data source file.
- **`--api-key`** (str): Your OpenAI (or Qwen) API key.
- **`--model`** (str): The model name to use (e.g., `gpt-3.5-turbo`, `qwen2.5-coder-7b-instruct`, etc.).
- **`--temperature`** (float): The temperature for the language model (creativity knob).
- **`--num-programs`** (int): How many candidate programs to generate per iteration.
- **`--max-iterations`** (int): The maximum number of refinement iterations.

### Prompt

All prompts used in the experiments are stored in the `prompts.py`, including prompt for code generation, test
generation, and requirement refinement, etc.

## Contributing

Contributions, bug reports, and feature requests are welcome! Please open issues or submit pull requests.