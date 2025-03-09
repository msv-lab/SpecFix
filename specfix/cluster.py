import ast

import math
import sys

from specfix.utils import wilson_lower

sys.set_int_max_str_digits(0)


class Clusters:
    def __init__(self):
        self.cluster_list = []  # list of clusters.
        self.entropy = 0  # entropy of the clusters.
        self.llm_generated_inputs = []  # LLM generated test inputs for entropy measure.
        self.input_output_examples = []  # input output examples for semantic measure
        self.at_least_one_align = None  # whether at least one cluster is aligned with the examples.
        self.weighted_test_consistency = 0  # weighted test consistency for semantic measure.
        self.ambiguity = 0  # ambiguity of the clusters.

    def add_cluster(self, cluster):
        self.cluster_list.append(cluster)

    def get_cluster_list(self):
        return self.cluster_list

    def set_llm_generated_inputs(self, llm_generated_inputs):
        self.llm_generated_inputs = llm_generated_inputs

    def set_input_output_examples(self, input_output_examples):
        self.input_output_examples = eval(input_output_examples)

    def set_at_least_one_align(self):
        self.at_least_one_align = True if any([cluster.is_align_req for cluster in self.cluster_list]) else False

    def calculate_distribution(self):
        total = sum([len(cluster.programs_str) for cluster in self.cluster_list])
        for cluster in self.cluster_list:
            cluster.probability = len(cluster.programs_str) / total

    def calculate_entropy(self):
        total = sum([cluster.probability for cluster in self.cluster_list])
        entropy = sum(
            [-cluster.probability / total * math.log(cluster.probability / total) for cluster in self.cluster_list])
        self.entropy = 0 if (len(self.cluster_list) == 1 or len(self.cluster_list) == 0) else entropy / math.log(
            len(self.cluster_list))

    def get_largest_cluster(self):
        return max(self.cluster_list, key=lambda cluster: cluster.probability)

    def serialize(self):
        return {
            'cluster_list': [cluster.serialize() for cluster in self.cluster_list],
            'entropy': self.entropy,
            'llm_generated_inputs': str(self.llm_generated_inputs),
            'input_output_examples': str(self.input_output_examples),
            'weighted_test_consistency': self.weighted_test_consistency,
            'at_least_one_align': self.at_least_one_align,
            'ambiguity': self.ambiguity
        }

    def deserialize(self, data):
        self.cluster_list = [Cluster().deserialize(cluster) for cluster in data['cluster_list']]
        self.entropy = data['entropy']
        self.llm_generated_inputs = ast.literal_eval(data['llm_generated_inputs'])
        self.input_output_examples = ast.literal_eval(data['input_output_examples'])
        self.at_least_one_align = data['at_least_one_align']
        self.weighted_test_consistency = data["weighted_test_consistency"]
        self.ambiguity = data['ambiguity']
        return self

    def calculate_ambiguity(self):
        # self.weighted_t_consistency = sum(
        #     [wilson_lower(cluster.test_consistency, len(self.input_output_examples)) * cluster.probability for cluster
        #      in self.cluster_list])
        self.weighted_test_consistency = sum(
            [cluster.test_consistency * cluster.probability for cluster in self.cluster_list])
        self.ambiguity = (self.entropy + (1 - self.weighted_test_consistency)) / 2


class Cluster:
    def __init__(self):
        self.programs_str = []  # list of programs in the cluster.
        self.is_align_req = False  # whether the requirement is aligned with the examples.
        self.entropy_outputs = []  # the corresponding outputs for LLM generated test inputs in entropy measure.
        self.failed_input_output_examples = []  # failed input output examples in semantic measure. (input, output, expected)
        self.test_consistency = 0  # test consistency for semantic measure.
        self.probability = 0  # probability of the cluster.

    def add_program_str(self, program_str):
        self.programs_str.append(program_str)

    def align(self):
        self.is_align_req = True

    def serialize(self):
        return {
            'programs_str': self.programs_str,
            'outputs': str(self.entropy_outputs),
            'probability': self.probability,
            'is_align_req': self.is_align_req,
            'test_consistency': self.test_consistency,
            'failed_input_output_examples': str(self.failed_input_output_examples)
        }

    def deserialize(self, data):
        self.programs_str = data['programs_str']
        self.entropy_outputs = data['outputs']
        self.probability = data['probability']
        self.is_align_req = data['is_align_req']
        self.test_consistency = data['test_consistency']
        # self.failed_input_output_examples = ast.literal_eval(data['failed_input_output_examples'])
        return self
