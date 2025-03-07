import argparse
import sys

import jsonlines
from os.path import abspath, dirname
from concurrent.futures import ThreadPoolExecutor, as_completed
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_output_file, get_evalplus_inputs_outputs, get_taco_lite_inputs_outputs, \
    unify_model_name

sys.set_int_max_str_digits(0)


def process_case(i, problem, specfix_accuracy_evaluator, inputs, outputs):
    requirement = problem['requirement']

    answer, reason = specfix_accuracy_evaluator.classification(requirement)
    print("Case #{}: {}\n{}".format(i, answer, reason))
    repaired_requirement = None
    if answer == "Yes":
        repaired_requirement = specfix_accuracy_evaluator.vanilla_repair_requirements(requirement)
        print(f"Case {i}: Repaired requirement: {repaired_requirement}")
    original_result, repaired_result, failed_inputs_outputs = specfix_accuracy_evaluator.pass_k(requirement,
                                                                                                repaired_requirement,
                                                                                                inputs[i],
                                                                                                outputs[i],
                                                                                                problem[
                                                                                                    'entry_point'],
                                                                                                1)
    result = {
        'task_id': problem['task_id'],
        'original_requirement': requirement,
        'original_result': original_result,
        'ambiguity': answer,
        'reason': reason,
        'repaired_requirement': repaired_requirement,
        'repaired_result': repaired_result,
        'original_failed_inputs_outputs': str(failed_inputs_outputs[0]),
        'repaired_failed_inputs_outputs': str(failed_inputs_outputs[1])
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", dest="dataset",
                        help="Name of dataset: taco_lite, humaneval, mbpp")
    parser.add_argument("-p", "--dataset_path", dest="dataset_path",
                        help="Path to dataset")
    parser.add_argument("-m", "--model", dest="model")
    parser.add_argument("-woe", "--without_example", dest="without_example", action='store_true')

    options = parser.parse_args()
    model_name = options.model

    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        model=model_name,
    )

    model_name = unify_model_name(model_name)
    dataset = options.dataset
    dataset_path = options.dataset_path
    wo_example = "_woe" if options.without_example else ""

    output_file = construct_output_file(dirname(abspath(__file__)), model_name, dataset, None, wo_example,
                                        "vanilla_repair")
    if dataset == "humaneval" or dataset == "mbpp":
        inputs, outputs = get_evalplus_inputs_outputs(dataset)
    else:
        inputs, outputs = get_taco_lite_inputs_outputs()

    with jsonlines.open(dataset_path) as reader, jsonlines.open(output_file, mode='w', flush=True) as writer:
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Prepare arguments for process_case
            futures = [executor.submit(process_case, i, problem, specfix_accuracy_evaluator, inputs, outputs) for
                       i, problem in
                       enumerate(reader) if i >= 50]
            results = [future.result() for future in as_completed(futures)]
            # sort results by task_id
            results = sorted(results, key=lambda x: int(x['task_id'].split('/')[-1]))
            writer.write_all(results)
        # for i, problem in enumerate(reader):
        #     if i < 50:
        #         continue
        #     print(f"Case {i}: {problem['requirement']}")
        #     result = process_case(i, problem, specfix_accuracy_evaluator, inputs, outputs)
        #     writer.write(result)


if __name__ == "__main__":
    main()
