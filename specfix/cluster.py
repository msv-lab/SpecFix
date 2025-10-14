import ast
import math
from utils import get_exception_list, compare, safe_eval


class Clusters:
    def __init__(self):
        self.cluster_list = []  # list of clusters.
        self.entropy = 0  # entropy of the clusters.
        self.llm_generated_inputs = []  # LLM generated test inputs for entropy measure.
        self.input_output_examples = []  # input output examples for semantic measure
        self.at_least_one_align = None  # whether at least one cluster is aligned with the examples.
        self.weighted_test_consistency = 0  # weighted test consistency for semantic measure.
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
            if cluster.test_consistency == 1 or cluster.test_consistency == -1:
                cluster_1.append(cluster)
            else:
                other_clusters.append(cluster)
        if not cluster_1:  # no cluster with test consistency 1
            largest_cluster = max(other_clusters, key=lambda x: x.probability)
            return 0, largest_cluster
        return 1, max(cluster_1, key=lambda x: x.probability)


    def get_other_clusters_and_diff_outputs(self, cluster, cluster_limit=5):
        filtered_clusters = [
            c for c in self.cluster_list
            if c.test_consistency == 1 and c != cluster
        ]

        exception_list = get_exception_list()
        filtered_clusters = [
            c for c in filtered_clusters
            if not all(output in exception_list for output in c.entropy_outputs)
        ]

        final_clusters = []
        diff_outputs = []

        for candidate in filtered_clusters:
            for i, candidate_output in enumerate(candidate.entropy_outputs):
                if "Error" not in candidate_output:
                    if not compare(candidate_output, cluster.entropy_outputs[i]):
                        final_clusters.append(candidate)
                        diff_outputs.append([
                            self.llm_generated_inputs[i],
                            candidate_output,
                            cluster.entropy_outputs[i]
                        ])
                        if len(final_clusters) == cluster_limit:
                            return final_clusters, diff_outputs
                        break
        return final_clusters, diff_outputs

    def serialize(self):
        return {
            'requirement': self.requirement,
            'entry_point': self.entry_point,
            'cluster_list': [cluster.serialize() for cluster in self.cluster_list],
            'entropy': self.entropy,
            'llm_generated_inputs': str(self.llm_generated_inputs),
            'input_output_examples': str(self.input_output_examples),
            'weighted_test_consistency': self.weighted_test_consistency,
            'at_least_one_align': self.at_least_one_align,
        }

    def deserialize(self, data):
        self.cluster_list = [Cluster().deserialize(cluster) for cluster in data['cluster_list']]
        self.entropy = data['entropy']
        self.llm_generated_inputs = ast.literal_eval(data['llm_generated_inputs'])
        self.input_output_examples = ast.literal_eval(data['input_output_examples'])
        self.at_least_one_align = data['at_least_one_align']
        self.weighted_test_consistency = data["weighted_test_consistency"]
        self.requirement = data['requirement']
        self.entry_point = data['entry_point']
        return self

    def calculate_test_consistency(self):
        self.weighted_test_consistency = sum(
            [cluster.test_consistency * cluster.probability for cluster in self.cluster_list])


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

    def get_min_length_program(self):
        return min(self.programs_str, key=len)

    def deserialize(self, data):
        self.programs_str = data['programs_str']
        try:
            self.entropy_outputs = ast.literal_eval(data["outputs"])
        except Exception as e:
            self.entropy_outputs = safe_eval(data["outputs"])
        self.probability = data['probability']
        self.is_align_req = data['is_align_req']
        self.test_consistency = data['test_consistency']
        try:
            self.failed_input_output_examples = ast.literal_eval(data['failed_input_output_examples'])
        except Exception as e:
            self.failed_input_output_examples = safe_eval(data['failed_input_output_examples'])
        return self
