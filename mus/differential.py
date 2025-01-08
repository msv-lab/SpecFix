from .cluster import Cluster
from .utils import execute_inputs, execute_requirement, check_discrepancy
from .model import Model


def differential_tester(generated_programs, test_inputs):
    # Store test results
    program_clusters = []
    # Test each generated program against the reference
    for program_str in generated_programs:
        result_list = execute_inputs(program_str, test_inputs)
        result_tuple = tuple(result_list)

        # Use class Cluster to add program to cluster
        for cluster in program_clusters:
            if result_tuple == cluster.outputs:
                cluster.add_program_str(program_str)
                break
        else:
            new_cluster = Cluster(result_tuple)
            new_cluster.add_program_str(program_str)
            program_clusters.append(new_cluster)
    return program_clusters


def requirement_differential_tester(requirement, test_inputs, num, model, api_key, temperature):
    model = Model(model, api_key, temperature)
    # Store test results
    program_clusters = []
    # Test each generated program against the reference
    for i in range(num):
        result = []
        probes = []
        for inp in test_inputs:
            res, description = execute_requirement(requirement, inp, model)
            result.append(res)
            probes.append(description)
        result_tuple = tuple(result)

        # Use class Cluster to add program to cluster
        if result_tuple not in [cluster.outputs for cluster in program_clusters]:
            new_cluster = Cluster(result_tuple)
            new_cluster.set_probe(probes)
            program_clusters.append(new_cluster)

    return program_clusters


def model_verifier(requirement, program, inp, outputs, model="o1-mini", api_key=None, temperature=1):
    model = Model(model, api_key, temperature)
    result = check_discrepancy(requirement, program, inp, outputs, model)
    if result.startswith("Yes"):
        return True
    return False
