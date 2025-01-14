import random
import pandas as pd

from mus.prompting import *
from mus.model import Model
from mus.utils import construct_test_case, unwrap

class MUSAccuracyEvaluator:
    def __init__(self, api_key, differential_tester=None, model="qwen2.5-coder-7b-instruct", temperature=1.0):
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
                                           prompt_generate_code(requirements), 0.8)
        code = unwrap(response, "code")
        if code == "":
            return self.generate_programs(requirements)
        return code

    def generate_tests(self, requirements):
        print("GENERATE TESTS INPUTS")
        response = self.model.get_response(instruction_generate_test,
                                           prompt_generate_test(requirements))
        try:
            response = eval(unwrap(response, "test"))
            if isinstance(response, list) and all(isinstance(t, list) for t in response):
                response = [t for t in response if t != []]
                if len(response) > 0:
                    return response
                else:
                    raise Exception
            else:
                raise Exception
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

    def find_discrepancy_fact(self, requirements, code, facts, assumptions, inp, outputs):
        print("FIND DISCREPANCY WITH FACT")
        # response = self.model.get_response(instruction_find_discrepancy_fact,
        # return unwrap(response, "discrepancy")

    def simulate_answer(self, requirement, program, inputs, question):
        tests = construct_test_case(program, inputs)
        print("SIMULATE ANSWER")
        response = self.model.get_response(instruction_simulated_answer,
                                           prompt_simulated_answer(requirement, program, tests, question))
        return unwrap(response, "answer")

    def minimize_requirement(self, ori_req, repaired_req):
        print("MINIMIZE REQUIREMENT")
        response = self.model.get_response(instruction_minimize_requirement,
                                           prompt_minimize_requirement(ori_req, repaired_req))
        return unwrap(response, "requirement")

    def generate_facts(self, requirement):
        print("GENERATE FACTS")
        response = self.model.get_response(instruction_generate_fact,
                                           prompt_generate_fact(requirement))
        code = unwrap(response, "code")
        fact = unwrap(response, "facts")
        assumption = unwrap(response, "assumptions")
        return code, fact, assumption

    def mus_code(self, program, initial_requirement, entry_point, task_id, N, max_iterations=10, DRS=False):
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
                for cluster in clusters.get_clusters():
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

    def generate_clarifying_question(self, requirement, information):
        print("GENERATE CLARIFYING QUESTION")
        response = self.model.get_response(instruction_generate_clarifying_question,
                                           prompt_generate_clarifying_question(requirement, information))
        return unwrap(response, "question")

    def classification(self, requirements):
        print("CLASSIFICATION")
        response = self.model.get_response(instruction_classification,
                                           prompt_classification(requirements))
        answer = unwrap(response, "answer")
        reason = unwrap(response, "reasoning")
        return answer, reason

    def vanilla_repair(self, requirement):
        print("VANILLA REPAIR")
        response = self.model.get_response(instruction_vanilla_repair,
                                           prompt_vanilla_repair(requirement))
        return unwrap(response, "requirement")
