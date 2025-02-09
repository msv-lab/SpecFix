import argparse
from os.path import dirname, abspath

import jsonlines

from specfix.differential import differential_tester, ground_truth_tester
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_output_file, unwrap

instruction_label = "You are an assistant that classifies the understanding gap between different programs. "


def prompt_label(requirement, programs):
    program_str = ""
    for i, program in enumerate(programs):
        program_str += f"{i + 1}. {program}\n"
    return f"""
You will be given a user requirement and its candidate solutions. Your task is to clarify this requirement by asking clarifying questions. Specifically, you will first analyze the functionality of each solution. Then by comparing their differences, you can determine which parts in the requirement are ambiguous and ask targeted clarification questions.

Wrap your answer in <classification></classification> tags.

Requirement:
{requirement}

Solutions:
{program_str}   
    """


def parse_problem(problem):
    requirement = problem['requirement']
    entry_point = problem['entry_point']
    return requirement, entry_point


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=50)
    parser.add_argument("-m", "--model", dest="model")
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

    options = parser.parse_args()

    model_name = options.model
    dataset = options.dataset
    dataset_path = options.dataset_path
    n_programs = options.number
    wo_example = "_woe" if options.without_example else ""

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        differential_tester=differential_tester,
        ground_truth_tester=ground_truth_tester,
        model=model_name
    )

    output_file = construct_output_file(dirname(abspath(__file__)), model_name, dataset, None, wo_example, "labelled")

    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        for i, problem in enumerate(reader):
            result = {}
            requirement, entry_point = parse_problem(problem)
            print(f"Case {i}: {requirement}")

            test_inputs = specfix_accuracy_evaluator.generate_tests(requirement)
            print(f"Test inputs: {test_inputs}")
            programs = specfix_accuracy_evaluator.parallel_generate_programs(requirement, n_programs)
            clusters = specfix_accuracy_evaluator.get_clusters(programs, test_inputs, entry_point)
            result["task_id"] = problem["task_id"]
            result["requirement"] = requirement
            result["clusters"] = clusters.serialize()
            if len(clusters.get_cluster_list()) == 1:
                result["ground_truth"] = "Unambiguous"
            else:
                response = specfix_accuracy_evaluator.model.get_response(instruction_label, prompt_label(requirement, [
                    cluster.programs_str[0] for cluster in clusters.get_cluster_list()]))
                gaps = unwrap(response, "classification")
                result["gaps"] = gaps
                result["ground_truth"] = ""
            writer.write(result)


if __name__ == "__main__":
    main()
