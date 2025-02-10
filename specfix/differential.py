import random

from specfix.cluster import Cluster, Clusters
from specfix.utils import execute_inputs, check_failed_semantic_input_output, compare


def differential_tester(generated_programs, test_inputs, entry_point):
    # Store test results
    program_clusters = Clusters()
    program_clusters.set_entropy_inputs(test_inputs)
    # Test each generated program against the reference
    for program_str in generated_programs:
        result_list = execute_inputs(program_str, test_inputs, entry_point)

        # Use class Cluster to add program to cluster
        for cluster in program_clusters.get_cluster_list():
            try:
                if compare(result_list, cluster.entropy_outputs):
                    cluster.add_program_str(program_str)
                    break
            except ValueError:
                continue
        else:
            new_cluster = Cluster()
            new_cluster.entropy_outputs = result_list
            new_cluster.add_program_str(program_str)
            program_clusters.add_cluster(new_cluster)
    program_clusters.calculate_distribution()
    program_clusters.calculate_entropy()
    return program_clusters


def ground_truth_tester(clusters, semantic_input_output, entry_point):
    clusters.set_semantic_inputs_outputs(semantic_input_output)
    for cluster in clusters.get_cluster_list():
        program_str = random.choice(cluster.programs_str)
        inputs, outputs = semantic_input_output
        result_list = execute_inputs(program_str, inputs, entry_point)
        failed_semantic_input_output, t_consistency = check_failed_semantic_input_output(result_list,
                                                                                         inputs, outputs)
        cluster.failed_semantic_input_output = failed_semantic_input_output
        cluster.test_consistency = t_consistency
        if t_consistency == 1:
            cluster.align()
    clusters.set_at_least_one_align()
    return clusters
