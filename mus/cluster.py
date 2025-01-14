import math


class Clusters:
    def __init__(self):
        self.clusters = []
        self.entropy = 0

    def add_cluster(self, cluster):
        self.clusters.append(cluster)

    def get_clusters(self):
        return self.clusters

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
            'entropy': self.entropy
        }


class Cluster:
    def __init__(self, outputs):
        self.programs_str = []
        self.requirement = []
        self.outputs = outputs
        self.distribution = 0
        self.DRS = None

    def add_program_str(self, program_str):
        self.programs_str.append(program_str)


    def set_requirement(self, requirement):
        self.requirement = requirement

    def set_DRS(self, DRS):
        self.DRS = DRS

    def set_probability(self, probability):
        self.distribution = probability

    def serialize(self):
        return {
            'programs_str': self.programs_str,
            'requirement': self.requirement,
            'outputs': self.outputs,
            'distribution': self.distribution,
            'DRS': self.DRS
        }