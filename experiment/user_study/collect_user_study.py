import random
import jsonlines
import pandas as pd


def random_select_problem(path, woe_path):
    with jsonlines.open(path) as reader, jsonlines.open(woe_path) as reader1, jsonlines.open(
            "user_study.jsonl") as reader2:
        used_problems = [problem for problem in reader2]
        problems = [problem for problem in reader][50:]
        problems_woe = [problem for problem in reader1][50:]
        problems_exclude = []
        for problem in problems:
            if problem["task_id"] not in [p["task_id"] for p in used_problems]:
                problems_exclude.append(problem)
        random_problems = random.sample(problems_exclude, 10)
        results = []
        record = []
        for p in random_problems:
            d = {"requirement": p["requirement"]}
            d["requirement_without_examples"] = \
                [p1["requirement"] for p1 in problems_woe if p1["task_id"] == p["task_id"]][0]
            results.append(d)
            p["requirement_without_examples"] = d["requirement_without_examples"]
            record.append(p)
        return results, record


paths = [
    ["../../dataset/humaneval.jsonl", "../../dataset/humaneval_woe.jsonl"],
    ["../../dataset/mbpp.jsonl", "../../dataset/mbpp_woe.jsonl"],
    ["../../dataset/taco_lite.jsonl", "../../dataset/taco_lite_woe.jsonl"]
]

# user_study1 = []
# user_study2 = []
# user_study3 = []
# records = []
# for path in paths:
#     problems, record = random_select_problem(*path)
#     user_study1.extend(problems[:10])
#     user_study2.extend(problems[10:20])
#     user_study3.extend(problems[20:])
#     records.extend(record)
#
# random.shuffle(user_study1)
# random.shuffle(user_study2)
# random.shuffle(user_study3)
#
# df = pd.DataFrame(user_study1)
# df.to_csv("user_study1.csv", index=False)
#
# df = pd.DataFrame(user_study2)
# df.to_csv("user_study2.csv", index=False)
#
# df = pd.DataFrame(user_study3)
# df.to_csv("user_study3.csv", index=False)
#
# with jsonlines.open("user_study.jsonl", mode='w') as writer:
#     for record in records:
#         writer.write(record)

user_study4 = []
records = []
for path in paths:
    problems, record = random_select_problem(*path)
    user_study4.extend(problems)
    records.extend(record)
random.shuffle(user_study4)
df = pd.DataFrame(user_study4)
df.to_csv("user_study4.csv", index=False)

with jsonlines.open("user_study.jsonl") as reader, jsonlines.open("new_user_study.jsonl", "w") as writer:
    problems = [problem for problem in reader]
    problems.extend(records)
    problems = sorted(problems, key=lambda p: int(p["task_id"].split("/")[-1]))
    for problem in problems:
        writer.write(problem)
