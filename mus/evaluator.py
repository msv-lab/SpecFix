import random
import pandas as pd

from mus.prompting import *
from mus.model import Model
from mus.utils import construct_test_case, unwrap


class MUSAccuracyEvaluator:
    def __init__(self, api_key, differential_tester, model="qwen2.5-coder-7b-instruct", temperature=1.0):
        self.differential_tester = differential_tester
        self.model = Model(model, api_key, temperature)
        self.temperature = temperature

        # Initialize result tracking
        self.total_runs = 0
        self.successful_runs = 0
        self.run_details = []

    def generate_programs(self, requirements):
        print("GENERATE PROGRAMS")
        response = self.model.get_response(instruction_generate_code,
                                           prompt_generate_code(requirements))
        return unwrap(response)

    def generate_tests(self, requirements):
        print("GENERATE TESTS INPUTS")
        response = self.model.get_response(instruction_generate_test,
                                           prompt_generate_test(requirements))
        try:
            response = eval(unwrap(response, "test"))
        except Exception as e:
            response = self.generate_tests(requirements)
        return response

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

    def find_discrepancy_DRS(self, requirements, clusters):
        print("FIND DISCREPANCY WITH DRS")
        DRS_list = [cluster.DRS for cluster in clusters]
        response = self.model.get_response(instruction_find_discrepancy_DRS,
                                           prompt_find_discrepancy_DRS(requirements, DRS_list))
        return unwrap(response, "discrepancy")

    def find_discrepancy(self, requirements):
        print("FIND DISCREPANCY")
        response = self.model.get_response(instruction_find_discrepancy,
                                           prompt_find_discrepancy(requirements),
                                           )
        return unwrap(response, "discrepancy")

    def find_discrepancy_probe(self, requirements, clusters):
        print("FIND DISCREPANCY WITH PROBE")
        probe_list = [cluster.probe for cluster in clusters]
        response = self.model.get_response(instruction_find_discrepancy_probe,
                                           prompt_find_discrepancy_probe(requirements, probe_list))
        return unwrap(response, "discrepancy")

    def simulate_answer(self, requirement, program, inputs, question):
        tests = construct_test_case(program, inputs)
        print("SIMULATE ANSWER")
        response = self.model.get_response(instruction_simulated_answer,
                                           prompt_simulated_answer(requirement, program, tests, question))
        return unwrap(response, "answer")

    def minimize_requirement(self, requirements):
        print("MINIMIZE REQUIREMENT")
        response = self.model.get_response(instruction_minimize_requirement,
                                           prompt_minimize_requirement(requirements))
        return unwrap(response, "requirement")

    def mus_code(self, program, initial_requirement, task_id, N, max_iterations=10, DRS=False):
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
                clusters = self.differential_tester(generated_programs, test_inputs)
                if len(clusters) == 1:
                    self.successful_runs += 1
                    self.run_details.append({
                        'task_id': task_id,
                        'initial_requirement': initial_requirement,
                        'iterations_to_success': iteration + 1,
                        'success': True
                    })
                    return requirement
                for cluster in clusters:
                    cluster.set_requirement(self.generate_requirement(random.choice(cluster.programs_str)))
                    cluster.set_distribution(len(cluster.programs_str) / N)
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

    def mus_probe(self, program, initial_requirement, task_id, N, max_iterations=10):
        self.total_runs += 1
        requirement = initial_requirement
        test_inputs = self.generate_tests(requirement)
        try:
            for iteration in range(max_iterations):
                print("REQUIREMENT:", task_id)
                print(requirement)
                print(f"PROBING FOR ITERATION {iteration}:")
                requirement_clusters = self.differential_tester(requirement, N, test_inputs)
                if len(requirement_clusters) == 1:
                    self.successful_runs += 1
                    self.run_details.append({
                        'task_id': task_id,
                        'initial_requirement': initial_requirement,
                        'iterations_to_success': iteration + 1,
                        'success': True
                    })
                    return requirement
                cots = ""
                for i, cluster in enumerate(requirement_clusters):
                    cots += f"COT {i + 1}: {random.choice(cluster.descriptions)}\n"
                clarifying_question = self.find_discrepancy_probe(requirement, requirement_clusters)
                answer = self.simulate_answer(requirement, program, test_inputs, clarifying_question)
                requirement = self.repair_requirements(requirement, answer)

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

        print("\n--- MUS Computation Accuracy ---")
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
