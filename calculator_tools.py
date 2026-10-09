"""Deterministic local calculator tools. No network access is used."""
from decimal import Decimal, InvalidOperation, getcontext
import ast
import operator
import statistics
from typing import List

import pint
from langchain.tools import tool

getcontext().prec = 50
ureg = pint.UnitRegistry()

# Safe arithmetic AST: no eval(), names, attributes, or arbitrary function calls.
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"Not a valid decimal number: {value!r}")

def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        # Use source text so decimal literals are not first rounded through binary float.
        return Decimal(ast.get_source_segment(_CURRENT_EXPRESSION, node))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Pow):
            if right != right.to_integral_value():
                raise ValueError("Exponent must be an integer for exact arithmetic.")
            if abs(right) > 10000:
                raise ValueError("Exponent magnitude is limited to 10000.")
        if isinstance(node.op, ast.Div) and right == 0:
            raise ValueError("Division by zero.")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Only numeric literals and +, -, *, /, %, **, and parentheses are allowed.")

_CURRENT_EXPRESSION = ""

@tool
def exact_calculation(expression: str) -> str:
    """Evaluate a numeric arithmetic expression exactly with decimal arithmetic. Supports +, -, *, /, %, ** and parentheses. Example: (17.5 / 100) * 8400."""
    global _CURRENT_EXPRESSION
    if len(expression) > 500:
        return "Error: expression is too long."
    _CURRENT_EXPRESSION = expression
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree)
        return f"Result: {result}; decimal representation (up to 50 significant digits)."
    except (SyntaxError, ValueError, ArithmeticError, InvalidOperation, OverflowError) as exc:
        return f"Calculation error: {exc}"
    finally:
        _CURRENT_EXPRESSION = ""

@tool
def convert_units(value: str, from_unit: str, to_unit: str) -> str:
    """Convert a quantity between compatible units. Example: value='5', from_unit='mile', to_unit='kilometer'. Uses Pint unit names."""
    try:
        quantity = ureg.Quantity(float(_decimal(value)), from_unit)
        converted = quantity.to(to_unit)
        return f"{value} {from_unit} = {converted.magnitude:.15g} {to_unit}"
    except Exception as exc:
        return f"Unit conversion error: {exc}. Use recognized Pint units and compatible dimensions."

@tool
def descriptive_statistics(values: List[float]) -> str:
    """Compute count, mean, median, population standard deviation, sample standard deviation (when possible), minimum, maximum, and range for a list of numeric values."""
    if not values:
        return "Statistics error: provide at least one number."
    try:
        xs = [float(x) for x in values]
        result = [
            f"count = {len(xs)}",
            f"mean = {statistics.mean(xs):.15g}",
            f"median = {statistics.median(xs):.15g}",
            f"population standard deviation = {statistics.pstdev(xs):.15g}",
            f"minimum = {min(xs):.15g}",
            f"maximum = {max(xs):.15g}",
            f"range = {max(xs) - min(xs):.15g}",
        ]
        if len(xs) >= 2:
            result.append(f"sample standard deviation = {statistics.stdev(xs):.15g}")
        return "; ".join(result)
    except (TypeError, ValueError, OverflowError) as exc:
        return f"Statistics error: {exc}"

@tool
def compound_interest(principal: str, annual_rate_percent: str, years: str, compounds_per_year: int = 1) -> str:
    """Calculate compound interest using A=P(1+r/n)^(nt). Inputs are decimal strings; annual_rate_percent is a percent (e.g. '5' for 5%)."""
    try:
        p, rate, t = _decimal(principal), _decimal(annual_rate_percent) / Decimal(100), _decimal(years)
        n = int(compounds_per_year)
        if p < 0 or t < 0 or n <= 0:
            return "Finance error: principal and years must be non-negative and compounds_per_year must be positive."
        # Decimal power is used; non-integral exponents may be rounded to current Decimal precision.
        amount = p * (Decimal(1) + rate / n) ** (Decimal(n) * t)
        interest = amount - p
        return f"Future value = {amount}; interest earned = {interest}; principal = {p}; annual rate = {rate * 100}%; years = {t}; compounds/year = {n}. Decimal precision: {getcontext().prec} significant digits."
    except (InvalidOperation, ValueError, ArithmeticError) as exc:
        return f"Finance error: {exc}"

@tool
def loan_payment(principal: str, annual_rate_percent: str, years: str, payments_per_year: int = 12) -> str:
    """Calculate fixed periodic loan payment for a fully amortizing loan. Inputs: principal, annual rate as percent, years, and payments per year (default monthly). Assumes a fixed nominal annual rate and end-of-period payments."""
    try:
        p, annual_rate, t = _decimal(principal), _decimal(annual_rate_percent) / Decimal(100), _decimal(years)
        n = int(payments_per_year)
        if p < 0 or t <= 0 or n <= 0:
            return "Finance error: principal must be non-negative; years and payments_per_year must be positive."
        periods = int(t * n)
        if periods <= 0:
            return "Finance error: loan term must include at least one payment."
        periodic_rate = annual_rate / n
        if periodic_rate == 0:
            payment = p / periods
        else:
            payment = p * periodic_rate / (Decimal(1) - (Decimal(1) + periodic_rate) ** (-periods))
        total = payment * periods
        return f"Payment per period = {payment}; number of payments = {periods}; total paid = {total}; total interest = {total - p}. Assumes fixed rate and end-of-period payments."
    except (InvalidOperation, ValueError, ArithmeticError) as exc:
        return f"Finance error: {exc}"

calculator_tools = [
    exact_calculation,
    convert_units,
    descriptive_statistics,
    compound_interest,
    loan_payment,
]
