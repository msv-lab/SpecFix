import math
import sys

from scipy.cluster.hierarchy import weighted

from specfix.utils import wilson_lower

sys.set_int_max_str_digits(0)


class Clusters:
    def __init__(self):
        self.cluster_list = []  # list of clusters.
        self.entropy = 0  # entropy of the clusters.
        self.entropy_inputs = []  # LLM generated test inputs for entropy measure.
        self.semantic_inputs_outputs = []  # input output examples for semantic measure
        self.at_least_one_align = False  # whether at least one cluster is aligned with the examples.
        self.ambiguity = 0  # ambiguity of the clusters.

    def add_cluster(self, cluster):
        self.cluster_list.append(cluster)

    def get_cluster_list(self):
        return self.cluster_list

    def set_entropy_inputs(self, entropy_inputs):
        self.entropy_inputs = entropy_inputs

    def set_semantic_inputs_outputs(self, semantic_inputs_outputs):
        self.semantic_inputs_outputs = semantic_inputs_outputs

    def set_at_least_one_align(self):
        self.at_least_one_align = True if any([cluster.is_align_req for cluster in self.cluster_list]) else False

    def calculate_distribution(self):
        total = sum([len(cluster.programs_str) for cluster in self.cluster_list])
        for cluster in self.cluster_list:
            cluster.probability = len(cluster.programs_str) / total

    def calculate_entropy(self):
        total = sum([cluster.probability for cluster in self.cluster_list])
        self.entropy = sum(
            [-cluster.probability / total * math.log(cluster.probability / total) for cluster in self.cluster_list])

    def get_largest_cluster(self):
        return max(self.cluster_list, key=lambda cluster: cluster.probability)

    def serialize(self):
        return {
            'cluster_list': [cluster.serialize() for cluster in self.cluster_list],
            'entropy': self.entropy,
            'LLM_generated_inputs': self.entropy_inputs if any(
                isinstance(i, set) for i in self.entropy_inputs) else str(
                self.entropy_inputs),
            'input_output_examples': self.semantic_inputs_outputs,
            'at_least_one_align': self.at_least_one_align
        }

    def deserialize(self, data):
        self.cluster_list = [Cluster().deserialize(cluster) for cluster in data['cluster_list']]
        self.entropy = data['entropy']
        self.entropy_inputs = data['LLM_generated_inputs']
        self.semantic_inputs_outputs = data['input_output_examples']
        self.at_least_one_align = data['at_least_one_align']
        return self

    def calculate_ambiguity(self):
        weighted_t_consistency = sum(
            [wilson_lower(cluster.test_consistency, len(self.semantic_inputs_outputs)) * cluster.probability for cluster
             in self.cluster_list])
        # weighted_t_consistency = sum(
        #     [cluster.test_consistency * cluster.probability for cluster in self.cluster_list])
        self.ambiguity = self.entropy * (1 - weighted_t_consistency)


class Cluster:
    def __init__(self):
        self.programs_str = []  # list of programs in the cluster.
        self.requirement = []  # TODO: future work for inverse requirement.
        self.is_align_req = False  # whether the requirement is aligned with the examples.
        self.entropy_outputs = []  # the corresponding outputs for LLM generated test inputs in entropy measure.
        self.failed_semantic_input_output = []  # failed input output examples in semantic measure. (input, output, expected)
        self.test_consistency = 0  # test consistency for semantic measure.
        self.probability = 0  # probability of the cluster.
        self.DRS = None

    def add_program_str(self, program_str):
        self.programs_str.append(program_str)

    def set_requirement(self, requirement):
        self.requirement = requirement

    def set_DRS(self, DRS):
        self.DRS = DRS

    def align(self):
        self.is_align_req = True

    def serialize(self):
        return {
            'programs_str': self.programs_str,
            'requirement': self.requirement,
            'outputs': str(self.entropy_outputs),
            'probability': self.probability,
            'is_align_req': self.is_align_req,
            'DRS': self.DRS
        }

    def deserialize(self, data):
        self.programs_str = data['programs_str']
        self.requirement = data['requirement']
        self.entropy_outputs = data['outputs']
        self.probability = data['probability']
        self.is_align_req = data['is_align_req']
        self.DRS = data['DRS']
        return self
