import math
import sys

sys.set_int_max_str_digits(0)


class Clusters:
    def __init__(self):
        self.clusters = []
        self.entropy = 0
        self.max_cluster_accuracy = 0
        self.test_inputs = []
        self.canonical_outputs = []
        self.canonical_solution = None
        self.at_least_one_align = False

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

    def set_at_least_one_align(self):
        self.at_least_one_align = True

    def calculate_distribution(self):
        total = sum([len(cluster.programs_str) for cluster in self.clusters])
        for cluster in self.clusters:
            cluster.distribution = len(cluster.programs_str) / total

    def calculate_entropy(self):
        total = sum([cluster.distribution for cluster in self.clusters])
        self.entropy = sum(
            [-cluster.distribution / total * math.log(cluster.distribution / total) for cluster in self.clusters])

    def calculate_max_cluster_accuracy(self):
        self.max_cluster_accuracy = max(cluster.accuracy for cluster in self.clusters)

    def serialize(self):
        return {
            'clusters': [cluster.serialize() for cluster in self.clusters],
            'entropy': self.entropy,
            'max_cluster_accuracy': self.max_cluster_accuracy,
            'test_inputs': self.test_inputs if any(isinstance(i, set) for i in self.test_inputs) else str(
                self.test_inputs),
            'canonical_outputs': self.canonical_outputs if any(
                isinstance(i, set) for i in self.canonical_outputs) else str(
                self.canonical_outputs),
            'canonical_solution': self.canonical_solution,
            'at_least_one_align': self.at_least_one_align
        }


class Cluster:
    def __init__(self, outputs):
        self.programs_str = []
        self.requirement = []
        self.is_align_req = False
        self.outputs = outputs
        self.failed_tests = []
        self.test_consistency = 0
        self.distribution = 0
        self.accuracy = 0
        self.DRS = None

    def add_program_str(self, program_str):
        self.programs_str.append(program_str)

    def set_requirement(self, requirement):
        self.requirement = requirement

    def set_DRS(self, DRS):
        self.DRS = DRS

    def set_distribution(self, distribution):
        self.distribution = distribution
        
    def set_accuracy(self, accuracy):
        self.accuracy = accuracy

    def align(self):
        self.is_align_req = True

    def set_failed_tests(self, failed_tests):
        self.failed_tests = failed_tests

    def set_test_consistency(self, test_consistency):
        self.test_consistency = test_consistency

    def serialize(self):
        return {
            'programs_str': self.programs_str,
            'requirement': self.requirement,
            'outputs': str(self.outputs),
            'distribution': self.distribution,
            'accuracy': self.accuracy,
            'is_align_req': self.is_align_req,
            'DRS': self.DRS
        }
