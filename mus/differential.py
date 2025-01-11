from mus.cluster import Cluster
from mus.utils import execute_inputs, execute_requirement, check_discrepancy
from mus.model import Model
from mus.utils import judge_discrepancy_probe


def differential_tester(generated_programs, test_inputs, entry_point):
    # Store test results
    program_clusters = []
    # Test each generated program against the reference
    for program_str in generated_programs:
        result_list = execute_inputs(program_str, test_inputs, entry_point)
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


def probe_tester(requirement, num, model):
    # Store test results
    discrepancies = []
    # Test each generated program against the reference
    probes = []
    for i in range(num):
        probe = execute_requirement(requirement, model)
        probes.append(probe)
    result = judge_discrepancy_probe(requirement, probes, model)
    if not result or "no discrepancies" in result.lower():
        return ""
    else:
        return result


def model_verifier(requirement, program, inp, outputs, model="o1-mini", api_key=None, temperature=1):
    model = Model(model, api_key, temperature)
    answer, explanation = check_discrepancy(requirement, program, inp, outputs, model)
    if answer.startswith("Yes"):
        return True, ""
    return False, explanation
