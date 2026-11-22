"""Safe arithmetic evaluator for budget math.

Parses the expression into an AST and only walks numeric literals and
arithmetic operators, so nothing like `__import__` or attribute access can
ever run (unlike `eval`, even with builtins removed).
"""
import ast
import operator

MAX_EXPONENT = 100
MAX_EXPRESSION_LENGTH = 200

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_expression(expression: str) -> float | int:
    """Evaluate a plain arithmetic expression like "120 * 5 + 300".

    Raises:
        ValueError: if the expression is not plain arithmetic or cannot be computed.
    """
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("Expression is too long")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ValueError(f"Invalid expression: {expression!r}") from error
    return _evaluate_node(tree.body)


def _evaluate_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        return _apply_binary(node)
    raise ValueError(f"Unsupported syntax: {ast.dump(node)[:60]}")


def _apply_binary(node: ast.BinOp) -> float | int:
    left = _evaluate_node(node.left)
    right = _evaluate_node(node.right)
    if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
        raise ValueError("Exponent is too large")
    try:
        return _BINARY_OPERATORS[type(node.op)](left, right)
    except ZeroDivisionError as error:
        raise ValueError("Division by zero") from error
