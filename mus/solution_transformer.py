import ast


def transform_code(original_code):
    """
    Transforms the original Python code by:
    1. Removing the "if __name__ == '__main__':" block if it exists.
    2. Converting methods inside classes to standalone functions.
    3. Removing all decorators (e.g., @staticmethod) throughout the code.
    4. Keeping the code unchanged if it's already standalone (no classes).

    Args:
        original_code (str): The original Python code as a string.

    Returns:
        str: The transformed Python code.
    """

    class ClassMethodExtractor(ast.NodeTransformer):
        def __init__(self):
            self.standalone_functions = []

        def visit_ClassDef(self, node):
            """
            Visits each class definition, extracts its methods,
            removes 'self' from their arguments, and collects them
            as standalone functions. Removes the class definition from the AST.
            """
            # Extract all function definitions from the class
            new_body = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    # Remove 'self' from arguments if present
                    if item.args.args and item.args.args[0].arg == 'self':
                        item.args.args = item.args.args[1:]
                    # Collect the function for later addition to the module
                    self.standalone_functions.append(item)
                else:
                    new_body.append(item)

            # Return None to remove the entire class definition from the AST
            return None

    class MainBlockRemover(ast.NodeTransformer):
        def visit_Module(self, node):
            """
            Visits the module body to remove the main block (if __name__ == '__main__':).
            """
            new_body = []
            for stmt in node.body:
                # Check if the statement is the main block
                if isinstance(stmt, ast.If):
                    test = stmt.test
                    if (
                            isinstance(test, ast.Compare)
                            and isinstance(test.left, ast.Name)
                            and test.left.id == '__name__'
                            and len(test.ops) == 1
                            and isinstance(test.ops[0], ast.Eq)
                            and len(test.comparators) == 1
                            and isinstance(test.comparators[0], ast.Constant)
                            and test.comparators[0].value == '__main__'
                    ):
                        # Skip this if block to remove it
                        continue
                # Otherwise, keep the statement
                new_body.append(stmt)
            node.body = new_body
            return node

    class DecoratorRemover(ast.NodeTransformer):
        """
        Removes all decorators from functions, async functions, and classes.
        """

        def visit_FunctionDef(self, node):
            node.decorator_list = []
            self.generic_visit(node)
            return node

        def visit_AsyncFunctionDef(self, node):
            node.decorator_list = []
            self.generic_visit(node)
            return node

        def visit_ClassDef(self, node):
            node.decorator_list = []
            self.generic_visit(node)
            return node

    # Parse the original code into an AST
    tree = ast.parse(original_code)

    # First, remove all decorators in the entire code (including those on classes and methods)
    tree = DecoratorRemover().visit(tree)

    # Extract class methods and remove class definitions
    extractor = ClassMethodExtractor()
    tree = extractor.visit(tree)

    # Remove the main block
    remover = MainBlockRemover()
    tree = remover.visit(tree)

    # Append the extracted standalone functions to the module body
    tree.body.extend(extractor.standalone_functions)

    # Fix any missing locations in the AST
    ast.fix_missing_locations(tree)

    # Generate the transformed code from the modified AST
    transformed_code = ast.unparse(tree)

    return transformed_code


def transform_starter_code(original_starter_code):
    lines = original_starter_code.split("\n")
    for line in lines:
        if "def " in line:
            if "(self, " in line or "(self," in line:
                line = line.replace("self, ", "").replace("self,", "")
            return line.strip() + "\n"
