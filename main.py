import openai
import random
import os
from dotenv import load_dotenv
from differential_tester import differential_tester_manual

class MUS:
    def __init__(self, openai_api_key, differential_tester, print_func, model="gpt-4"):

        self.openai_api_key = openai_api_key
        self.differential_tester = differential_tester
        self.print_func = print_func
        self.model = model
        openai.api_key = self.openai_api_key

    def generate_programs(self, requirements):
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant that generates Python code based on specifications."},
                    {"role": "user", "content": f"Generate Python programs based on the following requirements:\n{requirements}. Ensure that function signatures are correctly typed. Do not output any text besides the code and do not use any markdown formatting."}
                ],
                temperature=0.7,
                max_tokens=300
            )
            # Extract and return the generated response
            generated_program = response.choices[0].message.content
            return [generated_program.strip()]
        except openai.OpenAIError as e:
            print(f"Error interacting with OpenAI API: {e}")
            return []

    def refine_requirements(self, requirements, counterexample):
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant who reads code requirements and fixes them."},
                    {"role": "user", "content": f"Repair the ambiguous requirements: {requirements} given this counter example: {counterexample}. Do not provide commentary on the requirements, simply provide them to me like you are describing a problem. Do not answer or write the code described by the requirements."}
                ],
                temperature=0.7,
                max_tokens=300
            )
            # Extract and return the generated response
            generated_program = response.choices[0].message.content
            return [generated_program.strip()]
        except openai.OpenAIError as e:
            print(f"Error interacting with OpenAI API: {e}")
            return []

    def compute_mus(self, program, initial_requirements, max_iterations=10):
        
        requirements = initial_requirements
        for _ in range(max_iterations):
            # generate 
            generated_programs = self.generate_programs(requirements)
            equivalent = self.differential_tester(program, generated_programs)

            if equivalent:
                print("Requirements are unambiguous and sufficient.")
                return requirements
            else:
                # Identify a counterexample
                counterexample = random.choice(generated_programs)
                requirements = self.refine_requirements(requirements, counterexample)

        print("Max iterations reached. MUS computation stopped.")
        return requirements


# Example Usage
def mock_differential_tester(program, generated_programs):
    """Mock differential tester"""
    
    return all(p.strip() == program.strip() for p in generated_programs)

def mock_print_func(facts):
    """Mock print function."""
    return " and ".join(facts)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

mus_computer = MUS(
    openai_api_key=openai_api_key,
    differential_tester=differential_tester_manual,
    print_func=mock_print_func,
    model="gpt-4"
)

program = """
def add(a, b): 
    return a + b
"""
initial_requirements = "Write a Python function to add two numbers together."
mus = mus_computer.compute_mus(program, initial_requirements, 3)

print("Final MUS:", mus)
