import ast

import math
import sys

from specfix.utils import get_exception_list, compare, is_significant_large

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
        self.requirement = ""  # requirement for the clusters.
        self.entry_point = ""

    def add_cluster(self, cluster):
        self.cluster_list.append(cluster)

    def set_requirement(self, requirement):
        self.requirement = requirement

    def set_entry_point(self, entry_point):
        self.entry_point = entry_point

    def set_llm_generated_inputs(self, llm_generated_inputs):
        self.llm_generated_inputs = llm_generated_inputs

    def set_input_output_examples(self, input_output_examples):
        if input_output_examples:
            self.input_output_examples = eval(input_output_examples)

    def set_at_least_one_align(self):
        self.at_least_one_align = True if any([cluster.is_align_req == 1 for cluster in self.cluster_list]) else False

    def calculate_probability(self):
        total = sum([len(cluster.programs_str) for cluster in self.cluster_list])
        for cluster in self.cluster_list:
            cluster.probability = len(cluster.programs_str) / total

    def calculate_entropy(self):
        if len(self.cluster_list) == 1 or len(self.cluster_list) == 0:
            self.entropy = 0
        else:
            entropy = sum([-cluster.probability * math.log(cluster.probability) for cluster in self.cluster_list])
            self.entropy = entropy / math.log(len(self.cluster_list))

    def select_repair_method(self):
        cluster_1 = []
        other_clusters = []
        for cluster in self.cluster_list:
            if cluster.test_consistency == 1:
                cluster_1.append(cluster)
            else:
                other_clusters.append(cluster)
        if self.weighted_test_consistency == -1: # No example in requirement
            return 3, other_clusters
        if not cluster_1:  # no cluster with test consistency 1
            largest_cluster = max(other_clusters, key=lambda x: x.probability)
            return 0, largest_cluster
        if len(cluster_1) == 1:  # only one cluster with test consistency 1
            return 1, cluster_1[0]
        prob_list = [cluster.probability for cluster in cluster_1]
        if is_significant_large(
                prob_list):  # multiple clusters with test consistency 1 and significant large probabilities
            return 2, max(cluster_1, key=lambda x: x.probability)
        return 3, cluster_1  # multiple clusters with test consistency 1 and no significant large probabilities

    def get_other_clusters_and_diff_outputs(self, inputs, cluster):
        cluster_1 = []
        for cluster1 in self.cluster_list:
            if cluster1.test_consistency == 1 and cluster1 != cluster:
                cluster_1.append(cluster1)
        final_clusters = []
        exception_list = get_exception_list()
        for o_cluster in cluster_1:
            if not all(output in exception_list for output in o_cluster.entropy_outputs):
                final_clusters.append(o_cluster)
        diff_outputs = []
        for o_cluster in final_clusters:
            for i in range(len(o_cluster.entropy_outputs)):
                if "Error" not in o_cluster.entropy_outputs[i]:
                    if not compare(o_cluster.entropy_outputs[i], cluster.entropy_outputs[i]):
                        diff_outputs.append([inputs[i], o_cluster.entropy_outputs[i], cluster.entropy_outputs[i]])
        return final_clusters, diff_outputs

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
        self.is_align_req = 0  # whether the requirement is aligned with the examples.
        self.entropy_outputs = []  # the corresponding outputs for LLM generated test inputs in entropy measure.
        self.failed_input_output_examples = []  # failed input output examples in semantic measure. (input, output, expected)
        self.test_consistency = 0  # test consistency for semantic measure.
        self.probability = 0  # probability of the cluster.

    def add_program_str(self, program_str):
        self.programs_str.append(program_str)

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
