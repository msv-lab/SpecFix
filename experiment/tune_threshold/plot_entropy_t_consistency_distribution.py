import jsonlines
import numpy as np
import matplotlib.pyplot as plt
from specfix.cluster import Clusters
from specfix.utils import wilson_lower


def process_reader(reader):
    entropy = []
    t_consistency = []
    for problem in reader:
        clusters = Clusters()
        clusters.deserialize(problem["clusters"])
        entropy.append(clusters.entropy)
        weighted_tc = sum(
            cluster.test_consistency * cluster.probability
            for cluster in clusters.cluster_list
        )
        # weighted_tc = sum(
        #     [wilson_lower(cluster.test_consistency, len(clusters.input_output_examples)) * cluster.probability for cluster
        #      in clusters.cluster_list])
        t_consistency.append(weighted_tc)
    return entropy, t_consistency


def read_data(file_paths):
    data = {}
    for file_path in file_paths:
        dataset_name = file_path.split('/')[-1].split('.')[0]  # Extract dataset name from the file path
        with jsonlines.open(file_path) as reader:
            entropy, tc = process_reader(reader)
            data[dataset_name] = {'entropy': entropy, 'test_consistency': tc}
    return data


model = "deepseek-v3"
# List of dataset files
files = [
    f"ambiguity_detection/{model}/humaneval.jsonl",
    f"ambiguity_detection/{model}/humaneval_woe.jsonl",
    f"ambiguity_detection/{model}/mbpp.jsonl",
    f"ambiguity_detection/{model}/mbpp_woe.jsonl",
    f"ambiguity_detection/{model}/taco.jsonl",
    f"ambiguity_detection/{model}/taco_woe.jsonl"
]

# Read and process data
data = read_data(files)

# Create visualization with individual subplots for each dataset
fig, axs = plt.subplots(len(data), 4, figsize=(16, 4 * len(data)))

# Loop over each dataset and generate the respective plots
for i, (dataset_name, dataset) in enumerate(data.items()):
    entropy = dataset['entropy']
    test_consistency = dataset['test_consistency']

    # Calculate global entropy range for the current dataset
    entropy_min, entropy_max = min(entropy), max(entropy)
    entropy_bins = np.linspace(entropy_min, entropy_max, 11)
    tc_bins = np.linspace(0, 1, 11)

    # Entropy distribution
    axs[i, 0].hist(entropy, bins=entropy_bins, alpha=0.7, label=dataset_name)
    axs[i, 0].set(xlim=(entropy_min, entropy_max), title=f'{dataset_name} - Entropy Distribution')
    axs[i, 0].legend()

    # Test consistency distribution
    axs[i, 1].hist(test_consistency, bins=tc_bins, alpha=0.7, label=dataset_name)
    axs[i, 1].set(xlim=(0, 1), title=f'{dataset_name} - Test Consistency Distribution')
    axs[i, 1].legend()

    # Entropy boxplot
    axs[i, 2].boxplot(entropy, vert=False)
    axs[i, 2].set(xlim=(entropy_min, entropy_max), title=f'{dataset_name} - Entropy Boxplot')

    # Test consistency boxplot
    axs[i, 3].boxplot(test_consistency, vert=False)
    axs[i, 3].set(xlim=(0, 1), title=f'{dataset_name} - Test Consistency Boxplot')

plt.tight_layout()
plt.show()
