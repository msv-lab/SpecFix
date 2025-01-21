import math
import sys

sys.set_int_max_str_digits(0)


class Clusters:
    def __init__(self):
        self.clusters = []
        self.entropy = 0
        self.test_inputs = []
        self.canonical_outputs = []
        self.canonical_solution = None

    def add_cluster(self, cluster):
        self.clusters.append(cluster)

    def get_clusters(self):
        return self.clusters

    def set_test_inputs(self, test_inputs):
        self.test_inputs = test_inputs

    def set_canonical_outputs(self, canonical_outputs):
        self.canonical_outputs = canonical_outputs

    def set_canonical_solution(self, canonical_solution):
        self.canonical_solution = canonical_solution

    def calculate_distribution(self):
        total = sum([len(cluster.programs_str) for cluster in self.clusters])
        for cluster in self.clusters:
            cluster.distribution = len(cluster.programs_str) / total

    def calculate_entropy(self):
        total = sum([cluster.distribution for cluster in self.clusters])
        self.entropy = sum(
            [-cluster.distribution / total * math.log(cluster.distribution / total) for cluster in self.clusters])

    def serialize(self):
        return {
            'clusters': [cluster.serialize() for cluster in self.clusters],
            'entropy': self.entropy,
            'test_inputs': self.test_inputs if any(isinstance(i, set) for i in self.test_inputs) else str(
                self.test_inputs),
            'canonical_outputs': self.canonical_outputs if any(
                isinstance(i, set) for i in self.canonical_outputs) else str(
                self.canonical_outputs)
        }


class Cluster:
    def __init__(self, outputs):
        self.programs_str = []
        self.requirement = []
        self.is_align_req = None
        self.outputs = outputs
        self.distribution = 0
        self.DRS = None

    def add_program_str(self, program_str):
        self.programs_str.append(program_str)

    def set_requirement(self, requirement):
        self.requirement = requirement

    def set_DRS(self, DRS):
        self.DRS = DRS

    def set_distribution(self, distribution):
        self.distribution = distribution

    def align(self):
        self.is_align_req = True

    def not_align(self):
        self.is_align_req = False

    def get_alignment(self):
        return self.is_align_req

    def serialize(self):
        return {
            'programs_str': self.programs_str,
            'requirement': self.requirement,
            'outputs': str(self.outputs),
            'distribution': self.distribution,
            'is_align_req': self.is_align_req,
            'DRS': self.DRS
        }
