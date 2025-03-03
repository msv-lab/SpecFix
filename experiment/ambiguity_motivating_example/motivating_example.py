

# potential ones:



import argparse
import random
import concurrent.futures
import jsonlines
import configparser
import re
from scipy.stats import pointbiserialr
from specfix.differential import differential_tester, calculate_accuracy_ground_truth_testing
from specfix.evaluator import SpecFixAccuracyEvaluator
from specfix.utils import construct_requirement


def parse_problem(problem):    
    return problem['requirement'], problem['canonical_solution'], problem['entry_point']


def generate_and_test(specfix_evaluator, requirement, test_inputs, entry_point, canonical_solution, n_programs, n_shot, initial=False):
    generated_programs = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        evaluator = specfix_evaluator.generate_initial_programs_clarify_gpt if initial else specfix_evaluator.generate_programs_clarify_gpt 
        futures = [executor.submit(evaluator, requirement, n_shot)
                   for _ in range(n_programs)]
        for future in concurrent.futures.as_completed(futures):
            prog = future.result()
            generated_programs.append(prog)

    print("Differential Testing")
    clusters = differential_tester(generated_programs, test_inputs, entry_point)
    calculate_accuracy_ground_truth_testing(canonical_solution, clusters, test_inputs, entry_point)
    return clusters


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--program_number", dest="number", type=int, default=50)
    parser.add_argument("-ns", "--nshot", dest="n_shot", default="zero_shot",
                        help="Number of shots (demonstrations) given to LLM before prompt: one_shot, two_shot, three_shot")

    options = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../../.config')

    model_name = "qwen2.5-coder-32b-instruct"
    api_key = config['API_KEY']['qwen_key']
    
    specfix_accuracy_evaluator = SpecFixAccuracyEvaluator(
        api_key=api_key,
        differential_tester=differential_tester,
        model=model_name,
        temperature=0,
        top_p=0.95
    )
    # ONLY TESTED FOR CLARIFY_MBPP
    n_programs = options.number
    n_shot = options.n_shot
    
    # always 2 clusters, but the program is clearly unambiguous
    
    # Accuracy: 0.50
    # Accuracy: 1.00
    # Number of clusters: 2
    # Clusters entropy: 0.6899437584583995
    
    problem = {"task_id": "Mbpp/7", "gt": "U", "requirement": "\"\"\"\nWrite a function to find all words which are at least 4 characters long in a string.\nassert set(find_char_long('Please move back to stream')) == set(['Please', 'move', 'back', 'stream'])\n\"\"\"\n", "entry_point": "find_char_long", "canonical_solution": "\nimport re\ndef find_char_long(text):\n  return (re.findall(r\"\\b\\w{4,}\\b\", text))\n", "base_input": [["Please move back to stream"], ["Jing Eco and Tech"], ["Jhingai wulu road Zone 3"]], "atol": 0, "plus_input": [[""], ["This is a very long string with no words that are at least 4 characters long."], ["words"], ["with"], ["4"], ["ve"], ["This is a very long string with no arewords that are along.t least 4 charatacters long.is"], ["arewords"], ["This is a very long string with no words that are at llongeast 4 characters long."], ["arrewords"], ["This is a very long strigng with no words that are at least 4 characters long."], ["least"], ["arerwordsThis"], ["stralong.t"], ["stralonwith.t"], ["vate"], ["Thicharatactercss"], ["wosrds"], ["vwosrds"], ["llongeast"], ["along.t"], ["vcharacterse"], ["This is a very long string with no arords that are along.t least 4 charatacters long.is"], ["Thicharatactercsvcharacterse"], ["ThicharatacterThis is a very long strigng with no words that are at least 4 characters long.csvcharacterse"], ["ThicharatacterT4his is a very long strigng with no words that are at least 4 characters long.csvcharacterse"], ["arords"], ["This is a very long string with no arewords that are along.t least 4 charatacters lonThis vwosrdsis a very long string with no words that are at least 4 characters long.g.is"], ["long.with"], ["Thicharattactercss"], ["This is a very long string with no alrords that are along.t least 4 charatacters long.is"], ["Thicharataercss"], ["arewds"], ["This is a very long string with no arords that are along.t least 4 charatacters long.isarords"], ["thatvcharacterse"], ["is"], ["tat"], ["stralong..t"], ["s"], ["string"], ["long.g.is"], ["This is a very long gstrigng with no words that are at least 4 characters long."], ["This is a very long string with no words that are at llongeast 4 charactThis is a very long string with no arewords that are along.t least 4 charatacters lonThis vwosrdsis a very long string with no words that are at least 4 characters long.g.iss long."], ["vwords"], ["that"], ["characters"], ["woords"], ["vworrds"], ["ThicharatacterThis is a very long strigng  least 4 characters long.csvcharacterse"], ["srtring"], ["This is a very long sarrewordstring with no words that are at llongeast 4 characters long."], ["long.alrordsg.is"], ["wossrds"], ["This is a very long strigng with no words that are at least 4 characters longcharactThis."], ["arerwordsThis is a voery long gstrigng with no words that are at least 4 characters long.This"], ["vwdorrdwossrdss"], ["This is a very long string with no words that are at llongeast Thicharatactercssters long."], ["longlong.This.gwith"], ["vworrrds"], ["charactThis"], ["Tchicharatactercsvcharacterse"], ["stralon"], ["alrords"], ["tast"], ["44"], ["avworrds"], ["srtring44"], ["leaet"], ["ThicharatacterThis"], ["ThicharacterscharattractercssarerwordsThis"], ["vcherse"], ["alrordlonThiss"], ["This is a very long string with no words that are at llongeast Thcharactersicharatactercssters long."], ["ttat"], ["witth"], ["along.longcharactThis.t"], ["a"], ["at"], ["alrordlonThisllongeasts"], ["tlong.This"], ["ThicharatacterT4his is a very long strigng with no words that arevery at least 4 charactiers long.csvcharacterse"], ["srtrinrg"], ["tlong.TgstrignThcharactersicharatactercsstersghis"], ["wwith"], ["stringtast"], ["wilong.alrordsg.is"], ["long.This"], ["osrds"], ["stringtaststralong.t"], ["srtnoring"], ["vee"], ["ThicharatacterThis is a very long strigng with no words that are at least t4 characters long.csvcharacterse"], ["averyrewords"], ["thavworrdsat"], ["This is a very long string with no words that are at lllongeastcharacters long."], ["stralong..ts"], ["thatvcharaccharactiersterthavworrdsatse"], ["loleaetg"], ["wwitThish"], ["aa"], ["atare"], ["avaeryrewords"]], "contract": "\n  assert isinstance(text, str), \"invalid inputs\" # $_CONTRACT_$\n", "assertion": "\nassert set(find_char_long('Please move back to stream')) == set(['Please', 'move', 'back', 'stream'])\nassert set(find_char_long('Jing Eco and Tech')) == set(['Jing', 'Tech'])\nassert set(find_char_long('Jhingai wulu road Zone 3')) == set(['Jhingai', 'wulu', 'road', 'Zone'])\n"} 
    
    # problem = {"task_id": "Mbpp/4", "gt": "U", "requirement": "\"\"\"\nWrite a function to find the n largest integers from a given list of numbers, returned in descending order.\nassert heap_queue_largest( [25, 35, 22, 85, 14, 65, 75, 22, 58],3)==[85, 75, 65]\n\"\"\"\n", "entry_point": "heap_queue_largest", "canonical_solution": "\nimport heapq as hq\ndef heap_queue_largest(nums: list,n: int) -> list:\n  largest_nums = hq.nlargest(n, nums)\n  return largest_nums\n", "base_input": [[[25, 35, 22, 85, 14, 65, 75, 22, 58], 3], [[25, 35, 22, 85, 14, 65, 75, 22, 58], 2], [[25, 35, 22, 85, 14, 65, 75, 22, 58], 5]], "atol": 0, "plus_input": [[[9, 8, 7, 6, 5, 4, 3, 2, 1], 3], [[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], 5], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25], 7], [[10, 20, 30, 40, 50, 60, 70, 80, 90, 100], 3], [[1000, 900, 800, 700, 600, 500, 400, 300, 200, 100], 4], [[-10, 50, 0, -20, 30, -40, 60, -70, 80, -90, 100], 6], [[-10, 50, 0, -20, 30, -40, 60, -70, 80, -90, 100, -70], 3], [[9, 8, 7, 6, 5, 4, 3, 2, 1], 2], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 25], 7], [[1000, 900, 800, 700, 600, 500, 400, 300, 199, 100], 4], [[1000, 900, 800, 700, 600, 500, 400, 300, 200, 100], 9], [[1000, 900, 800, 700, 600, 500, 400, 300, 199, 100], 5], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25], 7], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25], 7], [[10, 20, 30, 40, 50, 70, 80, 100], 3], [[9, 8, 7, 6, 5, 4, 3, 2, 1, 6], 9], [[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], 4], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25, 11], 7], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25, 11, 11], 7], [[9, 8, 7, 6, 5, 4, 3, 2, 1, 7], 4], [[1000, 900, 800, 700, 600, 500, 400, 300, 200, 100, 800], 9], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25], 8], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25], 6], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25, 11, 11], 8], [[1000, 900, 700, 600, 500, 400, 300, 200, 100, 800], 9], [[1, 3, 5, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25], 8], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25], 8], [[1, 3, 5, 6, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25], 6], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25, 11, 24, 11], 7], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 1, 23, 25, 25, 11, 11], 8], [[1, 3, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25, 11, 24, 11], 7], [[1000, 900, 800, 700, 600, 500, 400, 300, 4, 100], 5], [[70, 900, 800, 700, 600, 500, 400, 300, 200, 100], 4], [[1000, 900, 800, 700, 600, 21, 500, 400, 300, 200, 100], 9], [[8, 7, 6, 5, 4, 2, 1], 2], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25, 40], 8], [[100, 200, 300, 400, 500, 600, 4, 700, 800, 900, 1000], 5], [[1, 3, 5, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25, 40], 8], [[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], 1], [[1000, 900, 800, 700, 600, 500, 400, 300, 199, 701, 100], 4], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25], 6], [[900, 700, 600, 500, 500, 400, 300, 200, 100, 800, 400], 9], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25], 2], [[1000, 900, 800, 700, 600, 500, 400, 300, 199, 701, 100], 5], [[10, 20, 40, 30, 40, 50, 60, 70, 80, 90, 100], 3], [[1000, 900, 800, 700, 600, 21, 500, 400, 300, 199, 100], 9], [[900, 700, 600, 500, 500, 400, 300, 200, 100, 800, 400], 10], [[8, 7, 6, 5, 5, 4, 2, 1], 2], [[1000, 800, 700, 600, 500, 400, 300, 4, 100], 5], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 24], 6], [[-10, 900, 800, 700, 600, 500, 400, 300, 200, 100, 800], 9], [[9, 8, 7, 6, 4, 3, 2, 1], 4], [[9, 8, 7, 6, 5, 4, 3, 2, 1, 7], 2], [[1, 3, 5, 7, 9, 11, 13, 14, 15, 17, 19, 21, 23, 25], 8], [[1000, 900, 800, 700, 600, 500, 400, 300, 199, 701, 100, 100], 5], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 40, 24, 25], 7], [[1, 3, 5, 7, 9, 11, 13, 17, 19, 21, 23, 25, 25], 7], [[1000, 900, 800, 700, 600, 21, 500, 400, 300, 200, 100], 4], [[1000, 900, 800, 700, 600, 500, 400, 300, 199, 701], 4], [[-10, 900, 800, 700, 600, 500, 400, 300, 200, 100, 800], 10], [[10, 21, 30, 40, 50, 70, 80, 100], 3], [[1, 3, 5, 14, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25, 40], 8], [[1000, 900, 800, 700, 600, 500, 400, 300, 199, 701, 701], 4], [[1, 3, 5, 25, 7, 9, 11, 13, 15, 16, 19, 21, 23, 25], 7], [[1, 3, 5, 14, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25, 40], 2], [[1000, 900, 90, 800, 700, 600, 500, 400, 300, 199, 701, 99], 4], [[9, 8, 7, 6, 5, 4, 3, 2, 1, 6], 8], [[101, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], 5], [[100, 200, 400, 500, 600, 800, 900, 1000], 5], [[1000, 900, 800, 700, 600, 21, 500, 400, 300, 200, 100], 5], [[1000, 900, 800, 700, 600, 21, 500, 400, 300, 199, 800, 100], 9], [[8, 7, 6, 5, 5, 4, 2, 0], 2], [[100, 200, 300, 400, 500, 599, 700, 800, 900, 1000], 1], [[1, 3, 5, 7, 21, 11, 13, 15, 17, 19, 21, 23, 25, 21], 7], [[1000, 8, 7, 6, 5, 4, 3, 2, 1, 6, 5], 9], [[101, 100, 200, 300, 3, 400, 500, 600, 700, 800, 900, 1000], 5], [[1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 40, 24, 25], 7], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 25, 7], 7], [[1000, 900, 800, 700, 900, 600, 500, 400, 300, 199, 100], 4], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 1, 23, 25, 25, 11, 11], 7], [[1000, 8, 7, 6, 5, 4, 3, 2, 1, 6], 9], [[101, 100, 200, 300, 3, 400, 500, 600, 700, 800, 40, 1000], 5], [[1, 23, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 1, 23, 25, 25, 11, 11], 8], [[1000, 900, 800, 700, 600, 15, 500, 400, 300, 4, 100, 400], 5], [[1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 40, 24, 25], 8], [[1, 3, 5, 7, 9, 11, 13, 17, 19, 21, 23, 25, 25], 8], [[1, 3, 5, 7, 9, 11, 13, 15, 18, 19, 21, 23, 25, 25, 11, 24, 11, 21], 7], [[8, 7, 6, 5, 4, 2, 1, 8], 2], [[1000, 900, 800, 400, 700, 600, 500, 400, 300, 199, 701, 100, 100], 5], [[1000, 900, 800, 700, 600, 500, 400, 1001, 300, 200, 100], 9], [[1000, 8, 7, 6, 5, 4, 3, 99, 2, 1, 6], 9], [[3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25], 9], [[-10, 900, 800, 700, 600, 500, 400, 300, 200, 100, 800], 3], [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25], 5], [[1, 3, 5, 9, 11, 13, 15, 17, 21, 23, 40, 25, 25], 8], [[1, 3, 5, 9, 900, 13, 15, 17, 19, 21, 19, 25, 25, 7], 7], [[1, 3, 5, 6, 14, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25, 40], 2], [[9, 8, 7, 6, 5, 4, 3, 2, 1, 4, 7], 4], [[3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 40, 24, 25], 8], [[1, 3, 5, 7, 9, 11, 13, 15, 13, 21, 1, 23, 25, 25, 11, 11], 8], [[100, 200, 400, 500, 800, 900, 1000], 5], [[1, 3, 5, 7, 9, 11, 22, 13, 15, 17, 19, 21, 23, 40, 25, 25], 8], [[3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 40, 25, 25], 8], [[3, 5, 8, 9, 11, 17, 19, 21, 23, 40, 24, 25], 7], [[100, 200, 300, 400, 30, 600, 700, 800, 900, 1000], 4], [[900, 700, 600, 500, 500, 400, 300, 200, 100, 800, 400, 900], 10]], "contract": "\n  assert isinstance(nums, list), \"invalid inputs\" # $_CONTRACT_$\n  assert isinstance(n, int), \"invalid inputs\" # $_CONTRACT_$\n  assert n > 0, \"invalid inputs\" # $_CONTRACT_$\n  assert all(isinstance(i, int) for i in nums), \"invalid inputs\" # $_CONTRACT_$\n  assert len(nums) > n, \"invalid inputs\" # $_CONTRACT_$\n", "assertion": "\nassert heap_queue_largest( [25, 35, 22, 85, 14, 65, 75, 22, 58],3)==[85, 75, 65]\nassert heap_queue_largest( [25, 35, 22, 85, 14, 65, 75, 22, 58],2)==[85, 75]\nassert heap_queue_largest( [25, 35, 22, 85, 14, 65, 75, 22, 58],5)==[85, 75, 65, 58, 35]\n"}
    # this one only works sometimes: 1 or 2 clusters, but the ambiguity is always quite low
    
    requirement, canonical_solution, entry_point = parse_problem(problem)

    print("Requirement: ", requirement)

    test_inputs = specfix_accuracy_evaluator.generate_tests_clarify_gpt(requirement, n_shot)
    mutated_test_inputs = specfix_accuracy_evaluator.type_aware_mutation(test_inputs)
    print(f"Test inputs: {test_inputs}")
    print(f"Mutated test inputs: {mutated_test_inputs}")
    clusters = generate_and_test(
        specfix_evaluator=specfix_accuracy_evaluator,
        requirement=requirement,
        test_inputs=mutated_test_inputs,
        entry_point=entry_point,
        canonical_solution=canonical_solution,
        n_programs=n_programs,
        n_shot=n_shot,
        initial=True
    )
    
    print(f"Number of clusters: {len(clusters.get_clusters())}")
    print(f"Clusters entropy: {clusters.entropy}")


if __name__ == "__main__":
    main()
