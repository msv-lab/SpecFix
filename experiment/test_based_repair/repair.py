import argparse
import ast
import sys
from os.path import dirname, abspath
import jsonlines
import concurrent.futures

from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import (
    get_evalplus_inputs_outputs,
    construct_output_file,
    read_jsonl,
    get_taco_lite_inputs_outputs,
    unify_model_name
)
from specfix.tester import differential_tester, ground_truth_tester

sys.set_int_max_str_digits(0)


def parse_problem(problem):
    requirement = problem['requirement']
    examples = problem['input_output_examples']
    entry_point = problem['entry_point']
    task_id = problem['task_id']
    return requirement, entry_point, examples, task_id


def process_problem(i, problem, inputs, outputs, evaluator, n_programs, threshold, model_name):
    requirement, entry_point, examples, task_id = parse_problem(problem)
    log_messages = []
    log_messages.append(f"Case {task_id}:\n{requirement}")

    test_inputs = ast.literal_eval(problem["llm_generated_inputs"][model_name])
    log_messages.append(f"Test inputs:\n{test_inputs}")

    # programs = evaluator.generate_programs(requirement, entry_point, n_programs)
    programs = evaluator.parallel_generate_programs(requirement, entry_point, n_programs)
    clusters = evaluator.get_clusters(programs, test_inputs, entry_point, examples)
    evaluator.calculate_ambiguity(clusters, entry_point)
    log_messages.append(f"Case {task_id}:\nclusters ambiguity: {clusters.ambiguity}")

    repaired_requirement = None
    repaired_clusters = None
    if clusters.ambiguity > threshold:
        cluster = clusters.get_largest_cluster()
        if cluster.test_consistency != 1:
            repaired_code = evaluator.test_based_repair(
                requirement, entry_point,
                cluster.programs_str[0],
                cluster.failed_input_output_examples
            )
            repaired_requirement = evaluator.repair_requirement(
                requirement, entry_point,
                repaired_code
            )
        else:
            other_programs = [c.programs_str[0] for c in clusters.cluster_list if c != cluster]
            repaired_requirement = evaluator.repair_largest_cluster_requirement(
                requirement, entry_point,
                other_programs, cluster.programs_str[0]
            )
        log_messages.append(f"Case {task_id}:\nRepaired requirement: {repaired_requirement}")

        # repaired_programs = evaluator.generate_programs(repaired_requirement, entry_point, n_programs)
        repaired_programs = evaluator.parallel_generate_programs(repaired_requirement, entry_point, n_programs)
        repaired_clusters = evaluator.get_clusters(repaired_programs, test_inputs, entry_point, examples)
        evaluator.calculate_ambiguity(repaired_clusters, entry_point)

    repaired_passk, generated_programs, failed_inputs_outputs = evaluator.pass_k_sample(
        repaired_requirement,
        inputs[i],
        outputs[i],
        entry_point,
        1, 10
    )

    writer_dict = {
        "task_id": task_id,
        "requirement": requirement,
        "repaired_requirement": repaired_requirement,
        "original_clusters": clusters.serialize(),
        "repaired_clusters": repaired_clusters.serialize() if repaired_clusters is not None else None,
        "original_passk": problem["original_passk"],
        "repaired_passk": problem["original_passk"] if repaired_passk is None else repaired_passk,
        "generated_programs": generated_programs,
        "failed_inputs_outputs": str(failed_inputs_outputs)
    }
    return i, writer_dict, repaired_passk, "\n".join(log_messages)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=20)
    parser.add_argument("-t", "--threshold", dest="threshold", type=float, default=0.7)
    parser.add_argument("-m", "--model", dest="model")
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')
    options = parser.parse_args()

    model_name = options.model
    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        differential_tester=differential_tester,
        ground_truth_tester=ground_truth_tester,
        model=model_name,
    )
    model_name = unify_model_name(model_name)

    dataset = options.dataset
    n_programs = options.number
    threshold = options.threshold
    wo_example = "_woe" if options.without_example else ""
    dataset_path = f"../../dataset/{dataset}{wo_example}.jsonl"

    if dataset in ["humaneval", "mbpp"]:
        inputs, outputs = get_evalplus_inputs_outputs(dataset)
    else:
        inputs, outputs = get_taco_lite_inputs_outputs()

    output_file = construct_output_file(
        dirname(abspath(__file__)),
        model_name,
        dataset,
        threshold,
        wo_example,
        "ambiguity_repair"
    )
    original_problems = read_jsonl(f"original_passk/{model_name}/{dataset}{wo_example}.jsonl")
    problems = read_jsonl(dataset_path)
    for problem, original_problem in zip(problems[50:], original_problems):
        problem["original_passk"] = original_problem["original_passk"]

    tasks = [(i, problem) for i, problem in enumerate(problems) if i >= 50]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor, \
            jsonlines.open(output_file, mode='w', flush=True) as writer:

        results = executor.map(
            lambda args: process_problem(
                *args, inputs, outputs, specfix_accuracy_evaluator, n_programs, threshold, model_name
            ),
            tasks
        )

        for i, writer_dict, repaired_passk, log_msg in results:
            print(log_msg)
            writer.write(writer_dict)


if __name__ == "__main__":
    main()