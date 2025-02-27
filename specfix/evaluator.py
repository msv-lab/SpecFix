import ast
import concurrent.futures

from specfix.prompting import *
from specfix.model import Model
from specfix.utils import unwrap, get_parameter_number, execute_inputs, compare


class SpecFixAccuracyEvaluator:
    def __init__(self, differential_tester=None, ground_truth_tester=None, model="qwen2.5-coder-7b-instruct",
                 temperature=1.0):
        self.differential_tester = differential_tester
        self.ground_truth_tester = ground_truth_tester
        self.model = Model(model, temperature)
        self.temperature = temperature

    def get_clusters(self, programs, test_inputs, entry_point, examples):
        clusters = self.differential_tester(programs, test_inputs, entry_point)
        clusters.set_input_output_examples(examples)
        return clusters

    def calculate_ambiguity(self, clusters, entry_point):
        self.ground_truth_tester(clusters, entry_point)
        clusters.calculate_ambiguity()

    def parallel_generate_programs(self, requirement, n_programs):
        generated_programs = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(self.generate_programs, requirement)
                       for _ in range(n_programs)]
            for future in concurrent.futures.as_completed(futures):
                prog = future.result()
                generated_programs.append(prog)
        return generated_programs

    def generate_programs(self, requirements):
        print("GENERATE PROGRAMS")
        response = self.model.get_response(instruction_generate_code,
                                           prompt_generate_code(requirements))
        code = unwrap(response, "code")
        if code == "":
            return self.generate_programs(requirements)
        return code

    def generate_tests(self, requirements, entry_point):
        print("GENERATE TESTS INPUTS")
        tests = []
        para_number = get_parameter_number(requirements, entry_point)
        response = self.model.get_response(instruction_generate_test,
                                           prompt_generate_test(requirements, entry_point, para_number))
        try:
            response = unwrap(response, "tests")
            for line in response.splitlines():
                test = ast.literal_eval("[" + unwrap(line, "test") + "]")
                if len(test) == para_number:
                    tests.append(test)
                if len(tests) > 50:
                    break
            if len(tests) == 0:
                raise Exception
        except Exception as e:
            tests = self.generate_tests(requirements, entry_point)
        return tests

    def generate_requirement(self, program):
        print("REQUIREMENTS GENERATION")
        response = self.model.get_response(instruction_generate_requirement,
                                           prompt_generate_requirement(program))
        return unwrap(response, "requirement")

    def repair_requirements(self, requirements, answer):
        print("REPAIR REQUIREMENTS")
        response = self.model.get_response(instruction_repair_requirement,
                                           prompt_repair_requirement(requirements, answer))
        return unwrap(response, "requirement")

    def vanilla_repair_requirements(self, requirements):
        print("VANILLA REPAIR REQUIREMENTS")
        response = self.model.get_response(instruction_vanilla_repair,
                                           prompt_vanilla_repair(requirements))
        return unwrap(response, "requirement")

    def inverse_requirement(self, code):
        print("INVERSE REQUIREMENT")
        response = self.model.get_response(instruction_inverse_requirement,
                                           prompt_inverse_requirement(code))
        return unwrap(response, "requirement")

    def test_based_repair(self, program, requirement, failed_input_output_examples):

        print("TEST BASED REPAIR")
        response = self.model.get_response(instruction_test_based_repair,
                                           prompt_test_based_repair(requirement, program, failed_input_output_examples))
        return unwrap(response, "code")

    def classification(self, requirements):
        print("CLASSIFICATION")
        response = self.model.get_response(instruction_classification,
                                           prompt_classification(requirements))
        answer = unwrap(response, "answer")
        reason = unwrap(response, "reasoning")
        return answer, reason

    def repair_largest_cluster_requirement(self, requirement, programs, specified_programs):
        print("REPAIR LARGEST CLUSTER REQUIREMENT")
        response = self.model.get_response(instruction_repair_largest_cluster_requirement,
                                           prompt_repair_largest_cluster_requirement(requirement, programs,
                                                                                     specified_programs))
        return unwrap(response, "requirement")

    def pass_k(self, requirement, inputs, outputs, entry_point, k):
        for _ in range(k):
            program = self.generate_programs(requirement)
            result_list = execute_inputs(program, inputs, entry_point)
            if compare(result_list, outputs):
                return True
        return False

    def pass_k_repair(self, original_requirement, repaired_requirement, inputs, outputs, entry_point, k):
        original_results = []
        repaired_results = []
        for _ in range(k):
            original_program = self.generate_programs(original_requirement)
            result = execute_inputs(original_program, inputs, entry_point)
            if compare(result, outputs):
                original_results.append(True)
            else:
                original_results.append(False)
            if repaired_requirement is not None:
                repaired_program = self.generate_programs(repaired_requirement)
                result = execute_inputs(repaired_program, inputs, entry_point)
                if compare(result, outputs):
                    repaired_results.append(True)
                else:
                    repaired_results.append(False)
        return any(original_results), any(repaired_results) if repaired_requirement is not None else any(
            original_results)
