import math
import sys
from specfix.utils import wilson_lower

sys.set_int_max_str_digits(0)


class Clusters:
    def __init__(self):
        self.clusters = []  # list of clusters.
        self.entropy = 0  # entropy of the clusters.
        self.entropy_inputs = []  # LLM generated test inputs for entropy measure.
        self.semantic_inputs_outputs = []  # input output examples for semantic measure
        self.at_least_one_align = False  # whether at least one cluster is aligned with the examples.
        self.ambiguity = 0  # ambiguity of the clusters.

    def add_cluster(self, cluster):
        self.clusters.append(cluster)

    def get_clusters(self):
        return self.clusters

    def set_entropy_inputs(self, entropy_inputs):
        self.entropy_inputs = entropy_inputs

    def set_semantic_inputs_outputs(self, semantic_inputs_outputs):
        self.semantic_inputs_outputs = semantic_inputs_outputs

    def set_at_least_one_align(self):
        self.at_least_one_align = True if any([cluster.is_align_req for cluster in self.clusters]) else False

    def calculate_distribution(self):
        total = sum([len(cluster.programs_str) for cluster in self.clusters])
        for cluster in self.clusters:
            cluster.probability = len(cluster.programs_str) / total

    def calculate_entropy(self):
        total = sum([cluster.probability for cluster in self.clusters])
        self.entropy = sum(
            [-cluster.probability / total * math.log(cluster.probability / total) for cluster in self.clusters])

    def get_largest_cluster(self):
        return max(self.clusters, key=lambda cluster: cluster.probability)

    def get_largest_two_clusters(self):
        return sorted(self.clusters, key=lambda cluster: cluster.probability, reverse=True)[:2]

    def serialize(self):
        return {
            'clusters': [cluster.serialize() for cluster in self.clusters],
            'entropy': self.entropy,
            'LLM_generated_inputs': self.entropy_inputs if any(
                isinstance(i, set) for i in self.entropy_inputs) else str(
                self.entropy_inputs),
            'input_output_examples': self.semantic_inputs_outputs,
            'at_least_one_align': self.at_least_one_align
        }

    def calculate_ambiguity(self):
        weighted_t_consistency = sum(
            [wilson_lower(cluster.test_consistency, len(self.semantic_inputs_outputs)) * cluster.probability for cluster
             in self.clusters])
        self.ambiguity = self.entropy * (1 - weighted_t_consistency)


class Cluster:
    def __init__(self, entropy_outputs):
        self.programs_str = []  # list of programs in the cluster.
        self.requirement = []  # TODO: future work for inverse requirement.
        self.is_align_req = False  # whether the requirement is aligned with the examples.
        self.entropy_outputs = entropy_outputs  # the corresponding outputs for LLM generated test inputs in entropy measure.
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
