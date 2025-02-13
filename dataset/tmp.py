import jsonlines

# with jsonlines.open("humaneval_woe.jsonl") as reader, jsonlines.open("humaneval_woe1.jsonl", mode="w",
#                                                                      flush=True) as writer:
#     for i, problem in enumerate(reader):
#         if problem["starter_code"] not in problem["requirement"]:
#             lines = []
#             for line in problem["requirement"].split("\n"):
#                 lines.append(line)
#                 if f"def {problem['entry_point']}" in line:
#                     original_starter_code = "\n".join(lines)
#                     break
#             problem["requirement"] = problem["requirement"].replace(original_starter_code, problem["starter_code"])
#         writer.write(problem)
with jsonlines.open("mbpp.jsonl") as reader, jsonlines.open("mbpp_pilot.jsonl", "w") as writer:
    for i, problem in enumerate(reader):
        if i < 50:
            writer.write(problem)

with jsonlines.open("mbpp_woe.jsonl") as reader, jsonlines.open("mbpp_woe_pilot.jsonl", "w") as writer:
    for i, problem in enumerate(reader):
        if i < 50:
            writer.write(problem)

with jsonlines.open("taco_lite.jsonl") as reader, jsonlines.open("taco_lite_pilot.jsonl", "w") as writer:
    for i, problem in enumerate(reader):
        if i < 50:
            writer.write(problem)

with jsonlines.open("taco_lite_woe.jsonl") as reader, jsonlines.open("taco_lite_woe_pilot.jsonl", "w") as writer:
    for i, problem in enumerate(reader):
        if i < 50:
            writer.write(problem)