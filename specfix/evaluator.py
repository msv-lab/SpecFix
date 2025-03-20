import ast
import concurrent.futures
import math
from time import sleep
from copy import deepcopy

from specfix.prompting import *
from specfix.model import Model
from specfix.utils import unwrap, get_parameter_number, execute_inputs, compare, get_failed_input_output, \
    calculate_pass_k, unify_model_name


class SpecFixAccuracyEvaluator:
    def __init__(self, differential_tester=None, ground_truth_tester=None, model="qwen2.5-coder-7b-instruct",
                 temperature=1.0):
        self.differential_tester = differential_tester
        self.ground_truth_tester = ground_truth_tester
        self.model = Model(model, temperature)
        self.temperature = temperature

    def get_clusters(self, requirement, programs, test_inputs, entry_point, examples=None):
        print("GET CLUSTERS")
        clusters = self.differential_tester(programs, test_inputs, entry_point)
        clusters.set_requirement(requirement)
        clusters.set_entry_point(entry_point)
        clusters.set_input_output_examples(examples)
        return clusters

    def get_clusters_crosshair(self, programs, entry_point, examples):
        print("GET CLUSTERS CROSSHAIR")
        clusters = self.differential_tester(programs, entry_point)
        clusters.set_input_output_examples(examples)
        return clusters

    def get_test_consistency(self, clusters):
        print("CALCULATE TEST CONSISTENCY")
        self.ground_truth_tester(clusters)
        clusters.calculate_test_consistency()

    def parallel_generate_programs(self, requirement, entry_point, n_programs, max_workers=10):
        generated_programs = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.generate_program, requirement, entry_point)
                       for _ in range(n_programs)]
            for future in concurrent.futures.as_completed(futures):
                prog = future.result()
                generated_programs.append(prog)
        generated_programs = [prog for prog in generated_programs if prog != ""]
        return generated_programs

    def generate_programs(self, requirement, entry_point, n_programs):
        if "deepseek" in self.model.model_name:
            batch_size = 5
            generated_programs = []
            for _ in range(math.ceil(n_programs / batch_size)):
                response = self.model.get_response_sample(instruction_generate_code,
                                                          prompt_generate_code(requirement, entry_point), batch_size)
                generated_programs.extend([unwrap(prog, "code") for prog in response])
            if len(generated_programs) > n_programs:
                generated_programs = generated_programs[: n_programs]
            generated_programs = [prog for prog in generated_programs if prog != ""]
            return generated_programs
        elif "gpt" in self.model.model_name:
            response = self.model.get_response_sample(instruction_generate_code,
                                                      prompt_generate_code(requirement, entry_point), n_programs)
            generated_programs = [unwrap(prog, "code") for prog in response]
            generated_programs = [prog for prog in generated_programs if prog != ""]
            return generated_programs
        else:
            return self.parallel_generate_programs(requirement, entry_point, n_programs)

    def generate_program(self, requirement, entry_point):
        for i in range(2):
            try:
                print("GENERATE PROGRAM ATTEMPT", i)
                response = self.model.get_response(instruction_generate_code,
                                                   prompt_generate_code(requirement, entry_point))
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

    def reverse_repair(self, requirement, entry_point, program):
        for i in range(10):
            print("REVERSE REPAIR REQUIREMENT", i)
            response = self.model.get_response(instruction_reverse_requirement,
                                               prompt_reverse_requirement(requirement, entry_point, program), True)
            repaired_requirement = unwrap(response, "requirement")
            if repaired_requirement != "":
                return repaired_requirement

    def program_repair(self, requirement, entry_point, program, failed_input_output_examples):
        for i in range(10):
            print("REPAIR PROGRAM", i)
            response = self.model.get_response(instruction_program_repair,
                                               prompt_program_repair(requirement, entry_point, program,
                                                                     failed_input_output_examples), True)
            repaired_program = unwrap(response, "program")
            if repaired_program != "":
                return repaired_program

    def classification(self, requirements):
        for i in range(10):
            print("CLASSIFICATION", i)
            response = self.model.get_response(instruction_classification,
                                               prompt_classification(requirements))
            answer = unwrap(response, "answer")
            reason = unwrap(response, "reasoning")
            if answer == "Yes" or answer == "No":
                return answer, reason

    def largest_cluster_repair(self, requirement, entry_point, specified_programs, programs, diff_outputs,
                               input_output_examples):
        for i in range(10):
            print("REPAIR LARGEST CLUSTER REQUIREMENT", i)
            ambiguity, analysis = self.largest_cluster_localization(requirement, entry_point,
                                                                    specified_programs, programs,
                                                                    diff_outputs)
            response = self.model.get_response(instruction_largest_cluster_repair,
                                               prompt_largest_cluster_repair(requirement, entry_point,
                                                                             ambiguity, analysis, input_output_examples
                                                                             ), True)
            repaired_requirement = unwrap(response, "requirement")
            if repaired_requirement != "":
                return repaired_requirement

    def largest_cluster_localization(self, requirement, entry_point, specified_programs, programs,
                                     diff_outputs):
        for i in range(10):
            print("REPAIR LARGEST CLUSTER REQUIREMENT WITH LOCALIZATION", i)
            ambiguity_response = self.model.get_response(instruction_largest_cluster_localization,
                                                         prompt_largest_cluster_localization(requirement,
                                                                                             entry_point,
                                                                                             programs,
                                                                                             specified_programs,
                                                                                             diff_outputs))
            ambiguity = unwrap(ambiguity_response, "ambiguity")
            analysis = unwrap(ambiguity_response, "analysis")
            return ambiguity, analysis

    def pass_k_and_pass_rate(self, requirement, inputs, outputs, entry_point, k, sample):
        if entry_point == "combinations_colors":
            return calculate_pass_k(sample, sample, k), 1, [], []
        if requirement is None:
            return None, None, [], []
        passes = 0
        programs = self.generate_programs(requirement, entry_point, sample)
        if len(programs) == 0:
            return None, [], []
        generated_programs = []
        failed_inputs_outputs = []
        pass_rates = []
        for i in range(len(programs)):
            passed = False
            program = programs[i]
            generated_programs.append(program)
            result = execute_inputs(program, inputs, entry_point)
            if compare(result, outputs):
                passed = True
                failed_inputs_outputs.append([])
                pass_rates.append(1)
            else:
                failed_input_output, pass_rate = get_failed_input_output(result, inputs, outputs)
                if len(failed_input_output) < 300:
                    failed_inputs_outputs.append(failed_input_output)
                pass_rates.append(pass_rate)
            passes += int(passed)

        return calculate_pass_k(len(programs), passes, k), sum(pass_rates) / len(
            pass_rates), generated_programs, failed_inputs_outputs

    def remove_example(self, problem, repaired_requirement):
        problem_woe = deepcopy(problem)
        response = self.model.get_response(instruction_remove_example, prompt_remove_example(repaired_requirement))
        problem_woe["requirement"] = unwrap(response, "requirement")
        return problem_woe

    def specfix_detect(self, problem, n_programs):
        requirement, entry_point, examples, task_id = problem['requirement'], problem['entry_point'], problem[
            'input_output_examples'], problem['task_id']
        print(F"SPECFIX DETECT {task_id}")
        test_inputs = ast.literal_eval(problem["llm_generated_inputs"][unify_model_name(self.model.model_name)])
        programs = self.generate_programs(requirement, entry_point, n_programs)
        if len(programs) == 0:
            return False, None
        clusters = self.get_clusters(requirement, programs, test_inputs, entry_point, examples)
        self.get_test_consistency(clusters)
        if clusters.entropy > 0 or 0 <= clusters.weighted_test_consistency < 1:
            return True, clusters
        return False, clusters

    def specfix_repair(self, clusters, n_programs):
        repair_attempts = 0
        requirement = clusters.requirement
        examples = clusters.input_output_examples
        entry_point = clusters.entry_point
        test_inputs = clusters.llm_generated_inputs
        repaired_requirement = None
        while True:
            repair_attempts += 1
            repair_method, largest_cluster = clusters.select_repair_method()
            match repair_method:
                case 0:  # if 0 cluster passed example
                    repaired_program = self.test_based_repair_program(requirement, entry_point,
                                                                      largest_cluster.programs_str[0],
                                                                      largest_cluster.failed_input_output_examples)
                    repaired_requirement = self.largest_cluster_repair(requirement, entry_point, repaired_program,
                                                                       [largest_cluster.programs_str[0]],
                                                                       largest_cluster.failed_input_output_examples,
                                                                       examples)
                case 1:  # if 1 cluster passed example
                    repaired_requirement = self.reverse_repair(requirement, entry_point,
                                                               largest_cluster.programs_str[0])
                case 2:  # if more than 1 cluster passed example and the largest cluster is significantly larger than other clusters
                    other_clusters, diff_outputs = clusters.get_other_clusters_and_diff_outputs(
                        largest_cluster)
                    other_programs = [cluster.get_min_length_program() for cluster in other_clusters]
                    repaired_requirement = self.largest_cluster_repair(
                        requirement, entry_point, largest_cluster.programs_str[0], other_programs, diff_outputs,
                        examples
                    )
                case 3:  # if more than 1 cluster passed example and the largest cluster is not significantly larger than other clusters
                    other_clusters = largest_cluster
                    programs = [cluster.get_min_length_program() for cluster in other_clusters]
                    repaired_requirement = self.cluster_repair(requirement, entry_point, programs, examples)

            repaired_programs = self.generate_programs(repaired_requirement, entry_point, n_programs)
            repaired_clusters = self.get_clusters(repaired_requirement, repaired_programs, test_inputs, entry_point,
                                                  str(examples))
            self.calculate_test_consistency(repaired_clusters)
            if (
                    repaired_clusters.entropy == 0 and repaired_clusters.weighted_test_consistency == 1) or repair_attempts >= 3:
                break
            requirement = repaired_requirement
            clusters = repaired_clusters
        return repaired_requirement, repaired_clusters

    def test_based_repair_program(self, requirement, entry_point, program, failed_input_output_examples):
        for i in range(10):
            print("TEST REPAIR PROGRAM", i)
            response = self.model.get_response(instruction_test_based_repair_program,
                                               prompt_test_based_repair_program(requirement, entry_point, program,
                                                                                failed_input_output_examples))
            repaired_program = unwrap(response, "code")
            return repaired_program

    def execution_repair(self, requirement, entry_point, program, failed_input_output_examples, incorrect_repair=None):
        for i in range(10):
            print("EXECUTION REPAIR", i)
            ambiguity, analysis = self.execution_location(requirement, entry_point, program,
                                                          failed_input_output_examples)
            response = self.model.get_response(instruction_execution_repair,
                                               prompt_execution_repair(requirement, entry_point, ambiguity, analysis,
                                                                       failed_input_output_examples, incorrect_repair))
            repaired_requirement = unwrap(response, "requirement")
            if repaired_requirement != "":
                return repaired_requirement
            else:
                return requirement

    def execution_location(self, requirement, entry_point, program, failed_input_output_examples):
        for i in range(10):
            print("EXECUTION LOCATION", i)
            ambiguity_response = self.model.get_response(instruction_execution_localization,
                                                         prompt_execution_localization(requirement, entry_point,
                                                                                       program,
                                                                                       failed_input_output_examples))
            ambiguity = unwrap(ambiguity_response, "ambiguity")
            analysis = unwrap(ambiguity_response, "analysis")
            return ambiguity, analysis

    def cluster_localization(self, requirement, entry_point, programs):
        for i in range(10):
            print("CLUSTER LOCALIZATION", i)
            response = self.model.get_response(instruction_cluster_localization,
                                               prompt_cluster_localization(requirement, entry_point, programs))
            ambiguity = unwrap(response, "ambiguity")
            analysis = unwrap(response, "analysis")
            return ambiguity, analysis

    def cluster_repair(self, requirement, entry_point, programs, input_output_examples):
        for i in range(10):
            print("REPAIR CLUSTER", i)
            ambiguity, analysis = self.cluster_localization(requirement, entry_point, programs)
            response = self.model.get_response(instruction_cluster_repair,
                                               prompt_cluster_repair(requirement, entry_point, ambiguity,
                                                                     analysis, input_output_examples))
            repaired_requirement = unwrap(response, "requirement")
            if repaired_requirement != "":
                return repaired_requirement

    def solved_with_majority_vote(self, clusters, inputs, outputs):
        cluster = max(clusters.cluster_list, key=lambda c: c.probability)
        program = cluster.programs_str[0]
        result = execute_inputs(program, inputs, clusters.entry_point)
        if compare(result, outputs):
            return True
        return False
