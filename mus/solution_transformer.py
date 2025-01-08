import ast


def transform_code(original_code):
    """
    Transforms the original Python code by:
    1. Removing the "if __name__ == '__main__':" block if it exists.
    2. Converting methods inside classes to standalone functions.
    3. Keeping the code unchanged if it's already standalone (no classes).

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
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    func = item
                    # Remove 'self' from arguments if present
                    if func.args.args and func.args.args[0].arg == 'self':
                        func.args.args = func.args.args[1:]
                    # Optionally, you can rename the function to avoid name clashes
                    # For simplicity, we'll keep the original function names
                    self.standalone_functions.append(func)
            # Remove the class definition by returning None
            return None

    class MainBlockRemover(ast.NodeTransformer):
        def visit_Module(self, node):
            """
            Visits the module body to remove the main block.
            """
            new_body = []
            for stmt in node.body:
                # Check if the statement is the main block
                if isinstance(stmt, ast.If):
                    test = stmt.test
                    if (isinstance(test, ast.Compare) and
                            isinstance(test.left, ast.Name) and test.left.id == '__name__' and
                            len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq) and
                            len(test.comparators) == 1 and isinstance(test.comparators[0], ast.Constant) and
                            test.comparators[0].value == '__main__'):
                        # Skip this if block to remove it
                        continue
                # Otherwise, keep the statement
                new_body.append(stmt)
            node.body = new_body
            return node

    # Parse the original code into an AST
    tree = ast.parse(original_code)

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

    transformed_code = ast.unparse(tree)

    return transformed_code
