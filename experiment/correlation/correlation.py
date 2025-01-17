import jsonlines
from scipy.stats import pointbiserialr


def compute_and_write_correlation(output_file, pilot_file, reader_file):
    with jsonlines.open(output_file, "w", flush=True) as writer, \
            jsonlines.open(pilot_file) as pilot, \
            jsonlines.open(reader_file) as reader:
        entropy_list = [obj["original_clusters"]["entropy"] for obj in reader]
        labels = [1 if problem['label'] == 'Yes' else 0 for problem in pilot]
        correlation, p_value = pointbiserialr(entropy_list, labels)
        result = {
            'entropy': entropy_list,
            'labels': labels,
            'correlation': correlation,
            'p_value': p_value
        }
        writer.write(result)


# Call the function for each dataset
compute_and_write_correlation(
    "humaneval_pilot_correlation.jsonl",
    "../ambiguity_classification/humaneval_pilot_classification.jsonl",
    "humaneval_70_vanilla_repair.jsonl"
)

compute_and_write_correlation(
    "humaneval_woe_pilot_correlation.jsonl",
    "../ambiguity_classification/humaneval_woe_pilot_classification.jsonl",
    "humaneval_70_woe_vanilla_repair.jsonl"
)

compute_and_write_correlation(
    "mbpp_pilot_correlation.jsonl",
    "../ambiguity_classification/mbpp_pilot_classification.jsonl",
    "mbpp_70_vanilla_repair.jsonl"
)

compute_and_write_correlation(
    "mbpp_woe_pilot_correlation.jsonl",
    "../ambiguity_classification/mbpp_woe_pilot_classification.jsonl",
    "mbpp_70_woe_vanilla_repair.jsonl"
)

compute_and_write_correlation(
    "taco_lite_pilot_correlation.jsonl",
    "../ambiguity_classification/taco_lite_pilot_classification.jsonl",
    "taco_lite_70_vanilla_repair.jsonl"
)

compute_and_write_correlation(
    "taco_lite_woe_pilot_correlation.jsonl",
    "../ambiguity_classification/taco_lite_woe_pilot_classification.jsonl",
    "taco_lite_70_woe_vanilla_repair.jsonl"
)
