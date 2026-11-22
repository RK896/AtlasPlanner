import pytest

from src.tools.services.calculator import evaluate_expression


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("100 * 7 + 50", 750),
        ("(120 + 80) / 2", 100),
        ("2 ** 10", 1024),
        ("-5 + 3", -2),
        ("10 % 3", 1),
        ("1_000 * 1.5", 1500),
    ],
)
def test_evaluates_basic_arithmetic(expression, expected):
    assert evaluate_expression(expression) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('ls')",
        "().__class__.__base__.__subclasses__()",
        "open('/etc/passwd')",
        "x + 1",
        "[1, 2, 3]",
        "'a' * 3",
    ],
)
def test_rejects_anything_that_is_not_plain_math(expression):
    with pytest.raises(ValueError):
        evaluate_expression(expression)


def test_rejects_huge_exponents():
    with pytest.raises(ValueError, match="too large"):
        evaluate_expression("9 ** 999999")


def test_reports_division_by_zero_as_value_error():
    with pytest.raises(ValueError, match="zero"):
        evaluate_expression("1 / 0")


def test_rejects_syntax_errors():
    with pytest.raises(ValueError):
        evaluate_expression("2 +* 3")
