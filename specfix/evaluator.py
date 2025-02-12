import ast
import concurrent.futures
import random
import pandas as pd

from specfix.prompting import *
from specfix.model import Model
from specfix.utils import unwrap, get_parameter_number


class SpecFixAccuracyEvaluator:
    def __init__(self, differential_tester=None, ground_truth_tester=None, model="qwen2.5-coder-7b-instruct",
                 temperature=1.0):
        self.differential_tester = differential_tester
        self.ground_truth_tester = ground_truth_tester
        self.model = Model(model, temperature)
        self.temperature = temperature

        # Initialize result tracking
        self.total_runs = 0
        self.successful_runs = 0
        self.run_details = []

    def get_clusters(self, programs, test_inputs, entry_point):
        clusters = self.differential_tester(programs, test_inputs, entry_point)
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
                                           prompt_generate_code(requirements), 1)
        code = unwrap(response, "code")
        if code == "":
            return self.generate_programs(requirements)
        return code

    def generate_tests(self, requirements, entry_point):
        print("GENERATE TESTS INPUTS")
        tests = []
        para_number = get_parameter_number(requirements, entry_point)
        response = self.model.get_response(instruction_generate_test,
                                           prompt_generate_test(requirements))
        try:
            response = unwrap(response, "tests")
            for line in response.splitlines():
                test = eval("[" + unwrap(line, "test") + "]")
                if len(test) == para_number:
                    tests.append(test)
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

    def generate_DRS(self, requirements):
        print("DRS GENERATION")
        response = self.model.get_response(instruction_generate_DRS,
                                           prompt_generate_DRS(requirements))
        return unwrap(response, "drs")

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

    def find_discrepancy_DRS(self, requirements, clusters):
        print("FIND DISCREPANCY WITH DRS")
        DRS_list = [cluster.DRS for cluster in clusters]
        response = self.model.get_response(instruction_find_discrepancy_DRS,
                                           prompt_find_discrepancy_DRS(requirements, DRS_list))
        return unwrap(response, "discrepancy")

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

    def specfix_code(self, program, initial_requirement, entry_point, task_id, N, max_iterations=10, DRS=False):
        self.total_runs += 1
        requirement = initial_requirement
        test_inputs = self.generate_tests(requirement)
        try:
            for iteration in range(max_iterations):
                print("REQUIREMENT:", task_id)
                print(requirement)
                # Generate programs (currently set to N=1 for testing speed)
                print(f"GENERATED PROGRAMS FOR ITERATION {iteration}:")
                generated_programs = []
                for i in range(N):
                    generated_programs.append(self.generate_programs(requirement))
                    print(generated_programs[i])

                # Check for clusters
                clusters = self.differential_tester(generated_programs, test_inputs, entry_point)
                if len(clusters) == 1:
                    self.successful_runs += 1
                    self.run_details.append({
                        'task_id': task_id,
                        'initial_requirement': initial_requirement,
                        'iterations_to_success': iteration + 1,
                        'success': True
                    })
                    return requirement
                for cluster in clusters.get_cluster_list():
                    cluster.set_requirement(self.generate_requirement(random.choice(cluster.programs_str)))
                requirements = ""
                for i, cluster in enumerate(clusters):
                    requirements += f"Requirement {i + 1}: {cluster.requirement}\n"
                if DRS:
                    DRSs = self.generate_DRS(requirements)
                    for i, cluster in enumerate(clusters):
                        cluster.set_DRS(DRSs[i])
                    clarifying_question = self.find_discrepancy_DRS(requirement, clusters)
                    answer = self.simulate_answer(requirement, program, test_inputs, clarifying_question)
                    requirement = self.repair_requirements(requirement, answer)
                else:
                    clarifying_question = self.find_discrepancy_DRS(requirement, clusters)
                    answer = self.simulate_answer(requirement, program, test_inputs, clarifying_question)
                    requirement = self.repair_requirements(requirement, answer)

                # requirement = self.minimize_requirement(requirement)
            # If max iterations reached
            self.run_details.append({
                'task_id': task_id,
                'initial_requirements': initial_requirement,
                'iterations_to_success': max_iterations,
                'success': False
            })
            return requirement
        except Exception as e:
            print('EXCEPTION THROWN: ', e)
            # If max iterations reached
            self.run_details.append({
                'task_id': task_id,
                'initial_requirement': initial_requirement,
                'iterations_to_success': max_iterations,
                'success': False
            })
            return requirement

    def calculate_accuracy(self):
        """Calculate and print accuracy metrics"""
        accuracy = self.successful_runs / self.total_runs if self.total_runs > 0 else 0

        print("\n--- SpecFix Computation Accuracy ---")
        print(f"Total Runs: {self.total_runs}")
        print(f"Successful Runs: {self.successful_runs}")
        print(f"Accuracy: {accuracy:.2%}")

        # Convert run details to DataFrame for further analysis
        df = pd.DataFrame(self.run_details)

        # Additional insights
        if not df.empty:
            print("\nAdditional Insights:")
            print("Success Rate by Iterations:")
            iterations_success = df.groupby('iterations_to_success')['success'].mean()
            print(iterations_success)

        return accuracy, df

    def get_probability(self):
        return self.successful_runs / self.total_runs if self.total_runs > 0 else 0

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
