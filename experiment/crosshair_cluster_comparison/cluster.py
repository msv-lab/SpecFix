#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "scikit-learn",
#   "jsonlines"
# ]
# ///

import ast
import tempfile
import os
import subprocess
import jsonlines
import json
import sys
import sklearn


MBPP_DATA = 'mbpp.jsonl'
MBPP_SE_CLUSTERS = 'mbpp_se_clusters.json'
MBPP_TEST_CLUSTERS = 'mbpp_test_clusters.json'

EXECUTION_TIMEOUT_SECONDS = 30

def get_first_function_name(code: str) -> str:
    tree = ast.parse(code)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node.name
    return None

def are_equivalent(p1, p2):
    with tempfile.TemporaryDirectory() as tmpdirname:
        file1 = os.path.join(tmpdirname, 'f1.py')
        file2 = os.path.join(tmpdirname, 'f2.py')
        with open(file1, 'w') as f:
            f.write(p1)
        with open(file2, 'w') as f:
            f.write(p2)
        func1_name = get_first_function_name(p1)
        func2_name = get_first_function_name(p2)
        cmd = [
            'uvx','--from','crosshair-tool','crosshair','diffbehavior','--exception_equivalence','ALL',
            f"f1.{func1_name}",
            f"f2.{func2_name}"
        ]
        try:
            proc = subprocess.run(cmd,
                                  capture_output=True,
                                  text=True,
                                  cwd=str(tmpdirname),
                                  timeout=EXECUTION_TIMEOUT_SECONDS)
            print(f"{proc.returncode}, {proc.stdout}, {proc.stderr}")
            if proc.returncode == 0:
                return True
            else:
                return False
        except subprocess.TimeoutExpired:
            return True  # failed to find difference in 30 seconds, so assume equivalent


def partition(programs):
    string_to_indices = {}
    for idx, prog in enumerate(programs):
        string_to_indices.setdefault(prog, []).append(idx)

    unique_programs = list(string_to_indices.keys())
    n_classes = 0
    rep_programs = []   # Representative program string for each class
    labels = [None] * len(programs)
    prog_to_class = {}  # Map program string to class index

    for prog in unique_programs:
        found_class = None
        for class_idx, rep in enumerate(rep_programs):
            if prog == rep:  # Identical strings, must be same class
                found_class = class_idx
                break
            if are_equivalent(prog, rep):
                found_class = class_idx
                break
        if found_class is None:
            # New equivalence class, use this prog as representative
            rep_programs.append(prog)
            found_class = n_classes
            n_classes += 1
        prog_to_class[prog] = found_class

    for prog, indices in string_to_indices.items():
        clabel = prog_to_class[prog]
        for idx in indices:
            labels[idx] = clabel

    return labels


def compute_se_clusters():
    if os.path.exists(MBPP_SE_CLUSTERS):
        with open(MBPP_SE_CLUSTERS, 'r', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = {}

    with jsonlines.open(MBPP_DATA) as reader:
        for entry in reader:
            print(f"PROGRESS: {len(results.keys())}/{378}")
            task_id = str(entry['task_id'])
            if task_id in results:
                continue  # Skip if results already exist for this id

            programs = entry['programs']
            ids = partition(programs)
            results[task_id] = ids

            with open(MBPP_SE_CLUSTERS, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)


def extract_test_clusters():
    def get_cluster_indices(programs, clusters):
        prog2cluster = {}
        for idx, cluster in enumerate(clusters):
            for prog in cluster['programs_str']:
                prog2cluster[prog] = idx
                
        return [prog2cluster[prog] for prog in programs]

    output = {}

    with open(MBPP_DATA, 'r') as fin:
        for line in fin:
            item = json.loads(line)
            programs = item['programs']
            clusters = item['clusters']
            indices = get_cluster_indices(programs, clusters)
            output[item['task_id']] = indices

    with open(MBPP_TEST_CLUSTERS, 'w') as fout:
        json.dump(output, fout, indent=2)


def avg_rand_score():
    with open(MBPP_TEST_CLUSTERS, 'r') as ft:
        test_labels = json.load(ft) 
        with open(MBPP_SE_CLUSTERS, 'r') as fs:
            se_labels = json.load(fs)

            scores = []
   
            for t in test_labels.keys():
                ari = sklearn.metrics.rand_score(test_labels[t], se_labels[t])
                scores.append(ari)

            return sum(scores) / len(scores)


if __name__ == "__main__":
    match sys.argv[1]:
        case "se":
            compute_se_clusters()
        case "test":
            extract_test_clusters()
        case "diff":
            print(avg_rand_score())
