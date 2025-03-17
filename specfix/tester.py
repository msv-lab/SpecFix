from specfix.cluster import Clusters, Cluster
from specfix.utils import execute_inputs, compare, get_failed_input_output, crosshair_compare


def differential_tester(generated_programs, test_inputs, entry_point):
    # Store test results
    program_clusters = Clusters()
    program_clusters.set_llm_generated_inputs(test_inputs)
    # Test each generated program against the reference
    for program_str in generated_programs:
        if program_str == "":
            continue
        result_list = execute_inputs(program_str, test_inputs, entry_point)

        # Use class Cluster to add program to cluster
        for cluster in program_clusters.cluster_list:
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
    program_clusters.calculate_probability()
    program_clusters.calculate_entropy()
    return program_clusters


def differential_tester_crosshair(generated_programs, entry_point):
    program_clusters = Clusters()
    for program_str in generated_programs:
        for cluster in program_clusters.cluster_list:
            if crosshair_compare(cluster.programs_str[0], program_str, entry_point):
                cluster.add_program_str(program_str)
                break
        else:
            new_cluster = Cluster()
            new_cluster.add_program_str(program_str)
            program_clusters.add_cluster(new_cluster)
    program_clusters.calculate_probability()
    program_clusters.calculate_entropy()
    return program_clusters


def ground_truth_tester(clusters):
    for cluster in clusters.cluster_list:
        program_str = cluster.programs_str[0]
        inputs, outputs = clusters.input_output_examples
        if inputs == [] or outputs == []:
            cluster.test_consistency = -1
            cluster.is_align_req = -1
        else:
            result_list = execute_inputs(program_str, inputs, clusters.entry_point)
            failed_input_output_examples, test_consistency = get_failed_input_output(result_list,
                                                                                     inputs, outputs)
            cluster.failed_input_output_examples = failed_input_output_examples
            cluster.test_consistency = test_consistency
            if test_consistency == 1:
                cluster.is_align_req = 1
    clusters.set_at_least_one_align()
    return clusters
