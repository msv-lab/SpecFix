import ast
import concurrent.futures
import math
from time import sleep

from specfix.prompting import *
from specfix.model import Model
from specfix.utils import unwrap, get_parameter_number, execute_inputs, compare, get_entry_point, \
    get_failed_input_output, calculate_pass_k


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
        if "deepseek" in self.model.model:
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
        else:
            response = self.model.get_response_sample(instruction_generate_code,
                                                      prompt_generate_code(requirement, entry_point), n_programs)
            generated_programs = [unwrap(prog, "code") for prog in response if unwrap(prog, "code") != ""]
            if len(generated_programs) < n_programs:
                for _ in range(n_programs - len(generated_programs)):
                    generated_programs.append(self.generate_program(requirement, entry_point))
            return generated_programs

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

    def repair_requirement(self, requirement, entry_point, program):
        for i in range(10):
            print("REPAIR REQUIREMENT", i)
            response = self.model.get_response(instruction_repair_requirement,
                                               prompt_repair_requirement(requirement, entry_point, program), True)
            repaired_requirement = unwrap(response, "requirement")
            if repaired_requirement != "":
                return repaired_requirement

    def repair_requirement_localization(self, requirement, entry_point, program):
        for i in range(10):
            print("REPAIR REQUIREMENT WITH LOCALIZATION", i)
            identified_response = self.model.get_response(instruction_ambiguity_localization,
                                                          prompt_ambiguity_localization(requirement, entry_point,
                                                                                        program))
            identified_sentences = unwrap(identified_response, "sentences")
            identified_sentences_list = []
            for sentence in identified_sentences.splitlines():
                if sentence != "":
                    sentence = unwrap(sentence, "sentence")
                    if sentence in requirement:
                        identified_sentences_list.append(sentence)
            if not identified_sentences_list:
                return self.repair_requirement(requirement, entry_point, program)
            revised_response = self.model.get_response(instruction_ambiguous_sentence_repair,
                                                       prompt_ambiguous_sentence_repair(requirement, entry_point,
                                                                                        identified_sentences_list,
                                                                                        program))
            revised_sentences = unwrap(revised_response, "revised_sentences")
            revised_sentences_list = [unwrap(sentence, "revised_sentence") for sentence in
                                      revised_sentences.splitlines()]
            for (identified_sentence, revised_sentence) in zip(identified_sentences_list, revised_sentences_list):
                revised_sentence = (revised_sentence[0].upper() if identified_sentence[0].isupper() else
                                    revised_sentence[0].lower()) + revised_sentence[1:]
                requirement = requirement.replace(identified_sentence, revised_sentence)
            return requirement

    def test_based_repair(self, requirement, entry_point, program, failed_input_output_examples):
        for i in range(10):
            print("TEST BASED REPAIR", i)
            response = self.model.get_response(instruction_test_based_repair,
                                               prompt_test_based_repair(requirement, entry_point, program,
                                                                        failed_input_output_examples), True)
            repaired_program = unwrap(response, "code")
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

    def repair_largest_cluster_requirement(self, requirement, entry_point, programs, specified_programs):
        for i in range(10):
            print("REPAIR LARGEST CLUSTER REQUIREMENT", i)
            response = self.model.get_response(instruction_repair_largest_cluster_requirement,
                                               prompt_repair_largest_cluster_requirement(requirement, entry_point,
                                                                                         programs,
                                                                                         specified_programs), True)
            repaired_requirement = unwrap(response, "requirement")
            if repaired_requirement != "":
                return repaired_requirement

    def repair_largest_cluster_requirement_localization(self, requirement, entry_point, programs, specified_programs):
        for i in range(10):
            print("REPAIR LARGEST CLUSTER REQUIREMENT WITH LOCALIZATION", i)
            identified_response = self.model.get_response(instruction_ambiguity_localization_largest_cluster,
                                                          prompt_ambiguity_localization_largest_cluster(requirement,
                                                                                                        entry_point,
                                                                                                        programs,
                                                                                                        specified_programs))
            identified_sentences = unwrap(identified_response, "sentences")
            identified_sentences_list = []
            for sentence in identified_sentences.splitlines():
                if sentence != "":
                    sentence = unwrap(sentence, "sentence")
                    if sentence in requirement:
                        identified_sentences_list.append(sentence)
            if not identified_sentences_list:
                return self.repair_largest_cluster_requirement(requirement, entry_point, programs, specified_programs)
            revised_response = self.model.get_response(instruction_ambiguous_sentence_repair_largest_cluster,
                                                       prompt_ambiguous_sentence_repair_largest_cluster(requirement,
                                                                                                        entry_point,
                                                                                                        identified_sentences_list,
                                                                                                        programs,
                                                                                                        specified_programs))
            revised_sentences = unwrap(revised_response, "revised_sentences")
            revised_sentences_list = [unwrap(sentence, "revised_sentence") for sentence in
                                      revised_sentences.splitlines()]
            for (identified_sentence, revised_sentence) in zip(identified_sentences_list, revised_sentences_list):
                revised_sentence = (revised_sentence[0].upper() if identified_sentence[0].isupper() else
                                    revised_sentence[0].lower()) + revised_sentence[1:]
                requirement = requirement.replace(identified_sentence, revised_sentence)
            return requirement

    def pass_k_sample(self, requirement, inputs, outputs, entry_point, k, sample):
        if entry_point == "combinations_colors":
            return calculate_pass_k(sample, sample, k), [], []
        if requirement is None:
            return None, [], []
        passes = 0
        generated_programs = []
        failed_inputs_outputs = []
        actual_sample = sample
        for _ in range(sample):
            passed = False
            for _ in range(k):
                program = self.generate_program(requirement, entry_point)
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
