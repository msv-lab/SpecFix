import os

import jsonlines
import random
from dotenv import load_dotenv, find_dotenv
from mus.evaluator import MUSAccuracyEvaluator
from mus.differential import differential_tester, model_verifier
load_dotenv()
verifier_name = "o1-mini"
verifier_api_key = os.getenv("API_KEY")


dataset_path = '../../dataset/TACO_lite.jsonl'
model_name = "qwen2.5-coder-14b-instruct"
api_key = os.getenv("API_KEY")
N = 10
mus_accuracy_evaluator = MUSAccuracyEvaluator(
    api_key=api_key,
    differential_tester=differential_tester,
    model=model_name,
    temperature=1
)

with jsonlines.open(dataset_path) as reader, jsonlines.open("ambiguity.json", "w",
                                                            flush=True) as ambiguity_file, jsonlines.open(
    "incorrect_generation.json", "w", flush=True) as incorrect_generation_file:
    ambiguity = []
    incorrect_generation = []
    for i, obj in enumerate(reader):
        requirement = obj['question']
        print("Case", i, ":", requirement)
        test_inputs = mus_accuracy_evaluator.generate_tests(requirement)
        generated_programs = []
        for n in range(N):
            generated_programs.append(mus_accuracy_evaluator.generate_programs(requirement))
            print(generated_programs[n])

        # Check for clusters
        print("Differential testing...")
        clusters = differential_tester(generated_programs, test_inputs)
        if len(clusters) > 1:
            print("Case", i, ": *********Discrepancy found!*********")
            cluster1, cluster2 = random.sample(clusters, k=2)
            for num in range(len(test_inputs)):
                if cluster1.outputs[num] != cluster2.outputs[num]:
                    res = model_verifier(requirement,
                                         [random.choice(cluster1.programs_str), random.choice(cluster2.programs_str)],
                                         test_inputs[num],
                                         [cluster1.outputs[num], cluster2.outputs[num]], model=verifier_name,
                                         api_key=verifier_api_key)
                    if not res:
                        print("*********Incorrect generation found!*********")
                        problem = {'requirement': requirement, 'test_input': test_inputs[num],
                                   "program1": cluster1.programs_str, "program2": cluster2.programs_str,
                                   'output1': cluster1.outputs[num], 'output2': cluster2.outputs[num]}
                        incorrect_generation.append(problem)
                        incorrect_generation_file.write(problem)
                        break
            else:
                print("*********Ambiguity found!*********")
                problem = {'requirement': requirement, 'test_input': test_inputs,
                           'outputs': [cluster.outputs for cluster in clusters],
                           'programs': [cluster.programs_str for cluster in clusters]}
                ambiguity.append(problem)
                ambiguity_file.write(problem)
        else:
            print("Case", i, ": No discrepancy found.")
print("Ambiguity number:", len(ambiguity))
print("Ambiguity percentage:", len(ambiguity) / 100)
print("Incorrect generation number:", len(incorrect_generation))
print("Incorrect generation percentage:", len(incorrect_generation) / 100)
