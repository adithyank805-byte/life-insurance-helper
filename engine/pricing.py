"""
Pricing Module — Level Annual Premium Solver

Solves for the level annual premium P such that:

    f(P) = EPV(Premiums) - EPV(Benefits) - EPV(Expenses) = 0

Uses bisection root-finding over the projection kernel.
This module is PRODUCT-AGNOSTIC — the product class is passed
as a parameter, so any product implementing BaseProduct can be priced.

No projection logic is duplicated here.
"""

from dataclasses import replace
from engine.assumptions import Assumptions
from engine.products.base_product import BaseProduct
from engine.projection import project


def pricing_objective(
    assumptions: Assumptions,
    candidate_premium: float,
    product_class: type[BaseProduct],
) -> float:
    """
    Evaluate f(P) = EPV(Premiums) - EPV(Benefits) - EPV(Expenses)
    for a candidate premium, by running the projection kernel.

    Parameters
    ----------
    assumptions : Assumptions
        Base assumptions (premium field is overridden).
    candidate_premium : float
        Candidate level annual premium to test.
    product_class : type[BaseProduct]
        Product class to instantiate with the test assumptions.

    Returns
    -------
    float
        f(P). Positive means premium is too high; negative means too low.
    """
    test_assumptions = replace(assumptions, premium=candidate_premium)
    product = product_class(test_assumptions)
    result = project(product, test_assumptions)
    summary = result["summary"]

    return (
        summary["total_pv_premium"]
        - summary["total_pv_claim"]
        - summary["total_pv_expense"]
    )


def solve_premium_bisection(
    assumptions: Assumptions,
    product_class: type[BaseProduct],
    p_low: float = 0.0,
    p_high: float | None = None,
    tolerance: float = 1e-8,
    max_iterations: int = 200,
) -> dict:
    """
    Solve for the level annual premium using the bisection method.

    Product-agnostic: works with any product implementing BaseProduct.

    Parameters
    ----------
    assumptions : Assumptions
        Base assumptions (premium field is ignored; it will be solved).
    product_class : type[BaseProduct]
        Product class to instantiate for each candidate premium.
    p_low : float, optional
        Lower bound for premium search. Default 0.0.
    p_high : float or None, optional
        Upper bound for premium search. Default: 2 * SA / n.
    tolerance : float, optional
        Convergence tolerance on premium. Default 1e-8.
    max_iterations : int, optional
        Maximum bisection iterations. Default 200.

    Returns
    -------
    dict with keys:
        "premium", "f_at_solution", "iterations", "converged",
        "bracket_final", "tolerance".

    Raises
    ------
    ValueError
        If the bracket does not contain a sign change.
    RuntimeError
        If the method fails to converge within max_iterations.
    """
    if p_high is None:
        p_high = 2.0 * assumptions.sum_assured / assumptions.term

    # --- Validate bracket ---
    f_low = pricing_objective(assumptions, p_low, product_class)
    f_high = pricing_objective(assumptions, p_high, product_class)

    if f_low > 0:
        raise ValueError(
            f"f(p_low={p_low}) = {f_low:.6f} > 0. "
            f"Lower bound is already too high."
        )
    if f_high < 0:
        raise ValueError(
            f"f(p_high={p_high}) = {f_high:.6f} < 0. "
            f"Upper bound is too low."
        )

    # --- Bisection iterations ---
    iterations = 0
    for i in range(max_iterations):
        iterations = i + 1
        p_mid = (p_low + p_high) / 2.0
        f_mid = pricing_objective(assumptions, p_mid, product_class)

        if f_mid > 0:
            p_high = p_mid
        else:
            p_low = p_mid

        if (p_high - p_low) < tolerance:
            solved_premium = (p_low + p_high) / 2.0
            f_solution = pricing_objective(
                assumptions, solved_premium, product_class
            )
            return {
                "premium": solved_premium,
                "f_at_solution": f_solution,
                "iterations": iterations,
                "converged": True,
                "bracket_final": (p_low, p_high),
                "tolerance": tolerance,
            }

    # --- Non-convergence ---
    solved_premium = (p_low + p_high) / 2.0
    f_solution = pricing_objective(assumptions, solved_premium, product_class)
    raise RuntimeError(
        f"Bisection did not converge after {max_iterations} iterations. "
        f"Final bracket: [{p_low:.8f}, {p_high:.8f}], "
        f"f(P_mid) = {f_solution:.2e}"
    )
