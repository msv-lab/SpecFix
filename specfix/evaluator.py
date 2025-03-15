import ast
import concurrent.futures
import math
from time import sleep
from copy import deepcopy

from specfix.prompting import *
from specfix.model import Model
from specfix.utils import unwrap, get_parameter_number, execute_inputs, compare, get_entry_point, \
    get_failed_input_output, calculate_pass_k, calculate_test_consistency, unify_model_name


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
        clusters.set_input_output_examples(examples)
        clusters.set_entry_point(entry_point)
        return clusters

    def get_clusters_crosshair(self, programs, entry_point, examples):
        print("GET CLUSTERS CROSSHAIR")
        clusters = self.differential_tester(programs, entry_point)
        clusters.set_input_output_examples(examples)
        return clusters

    def calculate_ambiguity(self, clusters):
        print("CALCULATE AMBIGUITY")
        self.ground_truth_tester(clusters)
        clusters.calculate_ambiguity()

    def parallel_generate_programs(self, requirement, entry_point, n_programs, max_workers=10):
        generated_programs = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.generate_program, requirement, entry_point)
                       for _ in range(n_programs)]
            for future in concurrent.futures.as_completed(futures):
                prog = future.result()
                generated_programs.append(prog)
        return generated_programs

    def generate_programs(self, requirement, entry_point, n_programs):
        if "deepseek" in self.model.model_name:
            generated_programs = []
            for _ in range(math.ceil(n_programs / 5)):
                response = self.model.get_response_sample(instruction_generate_code,
                                                          prompt_generate_code(requirement, entry_point), 5)
                generated_programs.extend([unwrap(prog, "code") for prog in response if unwrap(prog, "code") != ""])
            if len(generated_programs) < n_programs:
                for _ in range(n_programs - len(generated_programs)):
                    generated_programs.append(self.generate_program(requirement, entry_point))
            elif len(generated_programs) > n_programs:
                generated_programs = generated_programs[: n_programs]
            return generated_programs
        elif "gpt" in self.model.model_name:
            response = self.model.get_response_sample(instruction_generate_code,
                                                      prompt_generate_code(requirement, entry_point), n_programs)
            generated_programs = [unwrap(prog, "code") for prog in response if unwrap(prog, "code") != ""]
            if len(generated_programs) < n_programs:
                for _ in range(n_programs - len(generated_programs)):
                    generated_programs.append(self.generate_program(requirement, entry_point))
            return generated_programs
        else:
            return self.parallel_generate_programs(requirement, entry_point, n_programs)

    def generate_program(self, requirement, entry_point):
        for i in range(5):
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

    def repair_requirement(self, requirement, entry_point, program):
        for i in range(10):
            print("TEST BASED REPAIR REQUIREMENT", i)
            response = self.model.get_response(instruction_repair_requirement,
                                               prompt_repair_requirement(requirement, entry_point, program), True)
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

    def repair_largest_cluster_requirement(self, requirement, entry_point, specified_programs, programs, diff_outputs,
                                           input_output_examples):
        for i in range(10):
            print("REPAIR LARGEST CLUSTER REQUIREMENT", i)
            ambiguity, analysis = self.repair_largest_cluster_requirement_localization(requirement, entry_point,
                                                                                       specified_programs, programs,
                                                                                       diff_outputs)
            response = self.model.get_response(instruction_requirement_repair,
                                               prompt_requirement_repair(requirement, entry_point,
                                                                         ambiguity, analysis, input_output_examples
                                                                         ), True)
            repaired_requirement = unwrap(response, "requirement")
            if repaired_requirement != "":
                return repaired_requirement

    def repair_largest_cluster_requirement_localization(self, requirement, entry_point, specified_programs, programs,
                                                        diff_outputs):
        for i in range(10):
            print("REPAIR LARGEST CLUSTER REQUIREMENT WITH LOCALIZATION", i)
            ambiguity_response = self.model.get_response(instruction_ambiguity_localization_largest_cluster,
                                                         prompt_repair_largest_cluster_localization(requirement,
                                                                                                    entry_point,
                                                                                                    programs,
                                                                                                    specified_programs,
                                                                                                    diff_outputs))
            ambiguity = unwrap(ambiguity_response, "ambiguity")
            analysis = unwrap(ambiguity_response, "analysis")
            return ambiguity, analysis

    def pass_k_sample(self, requirement, inputs, outputs, entry_point, k, sample):
        if entry_point == "combinations_colors":
            return calculate_pass_k(sample, sample, k), [], []
        if requirement is None:
            return None, [], []
        passes = 0
        programs = self.generate_programs(requirement, entry_point, k * sample)
        generated_programs = []
        failed_inputs_outputs = []
        actual_sample = sample
        for i in range(sample):
            passed = False
            for j in range(k):
                program = programs[i * k + j]
                if not program:
                    actual_sample -= 1
                    continue
                generated_programs.append(program)
                result = execute_inputs(program, inputs, entry_point)
                failed_input_output, _ = get_failed_input_output(result, inputs, outputs)
                failed_inputs_outputs.append(failed_input_output)
                if compare(result, outputs):
                    passed = True
                    break
            passes += int(passed)

        return calculate_pass_k(actual_sample, passes, k), generated_programs, failed_inputs_outputs

    def remove_example(self, problem, repaired_requirement):
        problem_woe = deepcopy(problem)
        response = self.model.get_response(instruction_remove_example, prompt_remove_example(repaired_requirement))
        problem_woe["requirement"] = unwrap(response, "requirement")
        return problem

    def specfix_detect(self, problem, n_programs):
        requirement, entry_point, examples, task_id = problem['requirement'], problem['entry_point'], problem[
            'input_output_examples'], problem['task_id']
        print(F"SPECFIX DETECT {task_id}")
        test_inputs = ast.literal_eval(problem["llm_generated_inputs"][unify_model_name(self.model.model_name)])
        programs = self.generate_programs(requirement, entry_point, n_programs)
        clusters = self.get_clusters(requirement, programs, test_inputs, entry_point, examples)
        self.calculate_ambiguity(clusters)
        if clusters.entropy > 0 or clusters.weighted_test_consistency != 1:
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
            largest_cluster = clusters.get_largest_cluster()
            if largest_cluster.test_consistency != 1:
                #         while True:
                #             repaired_program = self.hoare_logic_repair(
                #                 requirement, entry_point,
                #                 largest_cluster.programs_str[0],
                #                 largest_cluster.failed_input_output_examples
                #             )
                #             failed_input_output_examples, test_consistency = calculate_test_consistency(repaired_program,
                #                                                                                         entry_point,
                #                                                                                         examples[0],
                #                                                                                         examples[1])
                #             if test_consistency == 1:
                #                 break
                repaired_requirement = self.execution_repair(requirement, entry_point, largest_cluster.programs_str[0],
                                                             largest_cluster.failed_input_output_examples,
                                                             repaired_requirement)
            else:
                other_clusters, diff_outputs = clusters.get_other_clusters_and_diff_outputs(
                    clusters.llm_generated_inputs,
                    largest_cluster)
                if not other_clusters:
                    repaired_requirement = self.repair_requirement(requirement, entry_point,
                                                                   largest_cluster.programs_str[0])
                else:
                    other_programs = [cluster.programs_str[0] for cluster in other_clusters]
                    repaired_requirement = self.repair_largest_cluster_requirement(
                        requirement, entry_point, largest_cluster.programs_str[0], other_programs, diff_outputs,
                        examples
                    )

            repaired_programs = self.generate_programs(repaired_requirement, entry_point, n_programs)
            repaired_clusters = self.get_clusters(repaired_requirement, repaired_programs, test_inputs, entry_point,
                                                  str(examples))
            self.calculate_ambiguity(repaired_clusters)
            if (
                    repaired_clusters.entropy == 0 and repaired_clusters.weighted_test_consistency == 1) or repair_attempts >= 3:
                break
            requirement = repaired_requirement
            clusters = repaired_clusters
        return repaired_requirement, repaired_clusters

    def test_based_repair_requirement(self, requirement, entry_point, failed_input_output_examples):
        for i in range(10):
            print("REPAIR REQUIREMENT TEST", i)
            response = self.model.get_response(instruction_repair_requirement_test_based,
                                               prompt_test_based_repair_requirement(requirement, entry_point,
                                                                                    failed_input_output_examples))
            repaired_requirement = unwrap(response, "requirement")
            return repaired_requirement

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
