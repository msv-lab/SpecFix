import json

original = "mbpp.jsonl"
clarify_gpt_dataset = "/Users/robbiemorris/Documents/repos/SpecFix/dataset/clarifygpt_mbpp/mbpp_tests_final.jsonl"
output_file = "clarify_mbpp.jsonl"

def create_clarify_dataset(original, clarify_gpt_dataset, output_file):
    with open(original, 'r') as infile1, open(clarify_gpt_dataset, 'r') as infile2, open(output_file, 'w') as outfile:
        data2_dict = {}
        
        for line2 in infile2:
            try:
                data2 = json.loads(line2)
                if "task_id" in data2:
                    data2_dict[data2["task_id"].replace("MbppEval/", "Mbpp/")] = data2
            except Exception as e:
                print(f"Error processing line in file2: {line2.strip()}\n{e}")

        for line1 in infile1:
            try:
                data1 = json.loads(line1)
                combined_data = {}

                task_id = data1.get("task_id")
                if task_id:
                    combined_data["task_id"] = task_id

                if task_id and task_id in data2_dict:
                    matching_data2 = data2_dict[task_id]
                    if "prompt" in matching_data2:
                        combined_data["prompt"] = matching_data2["prompt"]
                    if "tests" in matching_data2:
                        combined_data["tests"] = matching_data2["tests"]

                for key, value in data1.items():
                    if key != "task_id":
                        combined_data[key] = value

                # Write combined data to output file
                outfile.write(json.dumps(combined_data) + '\n')
            except Exception as e:
                print(f"Error processing line in file1: {line1.strip()}\n{e}")
                
                
def create_pilot_dataset(input_file, output_file, num_lines=50):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for i, line in enumerate(infile):
            if i >= num_lines:
                break
            try:
                json_data = json.loads(line)
                outfile.write(json.dumps(json_data) + '\n')
            except Exception as e:
                print(f"Error processing line {i + 1}: {line.strip()}\n{e}")
                
                
create_pilot_dataset("clarify_mbpp.jsonl", "clarify_mbpp_pilot.jsonl")