# SpecFix

SpecFix is a Python toolkit for repairing ambiguous programming problems by combining large language models with differential testing. It detects inconsistencies in task specifications, clusters candidate solutions by behaviour, and iteratively proposes refined requirements that better match the intended solution space.

This repository provides the official implementation and artifact for the ASE 2025 paper *Automated Repair of Ambiguous Problem Descriptions for LLM-Based Code Generation*.

## Table of Contents
- [Features](#features)
- [Repository Layout](#repository-layout)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running SpecFix](#running-specfix)
  - [Command-Line Arguments](#command-line-arguments)
  - [Example](#example)
- [Outputs](#outputs)
- [Datasets](#datasets)
- [Prompt Templates](#prompt-templates)
- [Contributing](#contributing)

## Features
- Detect specification ambiguity via clustering of LLM-generated candidate programs.
- Repair requirements with automated prompt sequencing and requirement refinement.
- Evaluate repaired specifications using pass@k, majority voting, and behavioural metrics.
- Parallel processing pipeline that scales across CPU cores for generation and testing.

## Repository Layout
- `specfix/`: Core library (generation, clustering, evaluation, utilities, prompts).
- `datasets/`: JSONL datasets used in the paper and experiments.
- `requirements.txt`: Python dependencies needed for running SpecFix.

## Requirements
- Python 3.10 or newer.
- Access to one or more supported chat-completion APIs (OpenAI-compatible endpoints).
- System packages required by `evalplus` for executing Python reference solutions.

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

## Installation

```bash
git clone https://github.com/msv-lab/SpecFix.git
cd SpecFix
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running SpecFix
The entry point is `specfix/main.py`, which orchestrates generation, clustering, detection, and repair for every problem in a dataset. Use the module form to ensure the package resources resolve correctly:

```bash
python -m specfix.main \
  -d humaneval \
  -p datasets/humaneval.jsonl \
  -m qwen2.5-coder-7b-instruct
```

### Command-Line Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `-d`, `--dataset` | ✓ | Dataset identifier used for bookkeeping (e.g., `humaneval`, `mbpp`, `livecodebench`). |
| `-p`, `--path` | ✓ | Path to the JSONL file containing problems to process. The format matches the files in `dataset/`. |
| `-m`, `--model` | ✓ | Model name understood by the configured OpenAI-compatible endpoint (e.g., `gpt-4o`, `qwen2.5-coder-7b-instruct`). |
| `-t`, `--temperature` |  | Optional sampling temperature used when generating code (defaults to provider behaviour). |
| `-c`, `--cluster_sample_size` |  | Number of candidate programs generated per requirement during ambiguity detection (default `20`). |
| `-e`, `--evaluation_sample_size` |  | Number of test cases generated when evaluating repaired requirements (default `10`). |
| `-k`, `--passk` |  | Pass@k threshold used by the evaluator when computing metrics (default `1`). |
| `-w`, `--workers` |  | Number of worker processes for parallel execution. Defaults to sequential execution when omitted. |

### Example

```bash
python -m specfix.main \
  -d livecodebench \
  -p datasets/livecodebench.jsonl \
  -m deepseek-v3 \
  -t 0.2 \
  -c 24 \
  -e 12 \
  -k 5 \
  -w 8
```

## Outputs
- Results are written to `specfix/Results/<model>/<timestamp>/<dataset>.jsonl`.
- Each entry includes the original requirement, detected clusters, repaired requirement (if produced), and summary metrics (`passk`, `avg_pass_rate`, majority voting outcome).
- Intermediate logs include generated code snippets, test cases, and failure diagnostics to support manual analysis.

## Datasets
- Bundled datasets (`dataset/*.jsonl`) follow the structure documented in `dataset/README.md` and include fields such as `requirement`, `entry_point`, `input_output_examples`, `inputs`, and `outputs`.

## Prompt Templates
- Prompt templates for generation, testing, and requirement refinement live in `specfix/prompting.py`.
- Modify these templates to experiment with alternative prompting strategies or to port SpecFix to new instruction-tuned models.


## Contributing
Contributions, bug reports, and feature requests are welcome! Please open issues or submit pull requests.

## Citation
If you use SpecFix or build upon this work, please cite:

> *Automated Repair of Ambiguous Problem Descriptions for LLM-Based Code Generation*, Proceedings of the 40th IEEE/ACM International Conference on Automated Software Engineering (ASE 2025).
