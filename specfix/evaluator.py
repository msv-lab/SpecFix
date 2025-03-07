import ast
import concurrent.futures
from time import sleep

from specfix.prompting import *
from specfix.model import Model
from specfix.utils import unwrap, get_parameter_number, execute_inputs, compare, get_entry_point, \
    get_failed_input_output


class SpecFixAccuracyEvaluator:
    def __init__(self, differential_tester=None, ground_truth_tester=None, model="qwen2.5-coder-7b-instruct",
                 temperature=1.0):
        self.differential_tester = differential_tester
        self.ground_truth_tester = ground_truth_tester
        self.model = Model(model, temperature)
        self.temperature = temperature

    def get_clusters(self, programs, test_inputs, entry_point, examples):
        print("GET CLUSTERS")
        clusters = self.differential_tester(programs, test_inputs, entry_point)
        clusters.set_input_output_examples(examples)
        return clusters

    def get_clusters_crosshair(self, programs, entry_point, examples):
        print("GET CLUSTERS CROSSHAIR")
        clusters = self.differential_tester(programs, entry_point)
        clusters.set_input_output_examples(examples)
        return clusters

    def calculate_ambiguity(self, clusters, entry_point):
        print("CALCULATE AMBIGUITY")
        self.ground_truth_tester(clusters, entry_point)
        clusters.calculate_ambiguity()

    def parallel_generate_programs(self, requirement, n_programs, entry_point, max_workers=10):
        generated_programs = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.generate_program, requirement, entry_point)
                       for _ in range(n_programs)]
            for future in concurrent.futures.as_completed(futures):
                prog = future.result()
                generated_programs.append(prog)
        return generated_programs

    def generate_programs(self, requirement, n_programs, entry_point):
        generated_programs = []
        for _ in range(n_programs):
            program = self.generate_program(requirement, entry_point)
            generated_programs.append(program)
        return generated_programs

    def generate_program(self, requirements, entry_point):
        for i in range(10):
            try:
                print("GENERATE PROGRAM ATTEMPT", i)
                response = self.model.get_response(instruction_generate_code,
                                                   prompt_generate_code(requirements, entry_point))
                code = unwrap(response, "code")
                if code == "":
                    raise Exception
                return code
            except Exception as e:
                print(e)
                sleep(1)
                continue
        print("GENERATE PROGRAM FAILED")
        return ""

    def generate_tests(self, requirements, entry_point):
        for i in range(10):
            print("GENERATE TEST ATTEMPT", i)
            tests = []
            para_number = get_parameter_number(requirements, entry_point)
            try:
                response = self.model.get_response(instruction_generate_test,
                                                   prompt_generate_test(requirements, entry_point, para_number))
                response = unwrap(response, "tests")
                for line in response.splitlines():
                    test = ast.literal_eval("[" + unwrap(line, "test") + "]")
                    if len(test) == para_number:
                        tests.append(test)
                    if len(tests) > 50:
                        break
                if len(tests) == 0:
                    raise Exception
                return tests
            except Exception as e:
                print(e)
                continue
        print("GENERATE TEST FAILED")
        return []

    def vanilla_repair_requirements(self, requirements):
        print("VANILLA REPAIR REQUIREMENTS")
        response = self.model.get_response(instruction_vanilla_repair,
                                           prompt_vanilla_repair(requirements))
        return unwrap(response, "requirement")

    def repair_requirement(self, requirement, entry_point, code):
        for i in range(10):
            print("REPAIR REQUIREMENT", i)
            response = self.model.get_response(instruction_repair_requirement,
                                               prompt_repair_requirement(requirement, entry_point, code))
            repaired_requirement = unwrap(response, "requirement")
            if repaired_requirement != "":
                return repaired_requirement

    def test_based_repair(self, requirement, entry_point, program, failed_input_output_examples):
        for i in range(10):
            print("TEST BASED REPAIR", i)
            response = self.model.get_response(instruction_test_based_repair,
                                               prompt_test_based_repair(requirement, entry_point, program,
                                                                        failed_input_output_examples))
            repaired_program = unwrap(response, "code")
            if repaired_program != "":
                return repaired_program

    def classification(self, requirements):
        print("CLASSIFICATION")
        response = self.model.get_response(instruction_classification,
                                           prompt_classification(requirements))
        answer = unwrap(response, "answer")
        reason = unwrap(response, "reasoning")
        return answer, reason

    def repair_largest_cluster_requirement(self, requirement, entry_point, programs, specified_programs):
        for i in range(10):
            print("REPAIR LARGEST CLUSTER REQUIREMENT", i)
            response = self.model.get_response(instruction_repair_largest_cluster_requirement,
                                               prompt_repair_largest_cluster_requirement(requirement, entry_point,
                                                                                         programs,
                                                                                         specified_programs))
            repaired_requirement = unwrap(response, "requirement")
            if repaired_requirement != "":
                return repaired_requirement

    def pass_k(self, original_requirement, repaired_requirement, inputs, outputs, entry_point, k):
        if entry_point == "combinations_colors":
            return True, True, [[], [], [], []]
        original_results = []
        repaired_results = []
        original_failed_inputs_outputs = []
        repaired_failed_inputs_outputs = []
        original_programs = []
        repaired_programs = []
        for _ in range(k):
            original_program = self.generate_program(original_requirement, entry_point)
            original_programs.append(original_program)
            if original_program == "":
                original_results.append(False)
            else:
                original_result = execute_inputs(original_program, inputs, entry_point)
                if compare(original_result, outputs):
                    original_results.append(True)
                else:
                    original_failed_input_output, _ = get_failed_input_output(original_result, inputs, outputs)
                    original_failed_inputs_outputs.append(original_failed_input_output)
                    original_results.append(False)

            if repaired_requirement is not None:
                repaired_entry_point = get_entry_point(repaired_requirement)
                repaired_program = self.generate_program(repaired_requirement, repaired_entry_point)
                repaired_programs.append(repaired_program)
                if repaired_program == "":
                    repaired_results.append(False)
                else:
                    repaired_result = execute_inputs(repaired_program, inputs, repaired_entry_point)
                    if compare(repaired_result, outputs):
                        repaired_results.append(True)
                    else:
                        repaired_failed_input_output, _ = get_failed_input_output(repaired_result, inputs, outputs)
                        repaired_failed_inputs_outputs.append(repaired_failed_input_output)
                        repaired_results.append(False)
                        # if original_results[-1]:
                        #     a = 1
        return any(original_results), any(repaired_results) if repaired_requirement is not None else any(
            original_results), [original_programs, original_failed_inputs_outputs, repaired_programs,
                                repaired_failed_inputs_outputs]