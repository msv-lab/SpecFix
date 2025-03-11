import ast


def transform_code(original_code):
    """
    Transforms the original Python code by:
    1. Removing the "if __name__ == '__main__':" block if it exists.
    2. Converting methods inside classes to standalone functions, removing 'self' parameters and 'self.xxx' references.
    3. Removing all decorators (e.g., @staticmethod) throughout the code.
    4. Keeping the code unchanged if it's already standalone (no classes).

    Args:
        original_code (str): The original Python code as a string.

    Returns:
        str: The transformed Python code.
    """

    class SelfReferenceTransformer(ast.NodeTransformer):
        """
        Transforms all 'self.xxx' references into 'xxx' within the AST.
        """
        def visit_Attribute(self, node):
            if isinstance(node.value, ast.Name) and node.value.id == 'self':
                return ast.Name(id=node.attr, ctx=node.ctx)
            return node

    class ClassMethodExtractor(ast.NodeTransformer):
        def __init__(self):
            self.standalone_functions = []

        def visit_ClassDef(self, node):
            """
            Extracts methods, removes 'self' parameters and transforms 'self.xxx' references.
            Removes the class definition from the AST.
            """
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    # Remove 'self' from arguments
                    if item.args.args and item.args.args[0].arg == 'self':
                        item.args.args = item.args.args[1:]
                    # Transform 'self.xxx' to 'xxx' in the method body
                    transformer = SelfReferenceTransformer()
                    transformed_item = transformer.visit(item)
                    self.standalone_functions.append(transformed_item)
            return None  # Removes the class definition

    class MainBlockRemover(ast.NodeTransformer):
        def visit_Module(self, node):
            """
            Removes the main block (if __name__ == '__main__':) from the module.
            """
            new_body = []
            for stmt in node.body:
                if isinstance(stmt, ast.If):
                    test = stmt.test
                    if (isinstance(test, ast.Compare) and
                        isinstance(test.left, ast.Name) and
                        test.left.id == '__name__' and
                        len(test.ops) == 1 and
                        isinstance(test.ops[0], ast.Eq) and
                        len(test.comparators) == 1 and
                        isinstance(test.comparators[0], ast.Constant) and
                        test.comparators[0].value == '__main__'):
                        continue
                new_body.append(stmt)
            node.body = new_body
            return node

    class DecoratorRemover(ast.NodeTransformer):
        """
        Removes all decorators from functions, async functions, and classes.
        """
        def visit_FunctionDef(self, node):
            node.decorator_list = []
            return self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            node.decorator_list = []
            return self.generic_visit(node)

        def visit_ClassDef(self, node):
            node.decorator_list = []
            return self.generic_visit(node)

    # Parse and transform the AST
    tree = ast.parse(original_code)

    # Remove decorators first
    tree = DecoratorRemover().visit(tree)

    # Extract class methods and transform self references
    extractor = ClassMethodExtractor()
    tree = extractor.visit(tree)

    # Remove the main block
    tree = MainBlockRemover().visit(tree)

    # Append transformed methods to the module body
    tree.body.extend(extractor.standalone_functions)

    # Ensure the AST is valid
    ast.fix_missing_locations(tree)

    # Generate the transformed code
    return ast.unparse(tree)


def transform_starter_code(original_starter_code):
    lines = original_starter_code.split("\n")
    for line in lines:
        if "def " in line:
            if "(self, " in line or "(self," in line:
                line = line.replace("self, ", "").replace("self,", "")
            return line.strip() + "\n"


class RemoveAsserts(ast.NodeTransformer):

    def visit_Assert(self, node):
        # Returning None from a NodeTransformer method
        # means "remove this node".
        return None


class RemovePrintCalls(ast.NodeTransformer):

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Name) and func.id == "print":
                return None
        return node

class RemoveDocstrings(ast.NodeTransformer):

    def visit_FunctionDef(self, node):
        if node.body:
            first_stmt = node.body[0]
            if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, (ast.Str, ast.Constant)):
                node.body.pop(0)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if node.body:
            first_stmt = node.body[0]
            if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, (ast.Str, ast.Constant)):
                node.body.pop(0)
        return self.generic_visit(node)

def remove_comments_and_asserts(source_code: str) -> str:

    tree = ast.parse(source_code)

    transformers = [RemoveAsserts(), RemovePrintCalls(), RemoveDocstrings()]
    for transformer in transformers:
        tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)
