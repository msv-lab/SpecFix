import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from specfix.cluster import Cluster, Clusters
from specfix.execute_util import check_correctness, get_execution_output
from specfix.utils import compare, crosshair_compare

Signature = Tuple[str, ...]


def _execution_signature(results: Sequence) -> Signature:
    try:
        return tuple(
            result.strip() if isinstance(result, str) else repr(result)
            for result in results
        )
    except Exception:
        return tuple(repr(result) for result in results)


def _run_programs(
    programs: Sequence[str],
    test_inputs: Iterable,
    entry_point: str,
) -> List:
    max_workers = min((os.cpu_count() or 1) * 2, len(programs), 32)
    if max_workers <= 0:
        return []

    def _execute(program_str: str):
        return get_execution_output(program_str, test_inputs, entry_point)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(_execute, programs))


def _assign_cluster(
    clusters: Clusters,
    signature_map: Dict[Signature, Cluster],
    program_str: str,
    outputs,
) -> None:
    signature = _execution_signature(outputs)
    existing = signature_map.get(signature)
    if existing is not None:
        existing.add_program_str(program_str)
        return


    new_cluster = Cluster()
    new_cluster.entropy_outputs = outputs
    new_cluster.add_program_str(program_str)
    clusters.add_cluster(new_cluster)
    signature_map[signature] = new_cluster


def differential_tester(generated_programs, test_inputs, entry_point):
    clusters = Clusters()
    clusters.set_llm_generated_inputs(test_inputs)

    program_list = [program for program in generated_programs if program]
    if not program_list:
        clusters.calculate_probability()
        clusters.calculate_entropy()
        return clusters

    outputs = _run_programs(program_list, test_inputs, entry_point)

    signature_map: Dict[Signature, Cluster] = {}

    for program_str, result_list in zip(program_list, outputs):
        _assign_cluster(clusters, signature_map, program_str, result_list)

    clusters.calculate_probability()
    clusters.calculate_entropy()
    return clusters


def _find_matching_cluster(
    clusters: Clusters,
    program_str: str,
    entry_point: str,
) -> Optional[Cluster]:
    for cluster in clusters.cluster_list:
        if crosshair_compare(cluster.programs_str[0], program_str, entry_point):
            return cluster
    return None


def differential_tester_crosshair(generated_programs, entry_point):
    clusters = Clusters()
    for program_str in generated_programs:
        if not program_str:
            continue
        cluster = _find_matching_cluster(clusters, program_str, entry_point)
        if cluster is None:
            cluster = Cluster()
            cluster.add_program_str(program_str)
            clusters.add_cluster(cluster)
        else:
            cluster.add_program_str(program_str)

    clusters.calculate_probability()
    clusters.calculate_entropy()
    return clusters


def ground_truth_tester(clusters):
    input_output_examples = clusters.input_output_examples or []
    if len(input_output_examples) != 2:
        inputs = outputs = []
    else:
        inputs, outputs = input_output_examples

    for cluster in clusters.cluster_list:
        _evaluate_cluster_against_examples(cluster, inputs, outputs, clusters.entry_point)

    clusters.set_at_least_one_align()
    clusters.calculate_test_consistency()
    return clusters


def _evaluate_cluster_against_examples(
    cluster: Cluster,
    inputs,
    outputs,
    entry_point: str,
) -> None:
    if not inputs or not outputs:
        cluster.test_consistency = -1
        cluster.is_align_req = -1
        cluster.failed_input_output_examples = []
        return

    program_str = cluster.programs_str[0]
    results, meta_data = check_correctness(program_str, inputs, outputs, entry_point)
    cluster.failed_input_output_examples = meta_data
    cluster.test_consistency = results.count(True) / len(results) if results else 0
    if cluster.test_consistency == 1:
        cluster.is_align_req = 1
