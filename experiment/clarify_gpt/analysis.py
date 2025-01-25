import json

def calculate_average_entropy(file_path):
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

# Example usage
file_path = 'clarify_mbpp_pilot_50_clarify_gpt.jsonl'
average_entropy = calculate_average_entropy(file_path)
print(f"Average Entropy: {average_entropy}")
