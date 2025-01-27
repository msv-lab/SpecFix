from specfix.cluster import Cluster, Clusters
from specfix.utils import execute_inputs, check_discrepancy, check_failed_test
from specfix.model import Model


def differential_tester(generated_programs, test_inputs, entry_point):
    # Store test results
    program_clusters = Clusters()
    program_clusters.set_test_inputs(test_inputs)
    # Test each generated program against the reference
    for program_str in generated_programs:
        result_list = execute_inputs(program_str, test_inputs, entry_point)

        # Use class Cluster to add program to cluster
        for cluster in program_clusters.get_clusters():
            try:
                if result_list == cluster.outputs:
                    cluster.add_program_str(program_str)
                    break
            except ValueError:
                continue
        else:
            new_cluster = Cluster(result_list)
            new_cluster.add_program_str(program_str)
            program_clusters.add_cluster(new_cluster)
    program_clusters.calculate_distribution()
    program_clusters.calculate_entropy()
    return program_clusters


def model_verifier(requirement, program, inp, outputs, model="o1-mini", api_key=None, temperature=1):
    model = Model(model, api_key, temperature)
    answer, explanation = check_discrepancy(requirement, program, inp, outputs, model)
    if answer.startswith("Yes"):
        return True, explanation
    return False, explanation


def ground_truth_testing(canonical_solution, clusters, test_inputs, entry_point):
    canonical_outputs = execute_inputs(canonical_solution, test_inputs, entry_point)
    clusters.set_canonical_outputs(canonical_outputs)
    clusters.set_canonical_solution(canonical_solution)
    for cluster in clusters.get_clusters():
        if canonical_outputs == cluster.outputs:
            cluster.align()
            clusters.set_at_least_one_align()
        else:
            cluster.not_align()
            result, ratio = check_failed_test(test_inputs, cluster.outputs, canonical_outputs)
            cluster.set_failed_tests(result)
            cluster.set_test_consistency(ratio)

def calculate_accuracy_ground_truth_testing(canonical_solution, clusters, test_inputs, entry_point):
    canonical_outputs = execute_inputs(canonical_solution, test_inputs, entry_point)
    clusters.set_canonical_outputs(canonical_outputs)
    for cluster in clusters.get_clusters():
        canonical_len = len(canonical_outputs)
        cluster_len = len(cluster.outputs)
        min_length = min(canonical_len, cluster_len)
        
        # Compare outputs up to the shorter length
        matches = sum(1 for i in range(min_length) if canonical_outputs[i] == cluster.outputs[i])
        
        # for i in range(min_length):
        #     if canonical_outputs[i] != cluster.outputs[i]:
        #         print("MISMATCH: ground truth output: ", canonical_outputs[i], " vs cluster output: ", cluster.outputs[i])
        
        total_outputs = max(canonical_len, cluster_len)
        accuracy = (matches / total_outputs)
        
        print(f"Accuracy: {accuracy:.2f}")
        
        cluster.set_accuracy(accuracy)
        
        if accuracy == 1.0:
            cluster.align()
        else:
            cluster.not_align()
    
    clusters.calculate_max_cluster_accuracy()
