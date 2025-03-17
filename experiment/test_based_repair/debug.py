import argparse
import ast
import json
import sys
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import (
    get_evalplus_inputs_outputs,
    read_jsonl,
    get_taco_lite_inputs_outputs,
    unify_model_name
)
from specfix.tester import differential_tester, ground_truth_tester

sys.set_int_max_str_digits(0)


def main():
    # model = "qwen2.5-coder-32b-instruct"
    model = "deepseek-v3-241226"
    # model = "gpt-4o-mini"
    program_number = 20
    evaluator = SpecFixAccuracyEvaluator(
        differential_tester=differential_tester,
        ground_truth_tester=ground_truth_tester,
        model=model
    )

    problem = {
        "task_id": "debug",
        "requirement": """
        from typing import List, Tuple
def remove_connections(numbers: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
 \"\"\"
 From a graph defined via a list of connections between nodes, remove all connections that repeat between the same nodes. Keep order of remaining ones the same as in the input. 
 Example: remove_connections([(1, 2), (2, 3), (2, 1)]) = [(2, 3)]
 \"\"\"
        """,
        "entry_point": "remove_connections",
        "input_output_examples": "[[[[(1, 2), (2, 3), (2, 1)]]], [[[(2, 3)]]]]",
    }
    problem["llm_generated_inputs"] = {
        model: str(evaluator.generate_tests(problem["requirement"], problem["entry_point"]))
    }

    result, original_clusters = evaluator.specfix_detect(problem, program_number)
    if result:
        repaired_requirement, repaired_clusters = evaluator.specfix_repair(original_clusters,
                                                                           program_number)
        repaired_requirement_woe = evaluator.remove_example(repaired_requirement)
        _, repaired_requirement_woe_clusters = evaluator.specfix_detect(repaired_requirement_woe,
                                                                        program_number)
        # original_passk, original_generated_programs, original_failed_inputs_outputs = evaluator.pass_k_sample(
        #     problem["requirement"], inputs[i], outputs[i], problem["entry_point"], 1, 10
        # )
        # repaired_passk, repaired_generated_programs, repaired_failed_inputs_outputs = evaluator.pass_k_sample(
        #     repaired_requirement, inputs[i], outputs[i], problem["entry_point"], 1, 10
        # )
        # repaired_woe_passk, repaired_woe_generated_programs, repaired_woe_failed_inputs_outputs = evaluator.pass_k_sample(
        #     repaired_requirement_woe, inputs[i], outputs[i], problem["entry_point"], 1, 10
        # )
        result = {
            "task_id": problem["task_id"],
            "requirement": problem["requirement"],
            "repaired_requirement": repaired_requirement,
            "repaired_requirement_woe": repaired_requirement_woe,
            "original_clusters": original_clusters.serialize(),
            "repaired_clusters": repaired_clusters.serialize(),
            # "original_passk": original_passk,
            # "original_generated_programs": original_generated_programs,
            # "original_failed_inputs_outputs": str(original_failed_inputs_outputs),
            # "repaired_passk": repaired_passk,
            # "repaired_generated_programs": repaired_generated_programs,
            # "repaired_failed_inputs_outputs": str(repaired_failed_inputs_outputs),
            # "repaired_woe_passk": repaired_woe_passk,
            # "repaired_woe_generated_programs": repaired_woe_generated_programs,
            # "repaired_woe_failed_inputs_outputs": str(repaired_woe_failed_inputs_outputs),
        }
    else:
        result = {
            "task_id": problem["task_id"],
            "requirement": problem["requirement"],
            "repaired_requirement": None,
            "repaired_requirement_woe": None,
            "original_clusters": original_clusters.serialize(),
            "repaired_clusters": None,
            "original_passk": None,
            "original_generated_programs": None,
            "original_failed_inputs_outputs": None,
            "repaired_passk": None,
            "repaired_generated_programs": None,
            "repaired_failed_inputs_outputs": None,
            "repaired_woe_passk": None,
            "repaired_woe_generated_programs": None,
            "repaired_woe_failed_inputs_outputs": None,
        }
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
