from specfix.utils import count_passk, count_passk_ambiguous

count_passk("vanilla_repair", "deepseek-v3", "taco_woe")
count_passk_ambiguous("vanilla_repair", "deepseek-v3", "taco_woe")
# count_passk_ambiguous("vanilla_repair", "qwen2.5-coder-32b-instruct", "mbpp")
