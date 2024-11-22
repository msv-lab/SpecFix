import types
import inspect
import random

def string_to_function(func_string):
    try:
        func_string = func_string.strip().removeprefix("```python").removeprefix("```").strip("`").strip()

        
        local_scope = {}
        exec(func_string, {}, local_scope)
        func_name = next(iter(local_scope))  # Assuming there's only one function in the string
        return local_scope[func_name]
    except Exception as e:
        print(f"Error creating function from string: {e}")
        return None
    
def generate_random_inputs(param_types, num_tests=10):
    inputs = []
    for _ in range(num_tests):
        test_case = []
        for param_type in param_types:
            if param_type == int:
                test_case.append(random.randint(-100, 100))  
            elif param_type == float:
                test_case.append(random.uniform(-100.0, 100.0))  
            elif param_type == str:
                test_case.append(''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=5)))
        inputs.append(tuple(test_case))
    return inputs

def differential_tester_manual(reference_func, generated_programs, num_tests=10):

    reference_func = string_to_function(reference_func)
    for program_str in generated_programs:
        candidate_func = string_to_function(program_str)

        if candidate_func is None:
            print("Invalid function generated. Skipping.")
            return False

        try:
            sig = inspect.signature(reference_func)
            param_types = [param.annotation for param in sig.parameters.values()]
        except Exception as e:
            print(f"Error extracting signature: {e}")
            return False
            
         # Generate random inputs
        try:
            random_inputs = generate_random_inputs(param_types, num_tests)
        except Exception as e:
            print(f"Error generating random inputs: {e}")
            return False

        # Perform a bunch of randomized tests
        for inputs in random_inputs:
            try:
                ref_output = reference_func(*inputs)
                cand_output = candidate_func(*inputs)
                if ref_output != cand_output:
                    print(f"Mismatch found for inputs {inputs}: {ref_output} (reference) != {cand_output} (candidate)")
                    return False
            except Exception as e:
                print(f"Error during function execution with inputs {inputs}: {e}")
                return False

    return True


# Example Usage
if __name__ == "__main__":
    # Original function
    reference_program = """
def add(a: int, b: int) -> int:
    return a + b
"""

    # Generated programs
    generated_programs = [
        """
def add(a: float, b: float) -> int:
    return a + b
        """,
        """
def add(a: int, b: int) -> int:
    return a - b
        """
    ]

    # Test equivalence
    result = differential_tester_manual(reference_program, generated_programs)
    print("Are all generated programs equivalent to the reference?", result)
