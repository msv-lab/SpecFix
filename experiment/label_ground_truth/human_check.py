import jsonlines

with jsonlines.open("qwen-plus/taco_woe_labelled.jsonl") as reader, jsonlines.open(
        "qwen-plus/taco_woe_labelled1.jsonl", "w", flush=True) as writer:
    for i, problem in enumerate(reader):
        if problem["ground_truth"] == "":
            print(problem["requirement"])
            print("-" * 10)
            print(problem["gaps"])
            answer = int(input("Enter ground truth: "))
            if answer == 1:
                problem["ground_truth"] = "Unambiguous"
            elif answer == 0:
                problem["ground_truth"] = "Ambiguous"
        writer.write(problem)
