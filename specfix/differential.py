from specfix.cluster import Cluster, Clusters
from specfix.utils import execute_inputs, check_discrepancy
from specfix.model import Model


def differential_tester(generated_programs, test_inputs, entry_point):
    # Store test results
    program_clusters = Clusters()
    program_clusters.set_test_inputs(test_inputs)
    # Test each generated program against the reference
    for program_str in generated_programs:
        result_list = execute_inputs(program_str, test_inputs, entry_point)
        result_tuple = tuple(result_list)

        # Use class Cluster to add program to cluster
        for cluster in program_clusters.get_clusters():
            if result_tuple == cluster.outputs:
                cluster.add_program_str(program_str)
                break
        else:
            new_cluster = Cluster(result_tuple)
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
