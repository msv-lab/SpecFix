import jsonlines
from pandas import read_csv

user_study1 = read_csv("../user_study1.csv")
user_study2 = read_csv("../user_study2.csv")
user_study3 = read_csv("../user_study3.csv")
user_study4 = read_csv("../user_study4.csv")

form1 = read_csv("User Study on Ambiguity in Requirements: Form1.csv").fillna("Unambiguous")
form2 = read_csv("User Study on Ambiguity in Requirements: Form2.csv").fillna("Unambiguous")
form3 = read_csv("User Study on Ambiguity in Requirements: Form3.csv").fillna("Unambiguous")
form4 = read_csv("User Study on Ambiguity in Requirements: Form4.csv").fillna("Unambiguous")

with jsonlines.open("../user_study.jsonl") as reader, jsonlines.open("user_study_with_feedbacks.jsonl", "w",
                                                                     flush=True) as writer:
    problems = list(reader)
    form1_list = [form1[col].tolist() for col in form1.columns]
    form2_list = [form2[col].tolist() for col in form2.columns]
    form3_list = [form3[col].tolist() for col in form3.columns]
    form4_list = [form4[col].tolist() for col in form4.columns]
    for index, row in user_study1.iterrows():
        candidates_woe = form1_list[2 * index + 1]
        candidates = form1_list[2 * index + 2]
        requirement = row["requirement"]
        for problem in problems:
            if requirement == problem["requirement"]:
                problem["human_feedback"] = candidates
                problem["human_feedback_without_examples"] = candidates_woe
                break

    for index, row in user_study2.iterrows():
        candidates_woe = form2_list[2 * index + 1]
        candidates = form2_list[2 * index + 2]
        requirement = row["requirement"]
        for problem in problems:
            if requirement == problem["requirement"]:
                problem["human_feedback"] = candidates
                problem["human_feedback_without_examples"] = candidates_woe
                break
    for index, row in user_study3.iterrows():
        candidates_woe = form3_list[2 * index + 1][1:]
        candidates = form3_list[2 * index + 2][1:]
        requirement = row["requirement"]
        for problem in problems:
            if requirement == problem["requirement"]:
                problem["human_feedback"] = candidates
                problem["human_feedback_without_examples"] = candidates_woe
                break
    for index, row in user_study4.iterrows():
        candidates_woe = form4_list[2 * index + 1]
        candidates = form4_list[2 * index + 2]
        requirement = row["requirement"]
        for problem in problems:
            if requirement == problem["requirement"]:
                problem["human_feedback"] = candidates
                problem["human_feedback_without_examples"] = candidates_woe
                break
    writer.write_all(problems)
