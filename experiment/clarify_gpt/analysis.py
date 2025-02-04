import json

def calculate_average_entropy_wo_repair(file_path):
    total_entropy = 0
    count = 0

    # Open the JSONL file
    with open(file_path, 'r') as file:
        for line in file:
            # Parse each line as a JSON object
            data = json.loads(line)
            # Check if 'entropy' is in the data
            
            if 'original_clusters' in data and 'entropy' in data['original_clusters']:
                total_entropy += data['original_clusters']['entropy']
                count += 1
    
    # Calculate the average entropy
    average_entropy = total_entropy / count if count > 0 else 0
    return average_entropy

def calculate_average_entropy(file_path):
    total_entropy = 0
    count = 0

    # Open the JSONL file
    with open(file_path, 'r') as file:
        for line in file:
            # Parse each line as a JSON object
            data = json.loads(line)
            # Check if 'entropy' is in the data
            if 'repaired_clusters' in data and 'entropy' in data['repaired_clusters']:
                total_entropy += data['repaired_clusters']['entropy']
                count += 1
            elif 'original_clusters' in data and 'entropy' in data['original_clusters']:
                total_entropy += data['original_clusters']['entropy']
                count += 1
    
    # Calculate the average entropy
    average_entropy = total_entropy / count if count > 0 else 0
    return average_entropy

def calculate_average_max_accuracy(file_path):
    total = 0
    count = 0

    # Open the JSONL file
    with open(file_path, 'r') as file:
        for line in file:
            # Parse each line as a JSON object
            data = json.loads(line)
            # Check if 'entropy' is in the data
            if 'repaired_clusters' in data and 'max_cluster_accuracy' in data['repaired_clusters']:
                total += data['repaired_clusters']['max_cluster_accuracy']
                count += 1
            elif 'original_clusters' in data and 'max_cluster_accuracy' in data['original_clusters']:
                total += data['original_clusters']['max_cluster_accuracy']
                count += 1
    
    # Calculate the average entropy
    average = total / count if count > 0 else 0
    return average

def calculate_pass_1(file_path):
    total_passing = 0
    count = 0

    # Open the JSONL file
    with open(file_path, 'r') as file:
        for line in file:
            # Parse each line as a JSON object
            data = json.loads(line)
            # Check if 'entropy' is in the data
            if 'repaired_clusters' in data:
                res = False
                max_dist = 0
                for cluster in data['repaired_clusters']['clusters']:
                    if cluster['distribution'] > max_dist:
                        max_dist = cluster['distribution']
                        res = cluster['is_align_req']
                
                total_passing += 1 if res else 0
                count += 1
                
            if 'original_clusters' in data:
                res = False
                max_dist = 0
                for cluster in data['original_clusters']['clusters']:
                    if cluster['distribution'] > max_dist:
                        max_dist = cluster['distribution']
                        res = cluster['is_align_req']
                
                total_passing += 1 if res else 0
                count += 1
                
    average = total_passing / count if count > 0 else 0
    return average


# Example usage
file_path = 'clarify_mbpp_pilot_50_clarify_gpt.jsonl'
average_entropy = calculate_average_entropy(file_path)
average_entropy_wo_repair = calculate_average_entropy_wo_repair(file_path)
pass_1 = calculate_pass_1(file_path)

print(f"Average Entropy without repair: {average_entropy_wo_repair}")
print(f"Average Entropy: {average_entropy}")
print(f"Pass@1", {pass_1})
