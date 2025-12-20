#!/usr/bin/env python3
import json
import sys
import traceback
import math
import csv  # For CSV output

def convert_to_expected(actual, expected):
    """
    Attempts to convert 'actual' into the same type as 'expected'.
    If conversion fails, returns the original 'actual'.
    """
    if actual is None:
        return actual
    exp_type = type(expected)
    try:
        if exp_type is tuple:
            return tuple(actual) if not isinstance(actual, tuple) else actual
        elif exp_type is list:
            return list(actual) if not isinstance(actual, list) else actual
        elif exp_type is int:
            return int(actual)
        elif exp_type is float:
            return float(actual)
        elif exp_type is str:
            return str(actual)
        elif exp_type is dict:
            return dict(actual)
        else:
            return exp_type(actual)
    except Exception:
        return actual

def compare_outputs(actual, expected):
    """
    Converts the actual output to the type of expected output and then compares them.
    For floats, a small tolerance is allowed.
    """
    try:
        converted = convert_to_expected(actual, expected)
        if isinstance(expected, float):
            return abs(converted - expected) < 1e-6
        return converted == expected
    except Exception:
        return False

def run_requirement(req_obj):
    """
    Process a single requirement JSON object:
      - Determines the function name from "entry_point" or "input_output.fn_name".
      - Iterates over the provided solution codes (in "solutions") and selects the
        first solution that produces a non-None output for all examples.
      - Runs the chosen solution on each example and compares the result (after conversion)
        to the expected output.
    
    Returns a tuple (fn_name, results) where results is a list of tuples:
        (input_args, expected_output, actual_output, passed_boolean)
    """
    # Determine the function name.
    fn_name = req_obj.get("entry_point")
    if not fn_name:
        fn_name = req_obj.get("input_output", {}).get("fn_name")
    if not fn_name:
        print("No entry point (function name) found in requirement.")
        return None

    # Extract examples: expecting a two-element list:
    # [ list_of_input_examples, list_of_expected_outputs ]
    examples = req_obj.get("example")
    if not examples or len(examples) != 2:
        print(f"No valid 'example' field found for requirement '{fn_name}'.")
        return None
    example_inputs, expected_outputs = examples
    if len(example_inputs) != len(expected_outputs):
        print(f"Mismatch in number of inputs and outputs for requirement '{fn_name}'.")
        return None

    # Iterate over all solutions and choose one that doesn't return None for any example.
    solutions = req_obj.get("solutions", [])
    if not solutions:
        print(f"No solutions provided for requirement '{fn_name}'.")
        return None

    chosen_solution_code = None
    for sol_code in solutions:
        env = {}
        try:
            exec(sol_code, env)
        except Exception as e:
            continue  # Skip solution if it fails to execute.
        if fn_name not in env:
            continue
        fn = env[fn_name]
        valid = True
        for inp, _ in zip(example_inputs, expected_outputs):
            if not isinstance(inp, list):
                inp = [inp]
            try:
                result = fn(*inp)
            except Exception:
                valid = False
                break
            if result is None:
                valid = False
                break
        if valid:
            chosen_solution_code = sol_code
            break

    # If none of the solutions produced a valid (non-None) result, fallback to the first solution.
    if chosen_solution_code is None:
        chosen_solution_code = solutions[0]

    # Execute the chosen solution code.
    env = {}
    try:
        exec(chosen_solution_code, env)
    except Exception as e:
        print(f"Error executing chosen solution code for '{fn_name}': {e}")
        traceback.print_exc()
        return None

    if fn_name not in env:
        print(f"Function '{fn_name}' was not defined in the executed solution code.")
        return None

    fn = env[fn_name]

    # Run the chosen solution on all examples.
    results = []
    for idx, (inp, expected) in enumerate(zip(example_inputs, expected_outputs)):
        # Ensure input is a list of arguments.
        if not isinstance(inp, list):
            inp = [inp]
        try:
            actual = fn(*inp)
        except Exception as e:
            print(f"Error calling function '{fn_name}' on example {idx+1} with input {inp}: {e}")
            traceback.print_exc()
            actual = None
        passed = compare_outputs(actual, expected)
        results.append((inp, expected, actual, passed))
    return fn_name, results

def main(jsonl_file_path):
    total_requirements = 0
    fully_matching_requirements = 0  # Count of fully passed (all examples passed)
    failed_requirements_details = {}
    summary_rows = []  # For per-requirement CSV summary

    try:
        with open(jsonl_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error opening JSONL file '{jsonl_file_path}': {e}")
        sys.exit(1)

    for line_no, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            print(f"Error parsing JSON on line {line_no}: {e}")
            continue

        total_requirements += 1
        result = run_requirement(req)
        if result is None:
            print(f"Skipping requirement on line {line_no} due to errors.\n")
            continue

        fn_name, results = result
        total_examples = len(results)
        passed_examples = sum(1 for r in results if r[3])
        failed_examples = total_examples - passed_examples

        # Determine overall status for this requirement:
        # Fully Passed: all examples passed
        # Failed: no examples passed
        # Partially Passed: some (but not all) examples passed
        if passed_examples == total_examples:
            overall_status = "Fully Passed"
            fully_matching_requirements += 1
        elif passed_examples == 0:
            overall_status = "Failed"
        else:
            overall_status = "Partially Passed"

        percentage_passed = (passed_examples / total_examples) * 100 if total_examples > 0 else 0
        summary_rows.append([
            fn_name, 
            total_examples, 
            passed_examples, 
            failed_examples, 
            f"{percentage_passed:.2f}%", 
            overall_status
        ])

        print(f"Testing '{fn_name}' (line {line_no}):")
        for i, (inp, expected, actual, passed) in enumerate(results, start=1):
            status_str = "Match" if passed else "Not match"
            print(f"  Example {i}: (Input: {inp}, Expected: {expected}, Got: {actual}) - {status_str}")
        print()

        if overall_status != "Fully Passed":
            failed_requirements_details[fn_name] = results

    # Print console summary.
    print("=== Summary ===")
    print(f"Total requirements processed: {total_requirements}")
    if total_requirements > 0:
        percentage_overall = (fully_matching_requirements / total_requirements) * 100
        print(f"Requirements with all examples matching (Fully Passed): {fully_matching_requirements} ({percentage_overall:.2f}%)")
    else:
        print("No requirements processed.")
    
    if failed_requirements_details:
        print("\nDetailed discrepancies:")
        for fn_name, results in failed_requirements_details.items():
            print(f"Requirement: {fn_name}")
            for i, (inp, expected, actual, passed) in enumerate(results, start=1):
                if not passed:
                    print(f"  Example {i}: Input: {inp}, Expected: {expected}, Got: {actual}")
    else:
        print("All requirements passed all examples.")

    # Write per-requirement summary report to CSV.
    summary_csv = "summary_report.csv"
    try:
        with open(summary_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "Requirement", 
                "Total Examples", 
                "Passed Examples", 
                "Failed Examples", 
                "Percentage Passed", 
                "Status"
            ])
            for row in summary_rows:
                writer.writerow(row)
        print(f"\nCSV per-requirement summary report written to {summary_csv}")
    except Exception as e:
        print(f"Error writing CSV per-requirement summary report: {e}")

    # Compute overall counts for the overall summary CSV.
    processed_requirements = len(summary_rows)
    fully_passed_count = 0
    partially_passed_count = 0
    failed_count = 0
    failed_tags = []  # List of requirement tags (function names) that failed completely.

    for row in summary_rows:
        fn_name, total_ex, passed_ex, _, _, status = row
        if status == "Fully Passed":
            fully_passed_count += 1
        elif status == "Failed":
            failed_count += 1
            failed_tags.append(fn_name)
        else:  # Partially Passed
            partially_passed_count += 1

    percentage_fully_passed = (fully_passed_count / processed_requirements * 100) if processed_requirements > 0 else 0

    # Write overall summary CSV.
    overall_csv = "overall_summary.csv"
    try:
        with open(overall_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "Fully Passed", 
                "Partially Passed", 
                "Failed", 
                "Percentage Fully Passed", 
                "Failed Requirement Tags"
            ])
            writer.writerow([
                fully_passed_count, 
                partially_passed_count, 
                failed_count, 
                f"{percentage_fully_passed:.2f}%", 
                ", ".join(failed_tags)
            ])
        print(f"CSV overall summary report written to {overall_csv}")
    except Exception as e:
        print(f"Error writing CSV overall summary report: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify.py <jsonl_file>")
        sys.exit(1)
    jsonl_file_path = sys.argv[1]
    main(jsonl_file_path)
