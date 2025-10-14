import argparse
import os
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
from pathlib import Path
from typing import Any, Dict, Optional

import jsonlines

from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.tester import differential_tester, ground_truth_tester
from specfix.utils import (
    construct_output_file,
    get_inputs_outputs,
    read_jsonl,
    summarize_result,
)

_STATE: Dict[str, Any] = {
    "evaluator": None,
    "inputs": None,
    "outputs": None,
    "cluster_sample_size": None,
    "evaluation_sample_size": None,
    "passk": None,
}


def _worker_init(
    model_name: str,
    temperature: Optional[float],
    dataset: str,
    path: str,
    cluster_sample_size: int,
    evaluation_sample_size: int,
    passk: int,
) -> None:
    evaluator = SpecFixAccuracyEvaluator(
        differential_tester, ground_truth_tester, model_name, temperature
    )
    inputs, outputs = get_inputs_outputs(dataset, path)
    _STATE.update(
        {
            "evaluator": evaluator,
            "inputs": inputs,
            "outputs": outputs,
            "cluster_sample_size": cluster_sample_size,
            "evaluation_sample_size": evaluation_sample_size,
            "passk": passk,
        }
    )


def _evaluate_requirement(
    evaluator: SpecFixAccuracyEvaluator,
    requirement: Optional[str],
    clusters,
    inputs,
    outputs,
    entry_point: str,
    passk: int,
    evaluation_sample_size: int,
) -> Dict[str, Any]:
    if requirement is None:
        return {
            "passk": None,
            "avg_pass_rate": None,
            "pass_rate": None,
            "majority_passk": None,
        }

    pass_at_k, avg_pass_rate, _, _ = evaluator.pass_k_and_pass_rate(
        requirement,
        inputs,
        outputs,
        entry_point,
        passk,
        evaluation_sample_size,
    )
    majority = evaluator.solved_with_majority_vote(clusters, inputs, outputs)
    return {
        "passk": pass_at_k,
        "avg_pass_rate": avg_pass_rate,
        "pass_rate": avg_pass_rate,
        "majority_passk": majority,
    }


def _process_problem(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    evaluator: SpecFixAccuracyEvaluator = _STATE["evaluator"]
    inputs = _STATE["inputs"]
    outputs = _STATE["outputs"]

    if evaluator is None or inputs is None or outputs is None:
        raise RuntimeError("Worker not initialized correctly.")

    idx = task["index"]
    problem = task["problem"]
    try:
        input_data = inputs[idx]
        output_data = outputs[idx]
    except IndexError:
        return None

    cluster_sample_size = _STATE["cluster_sample_size"]
    evaluation_sample_size = _STATE["evaluation_sample_size"]
    passk = _STATE["passk"]

    detect_result, original_clusters = evaluator.specfix_detect(
        problem, cluster_sample_size
    )
    original_serialized = (
        original_clusters.serialize() if original_clusters is not None else None
    )
    original_result = _evaluate_requirement(
        evaluator,
        problem.get("requirement"),
        original_clusters,
        input_data,
        output_data,
        problem.get("entry_point"),
        passk,
        evaluation_sample_size,
    )

    repaired_requirement: Optional[str] = None
    repaired_clusters_serialized = None
    repaired_result: Optional[Dict[str, Any]] = None

    if detect_result and original_clusters is not None:
        print("Ambiguity detected, attempting repair...")
        repaired_requirement, repaired_clusters = evaluator.specfix_repair(
            original_clusters, cluster_sample_size
        )
        repaired_clusters_serialized = (
            repaired_clusters.serialize() if repaired_clusters is not None else None
        )
        repaired_result = _evaluate_requirement(
            evaluator,
            repaired_requirement,
            repaired_clusters,
            input_data,
            output_data,
            problem.get("entry_point"),
            passk,
            evaluation_sample_size,
        )
    else:
        print("No ambiguity detected.")
    return summarize_result(
        problem,
        repaired_requirement,
        original_serialized,
        repaired_clusters_serialized,
        original_result,
        repaired_result,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--dataset",
        required=True,
        help="Dataset: humaneval, mbpp and livecodebench",
    )
    parser.add_argument("-p", "--path", required=True, help="Dataset Path")
    parser.add_argument("-c", "--cluster_sample_size", type=int, default=20)
    parser.add_argument("-e", "--evaluation_sample_size", type=int, default=10)
    parser.add_argument(
        "-k", "--passk", type=int, default=1, help="Pass@k value for evaluation"
    )
    parser.add_argument("-m", "--model", type=str, required=True)
    parser.add_argument("-t", "--temperature", type=float, default=None)
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes for parallel execution",
    )
    options = parser.parse_args()

    output_file = construct_output_file(
        Path(__file__).resolve().parent, options.model, options.dataset, "Results"
    )
    problems = read_jsonl(options.path)
    tasks = [{"index": idx, "problem": problem} for idx, problem in enumerate(problems)]

    max_workers = options.workers or 1

    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=_worker_init,
        initargs=(
            options.model,
            options.temperature,
            options.dataset,
            options.path,
            options.cluster_sample_size,
            options.evaluation_sample_size,
            options.passk,
        ),
    ) as executor:
        results = [
            summary
            for summary in executor.map(_process_problem, tasks)
            if summary is not None
        ]

    with jsonlines.open(output_file, "w") as writer:
        writer.write_all(results)


if __name__ == "__main__":
    main()
