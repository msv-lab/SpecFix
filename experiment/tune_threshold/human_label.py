import jsonlines

with jsonlines.open("ambiguity_detection/deepseek-v3/taco_lite.jsonl") as reader, jsonlines.open(
        "taco_lite_pilot_ground_truth.jsonl", "w", flush=True) as writer:
    for problem in reader:
        print(problem["requirement"])
        print(problem["clusters"]["entropy"])
        print(problem["clusters"]["weighted_test_consistency"])
        print(problem["clusters"]["ambiguity"])
        print(problem["clusters"]["llm_generated_inputs"])
        print(problem["clusters"]["input_output_examples"])
        problem["ground_truth"] = int(input("Enter ground truth: "))
        writer.write(problem)

with jsonlines.open("ambiguity_detection/deepseek-v3/taco_lite_woe.jsonl") as reader, jsonlines.open(
        "taco_lite_woe_pilot_ground_truth.jsonl", "w", flush=True) as writer:
    for problem in reader:
        print(problem["requirement"])
        print(problem["clusters"]["entropy"])
        print(problem["clusters"]["weighted_test_consistency"])
        print(problem["clusters"]["ambiguity"])
        print(problem["clusters"]["llm_generated_inputs"])
        print(problem["clusters"]["input_output_examples"])
        problem["ground_truth"] = int(input("Enter ground truth: "))
        writer.write(problem)