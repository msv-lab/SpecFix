class Cluster:
    def __init__(self, outputs):
        self.programs_str = []
        self.requirement = []
        self.probe = []
        self.outputs = outputs
        self.distribution = 0
        self.DRS = None

    def add_program_str(self, program_str):
        self.programs_str.append(program_str)

    def set_probe(self, probe):
        self.probe = probe

    def set_requirement(self, requirement):
        self.requirement = requirement

    def set_DRS(self, DRS):
        self.DRS = DRS

    def set_distribution(self, distribution):
        self.distribution = distribution