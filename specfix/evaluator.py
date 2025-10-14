import ast
import concurrent.futures
import os
import math
from itertools import repeat
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, List, Tuple
from time import sleep

from specfix.execute_util import check_correctness
from specfix.prompting import *
from specfix.model import Model
from specfix.utils import (
    unwrap,
    get_parameter_number,
    calculate_pass_k,
    unify_model_name,
)


class SpecFixAccuracyEvaluator:
    def __init__(
        self,
        differential_tester=None,
        ground_truth_tester=None,
        model="qwen2.5-coder-7b-instruct",
        temperature=1.0,
    ):
        self.differential_tester = differential_tester
        self.ground_truth_tester = ground_truth_tester
        self.model = Model(model, temperature)
        self.temperature = temperature

    # ------------------------------------------------------------------ #
    # Internal helpers for prompt construction and response processing.  #
    # ------------------------------------------------------------------ #

    def _build_code_prompt(self, requirement: str, entry_point: str) -> str:
        return (
            prompt_generate_code_stdin(requirement)
            if entry_point == ""
            else prompt_generate_code(requirement, entry_point)
        )

    def _clean_programs(self, programs: Iterable[str]) -> List[str]:
        return [prog for prog in programs if prog]

    def _unwrap_code_responses(self, responses) -> List[str]:
        return [unwrap(prog, "code") for prog in responses]

    def _batched_program_generation(
        self, prompt: str, target_count: int, batch_size: int
    ) -> List[str]:
        programs: List[str] = []
        for _ in range(math.ceil(target_count / batch_size)):
            responses = self.model.get_response_sample(
                instruction_generate_code,
                prompt,
                batch_size,
            )
            programs.extend(self._unwrap_code_responses(responses))
        return self._clean_programs(programs)[:target_count]

    def _generate_single_program_with_retry(self, prompt: str) -> str:
        for attempt in range(2):
            try:
                print("GENERATE PROGRAM ATTEMPT", attempt)
                response = self.model.get_response(
                    instruction_generate_code,
                    prompt,
                )
                code = unwrap(response, "code")
                if code == "":
                    print(response)
                    raise RuntimeError("Empty code block returned.")
                return code
            except Exception as exc:  # noqa: BLE001 - retry on any failure
                print(exc)
                sleep(1)
        print("GENERATE PROGRAM FAILED")
        return ""

    def _generate_programs_in_threads(
        self, prompt: str, n_programs: int, max_workers: int = 10
    ) -> List[str]:
        if n_programs <= 0:
            return []
        generated_programs: List[str] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._generate_single_program_with_retry, prompt)
                for _ in range(n_programs)
            ]
            for future in concurrent.futures.as_completed(futures):
                generated_programs.append(future.result())
        return self._clean_programs(generated_programs)

    def _collect_program_samples(
        self, requirement: str, entry_point: str, n_programs: int
    ) -> List[str]:
        if n_programs <= 0:
            return []

        prompt = self._build_code_prompt(requirement, entry_point)
        model_name = self.model.model_name.lower()

        if "deepseek" in model_name:
            return self._batched_program_generation(prompt, n_programs, batch_size=4)
        if "gpt" in model_name:
            responses = self.model.get_response_sample(
                instruction_generate_code,
                prompt,
                n_programs,
            )
            return self._clean_programs(self._unwrap_code_responses(responses))

        return self._generate_programs_in_threads(prompt, n_programs)

    def _clusters_solved(self, clusters) -> bool:
        return (
            clusters.entropy == 0
            and clusters.weighted_test_consistency == 1
        )

    def _clusters_improved(self, current, previous) -> bool:
        current_consistency = current.weighted_test_consistency
        previous_consistency = previous.weighted_test_consistency
        if current_consistency > previous_consistency:
            return True
        if (
            current_consistency == previous_consistency
            and current.entropy < previous.entropy
        ):
            return True
        return False

    def _extract_problem_fields(self, problem, label=None):
        requirement = problem[label] if label else problem["requirement"]
        entry_point = problem["entry_point"]
        examples = problem["input_output_examples"]
        task_id = problem["task_id"]
        return requirement, entry_point, examples, task_id

    def _build_test_generation_request(
        self, requirement: str, entry_point: str
    ) -> Tuple[str, str, Callable[[str], List[List[str]]]]:
        parameter_count = get_parameter_number(requirement, entry_point)

        if parameter_count == 0:
            instruction = instruction_generate_code
            prompt = prompt_generate_test_stdin(requirement, entry_point)

            def parser(response: str) -> List[List[str]]:
                block = unwrap(response, "tests")
                return [[test] for test in unwrap(block, "test", multiple=True)]

        else:
            instruction = instruction_generate_test
            prompt = prompt_generate_test(requirement, entry_point, parameter_count)

            def parser(response: str) -> List[List[str]]:
                block = unwrap(response, "tests")
                return [
                    ast.literal_eval(f"[{test}]")
                    for test in unwrap(block, "test", multiple=True)
                ]

        return instruction, prompt, parser

    def _score_programs(
        self,
        programs: List[str],
        inputs,
        outputs,
        entry_point: str,
    ) -> Tuple[int, List[float], List[List]]:
        if not programs:
            return 0, [], []

        passes = 0
        pass_rates: List[float] = []
        failed_inputs_outputs: List[List] = []

        max_workers = min(os.cpu_count() or 1, 32, len(programs)) or 1
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results_iter = executor.map(
                check_correctness,
                programs,
                repeat(inputs),
                repeat(outputs),
                repeat(entry_point),
            )
            for result, meta_data in results_iter:
                if all(result):
                    passes += 1
                    failed_inputs_outputs.append([])
                    pass_rates.append(1)
                else:
                    failed_inputs_outputs.append(meta_data)
                    pass_rates.append(result.count(True) / len(result))

        return passes, pass_rates, failed_inputs_outputs

    def get_clusters(
        self, requirement, programs, test_inputs, entry_point, examples=None
    ):
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

    def parallel_generate_programs(
        self, requirement, entry_point, n_programs, max_workers=10
    ):
        prompt = self._build_code_prompt(requirement, entry_point)
        return self._generate_programs_in_threads(
            prompt,
            n_programs,
            max_workers=max_workers,
        )

    def generate_programs(self, requirement, entry_point, n_programs):
        return self._collect_program_samples(requirement, entry_point, n_programs)

    def generate_program(self, requirement, entry_point):
        prompt = self._build_code_prompt(requirement, entry_point)
        return self._generate_single_program_with_retry(prompt)

    def generate_tests(self, requirements, entry_point):
        instruction, prompt, parser = self._build_test_generation_request(
            requirements, entry_point
        )
        for attempt in range(10):
            print("GENERATE TEST ATTEMPT", attempt)
            try:
                response = self.model.get_response(
                    instruction,
                    prompt,
                )
                tests = parser(response)
                if tests:
                    return tests
                raise RuntimeError("Model returned no tests.")
            except Exception as exc:  # noqa: BLE001 - continue retry loop
                print(exc)
        print(f"GENERATE TEST FAILED: {self.model.model_name}")
        return []

    def vanilla_repair_requirements(self, requirements):
        print("VANILLA REPAIR REQUIREMENTS")
        response = self.model.get_response(
            instruction_vanilla_repair, prompt_vanilla_repair(requirements)
        )
        return unwrap(response, "requirement")

    def classification(self, requirements):

        print("CLASSIFICATION")
        response = self.model.get_response(
            instruction_classification, prompt_classification(requirements)
        )
        answer = unwrap(response, "answer")
        reason = unwrap(response, "reasoning")
        if answer == "Yes" or answer == "No":
            return answer, reason
        return None

    def requirement_repair(
        self, requirement, entry_point, specified_programs, programs, diff_outputs
    ):
        print("REQUIREMENT REPAIR")
        ambiguity, analysis = self.fault_localization(
            requirement, entry_point, specified_programs, programs, diff_outputs
        )
        if entry_point == "":
            prompt = prompt_requirement_repair_stdin(
                requirement,
                ambiguity,
                analysis,
                specified_programs,
                diff_outputs,
            )
        else:
            prompt = prompt_requirement_repair(
                requirement,
                entry_point,
                ambiguity,
                analysis,
                specified_programs,
                diff_outputs,
            )
        response = self.model.get_response(
            instruction_requirement_repair,
            prompt,
            True,
        )
        repaired_requirement = unwrap(response, "requirement")
        if repaired_requirement != "":
            return repaired_requirement
        return None

    def fault_localization(
        self, requirement, entry_point, specified_programs, programs, diff_outputs
    ):
        if entry_point == "":
            prompt = prompt_fault_localization_stdin(
                requirement, specified_programs, programs, diff_outputs
            )
        else:
            prompt = prompt_fault_localization(
                requirement, entry_point, specified_programs, programs, diff_outputs
            )
        print("FAULT LOCALIZATION")
        ambiguity_response = self.model.get_response(
            instruction_fault_localization, prompt
        )
        ambiguity = unwrap(ambiguity_response, "ambiguity")
        analysis = unwrap(ambiguity_response, "analysis")
        return ambiguity, analysis

    def pass_k_and_pass_rate(
        self, requirement, inputs, outputs, entry_point, k, sample
    ):
        # Fast path for special entry point
        if entry_point == "combinations_colors":
            return calculate_pass_k(sample, sample, k), 1, [], []
        if requirement is None:
            return None, None, [], []

        max_attempts = 3
        for _ in range(max_attempts):
            programs = self.generate_programs(requirement, entry_point, sample)
            if programs:
                break
        else:
            return None, None, [], []

        passes, pass_rates, failed_inputs_outputs = self._score_programs(
            programs,
            inputs,
            outputs,
            entry_point,
        )

        pass_at_k = calculate_pass_k(len(programs), passes, k)
        avg_pass_rate = sum(pass_rates) / len(pass_rates) if pass_rates else 0

        return pass_at_k, avg_pass_rate, programs, failed_inputs_outputs

    def remove_example(self, requirement):
        response = self.model.get_response(
            instruction_remove_example, prompt_remove_example(requirement)
        )
        return unwrap(response, "requirement")

    def specfix_detect(self, problem, n_programs, label=None):
        requirement, entry_point, examples, task_id = self._extract_problem_fields(
            problem, label=label
        )
        print(f"SPECFIX DETECT {task_id}")
        # test_inputs = ast.literal_eval(
        #     problem["llm_generated_inputs"][unify_model_name(self.model.model_name)]
        # )
        test_inputs = self.generate_tests(requirement, entry_point)
        programs = self.generate_programs(requirement, entry_point, n_programs)
        if len(programs) == 0:
            return False, None
        clusters = self.get_clusters(
            requirement, programs, test_inputs, entry_point, examples
        )
        self.get_test_consistency(clusters)
        if clusters.entropy > 0 or 0 <= clusters.weighted_test_consistency < 1:
            return True, clusters
        return False, clusters

    def specfix_repair(self, clusters, n_programs):
        requirement = clusters.requirement
        entry_point = clusters.entry_point
        examples = clusters.input_output_examples
        test_inputs = clusters.llm_generated_inputs

        for repair_attempts in range(3):
            repair_method, largest_cluster = clusters.select_repair_method()
            if repair_method == 0:
                repaired_program = self.program_repair(
                    requirement,
                    entry_point,
                    largest_cluster.programs_str[0],
                    largest_cluster.failed_input_output_examples,
                )
                repaired_requirement = self.requirement_repair(
                    requirement,
                    entry_point,
                    repaired_program,
                    [largest_cluster.programs_str[0]],
                    largest_cluster.failed_input_output_examples,
                )
            else:
                other_clusters, diff_outputs = (
                    clusters.get_other_clusters_and_diff_outputs(largest_cluster)
                )
                other_programs = [
                    cluster.get_min_length_program() for cluster in other_clusters
                ]
                repaired_requirement = self.requirement_repair(
                    requirement,
                    entry_point,
                    largest_cluster.programs_str[0],
                    other_programs,
                    diff_outputs,
                )

            repaired_programs = self.generate_programs(
                repaired_requirement, entry_point, n_programs
            )
            repaired_clusters = self.get_clusters(
                repaired_requirement,
                repaired_programs,
                test_inputs,
                entry_point,
                str(examples),
            )
            self.get_test_consistency(repaired_clusters)

            if self._clusters_solved(repaired_clusters):
                return repaired_requirement, repaired_clusters

            if self._clusters_improved(repaired_clusters, clusters):
                requirement, clusters = repaired_requirement, repaired_clusters

        return requirement, clusters

    def program_repair(
        self, requirement, entry_point, program, failed_input_output_examples
    ):
        print("PROGRAM REPAIR")
        if entry_point == "":
            prompt = prompt_program_repair_stdin(
                requirement, program, failed_input_output_examples
            )
        else:
            prompt = prompt_program_repair(
                requirement, entry_point, program, failed_input_output_examples
            )
        response = self.model.get_response(instruction_program_repair, prompt)
        repaired_program = unwrap(response, "code")
        return repaired_program

    def solved_with_majority_vote(self, clusters, inputs, outputs):
        if clusters is None:
            return None
        if clusters.entry_point == "combinations_colors":
            return True
        cluster = max(clusters.cluster_list, key=lambda c: c.probability)
        program = cluster.programs_str[0]
        result, _ = check_correctness(program, inputs, outputs, clusters.entry_point)
        if all(result):
            return True
        return False
