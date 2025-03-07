import ast
import random
import pandas as pd
from copy import deepcopy
from specfix.prompting import *
from specfix.model import Model
from specfix.utils import unwrap, get_entry_point, execute_inputs, compare, get_failed_input_output


class SpecFixAccuracyEvaluator:
    def __init__(self, api_key, differential_tester=None, model="qwen2.5-coder-7b-instruct", temperature=1.0, top_p=1.0):
        self.differential_tester = differential_tester
        self.model = Model(model, api_key, temperature, top_p)
        self.temperature = temperature

        # Initialize result tracking
        self.total_runs = 0
        self.successful_runs = 0
        self.run_details = []

    def generate_programs(self, requirements):
        print("GENERATE PROGRAMS")
        response = self.model.get_response(instruction_generate_code,
                                           prompt_generate_code(requirements), 1)
        code = unwrap(response, "code")
        if code == "":
            return self.generate_programs(requirements)
        return code
    
    def generate_program(self, requirements, entry_point):
        for i in range(5):
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
                continue
        print("GENERATE PROGRAM FAILED")
        return ""
    
    # ClarifyGPT has two prompts for generating programs: one for the first programs generated, and one for after requirements have been repaired
    def generate_initial_programs_clarify_gpt(self, requirements, n_shot):
        print("GENERATE INITIAL PROGRAMS")
        
        # parse requirements imports
        first_def = requirements.find('def ')
        imports = requirements[:first_def] if first_def != -1 else ""
        
        response = self.model.get_response_few_shot(prompt_generate_initial_code_clarify_gpt(requirements), 0.8)
        code = unwrap(response, "code")
        if code == "":
            return self.generate_initial_program_clarify_gpt(requirements, n_shot)
        
        return imports + code
    
    def generate_programs_clarify_gpt(self, requirements, n_shot):
        print("GENERATE PROGRAMS")
        
        # parse requirements imports
        first_def = requirements.find('def ')
        imports = requirements[:first_def] if first_def != -1 else ""
        
        response = self.model.get_response_few_shot(prompt_generate_code_clarify_gpt(requirements, n_shot), 0.8)
        code = unwrap(response, "code")
        
        if code == "":
            return self.generate_program_clarify_gpt(requirements, n_shot)
        
        return imports + code

    def generate_initial_program_clarify_gpt(self, requirements, n_shot):
        for i in range(5):
            try:
                print("GENERATE INITIAL PROGRAM ATTEMPT", i)
                response = self.model.get_response_few_shot(prompt_generate_initial_code_clarify_gpt(requirements), 0.8)
                code = unwrap(response, "code")
                if code == "" or "exit()" in code or "quit()" in code:
                    print(response)
                    raise Exception
                return code
            except Exception as e:
                print(e)
                continue
        print("GENERATE INITIAL PROGRAM FAILED")
        return ""

    def generate_program_clarify_gpt(self, requirements, n_shot):
        for i in range(5):
            try:
                print("GENERATE PROGRAM ATTEMPT", i)
                response = self.model.get_response_few_shot(prompt_generate_code_clarify_gpt(requirements, n_shot), 0.8)
                code = unwrap(response, "code")
                if code == "" or "exit()" in code or "quit()" in code:
                    raise Exception
                return code
            except Exception as e:
                print(e)
                continue
        print("GENERATE PROGRAM FAILED")
        return ""

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
    
    def generate_tests_clarify_gpt(self, requirements, n_shot):
        print("GENERATE TESTS INPUTS")
        response = self.model.get_response_few_shot(prompt_generate_test_clarify_gpt(requirements, n_shot))
        try:
            print(response)
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

    def type_aware_mutation(self, tests, n=25):
        
        def mutate_single(x):
            if x is None:
                return None
                
            if isinstance(x, (int, float)):
                return x + random.choice([-1, 1])
                
            elif isinstance(x, bool):
                return random.choice([True, False])
                
            elif isinstance(x, str):
                if not x:  # Handle empty string
                    return x 
                
                mutation_type = random.choice(['remove', 'repeat', 'replace'])
                if mutation_type == 'remove':
                    pos = random.randint(0, len(x) - 1)
                    return x[:pos] + x[pos + 1:]
                elif mutation_type == 'repeat':
                    pos = random.randint(0, len(x) - 1)
                    return x[:pos] + x[pos] + x[pos:]
                else:  # replace
                    pos = random.randint(0, len(x) - 1)
                    return x[:pos] + mutate_single(x[pos]) + x[pos + 1:]
                    
            elif isinstance(x, list):
                if not x:  # Handle empty list
                    return x
                    
                mutation_type = random.choice(['remove', 'repeat', 'insert'])
                mutated = copy.deepcopy(x)
                
                if mutation_type == 'remove' and mutated:
                    del mutated[random.randint(0, len(mutated) - 1)]
                elif mutation_type == 'repeat' and mutated:
                    idx = random.randint(0, len(mutated) - 1)
                    mutated.insert(idx, mutated[idx])
                else:  # insert/replace
                    idx = random.randint(0, len(mutated) - 1)
                    mutated[idx] = mutate_single(mutated[idx])
                return mutated
                
            elif isinstance(x, tuple):
                return tuple(mutate_single(list(x)))
                
            elif isinstance(x, set):
                return set(mutate_single(list(x)))
                
            elif isinstance(x, dict):
                if not x:  # Handle empty dict
                    return x
                    
                mutation_type = random.choice(['remove', 'update', 'insert'])
                mutated = copy.deepcopy(x)
                
                if mutation_type == 'remove' and mutated:
                    key = random.choice(list(mutated.keys()))
                    del mutated[key]
                elif mutation_type == 'update' and mutated:
                    key = random.choice(list(mutated.keys()))
                    mutated[key] = mutate_single(mutated[key])
                else:  # insert
                    new_key = mutate_single(random.choice(list(mutated.keys())))
                    new_value = mutate_single(random.choice(list(mutated.values())))
                    mutated[new_key] = new_value
                return mutated
            
            # Unchanged if not supported type
            return x 
        
        tests = ast.literal_eval(tests)
        iterations = 0
        while(len(tests) < n and iterations < n*10):
            chosen_test = random.choice(tests)
            new_test = [mutate_single(x) for x in chosen_test]
            if new_test not in tests:
                tests.append(new_test)
            iterations += 1
        
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
    
    def repair_requirements_clarify_gpt(self, requirements, clarifying_questions, n_shot):
        print("CLARIFY GPT REPAIR REQUIREMENTS")
        try:
            response = self.model.get_response_few_shot(prompt_repair_requirement_clarify_gpt(requirements, clarifying_questions, n_shot))
            answers = unwrap(response, "answers")

            # Process to interleave questions and answers
            clarification_section = ""
            question_list = clarifying_questions.split('\n')
            answer_list = answers.split('\n')
            if (answer_list[0] == "### Answers:"):
                answer_list = answer_list[1:]
            num = 1
            for q, a in zip(question_list, answer_list):
                if (a[0] == str(num)):
                    a = a[3:]
                    num = num + 1
                clarification_section = clarification_section + f"{q}\n- {a}\n"
        except Exception as e:
            print(e)

        return f"{requirements[:-3]}\nClarification:\n{clarification_section}\n\"\"\""

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


    def minimize_requirement(self, ori_req, repaired_req):
        print("MINIMIZE REQUIREMENT")
        response = self.model.get_response(instruction_minimize_requirement,
                                           prompt_minimize_requirement(ori_req, repaired_req))
        return unwrap(response, "requirement")

    def inverse_requirement(self, code):
        print("INVERSE REQUIREMENT")
        response = self.model.get_response(instruction_inverse_requirement,
                                           prompt_inverse_requirement(code))
        return unwrap(response, "requirement")

    def test_based_repair(self, program, requirement, failed_semantic_input_output):

        print("TEST BASED REPAIR")
        response = self.model.get_response(instruction_test_based_repair,
                                           prompt_test_based_repair(requirement, program, failed_semantic_input_output))
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

    def generate_clarifying_question(self, requirement, information):
        print("GENERATE CLARIFYING QUESTION")
        response = self.model.get_response(instruction_generate_clarifying_question,
                                           prompt_generate_clarifying_question(requirement, information))
        return unwrap(response, "question")
    
    def generate_clarifying_question_clarify_gpt(self, requirement, inconsistent_solutions, n_shot):
        print("GENERATE CLARIFYING QUESTION")
        response = self.model.get_response_few_shot(messages=prompt_generate_clarifying_question_clarify_gpt(requirement, inconsistent_solutions, n_shot), max_tokens=800)
        return unwrap(response, "questions")

    def classification(self, requirements):
        print("CLASSIFICATION")
        response = self.model.get_response(instruction_classification,
                                           prompt_classification(requirements))
        answer = unwrap(response, "answer")
        reason = unwrap(response, "reasoning")
        return answer, reason
    
    def pass_k(self, original_requirement, repaired_requirement, inputs, outputs, entry_point, k):
        original_results = []
        repaired_results = []
        original_failed_inputs_outputs = []
        repaired_failed_inputs_outputs = []
        for _ in range(k):
            original_failed_input_output = None
            repaired_failed_input_output = None
            original_program = self.generate_program(original_requirement, entry_point)
            if original_program == "":
                original_results.append(False)
            else:
                result = execute_inputs(original_program, inputs, entry_point)
                if compare(result, outputs):
                    original_results.append(True)
                else:
                    original_failed_inputs_outputs, _ = get_failed_input_output(result, inputs, outputs)
                    original_results.append(False)
            if repaired_requirement is not None:
                repaired_entry_point = get_entry_point(repaired_requirement)
                repaired_program = self.generate_program(repaired_requirement, entry_point)
                if repaired_program == "":
                    repaired_results.append(False)
                else:
                    result = execute_inputs(repaired_program, inputs, repaired_entry_point)
                    if compare(result, outputs):
                        repaired_results.append(True)
                    else:
                        repaired_failed_inputs_outputs, _ = get_failed_input_output(result, inputs, outputs)
                        repaired_results.append(False)
            original_failed_inputs_outputs.append(original_failed_input_output)
            repaired_failed_inputs_outputs.append(repaired_failed_input_output)
        return any(original_results), any(repaired_results) if repaired_requirement is not None else any(
            original_results), [original_failed_inputs_outputs, repaired_failed_inputs_outputs]

    def pass_k_clarify_gpt(self, original_requirement, repaired_requirement, inputs, outputs, entry_point, n_shot, k):
        original_results = []
        repaired_results = []
        original_failed_inputs_outputs = []
        repaired_failed_inputs_outputs = []
        for _ in range(k):
            original_failed_input_output = None
            repaired_failed_input_output = None
            original_program = self.generate_initial_program_clarify_gpt(original_requirement, n_shot)
            if original_program == "":
                original_results.append(False)
            else:
                result = execute_inputs(original_program, inputs, entry_point)
                if compare(result, outputs):
                    original_results.append(True)
                else:
                    original_failed_inputs_outputs, _ = get_failed_input_output(result, inputs, outputs)
                    original_results.append(False)
            if repaired_requirement is not None:
                repaired_entry_point = get_entry_point(repaired_requirement)
                # repaired_program = self.generate_program_clarify_gpt(repaired_requirement, n_shot)
                # See dataset/clarifygpt_mbpp/mbpp_synthesize_three_shot_chatgpt_results.jsonl – they use iniital prorgram synthesis for final pass@1 analysis
                repaired_program = self.generate_initial_program_clarify_gpt(repaired_requirement, n_shot)
                if repaired_program == "":
                    repaired_results.append(False)
                else:
                    result = execute_inputs(repaired_program, inputs, repaired_entry_point)
                    if compare(result, outputs):
                        repaired_results.append(True)
                    else:
                        repaired_failed_inputs_outputs, _ = get_failed_input_output(result, inputs, outputs)
                        repaired_results.append(False)
            original_failed_inputs_outputs.append(original_failed_input_output)
            repaired_failed_inputs_outputs.append(repaired_failed_input_output)
        
        return any(original_results), any(repaired_results) if repaired_requirement is not None else any(
            original_results), [original_failed_inputs_outputs, repaired_failed_inputs_outputs]
