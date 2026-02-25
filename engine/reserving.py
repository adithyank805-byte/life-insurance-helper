"""
Reserving Module — Prospective Gross Premium Reserves

Computes reserves by running sub-projections through the generic
projection kernel for the remaining term at each duration.

This module is PRODUCT-AGNOSTIC — the product class is passed as
a parameter, so reserves can be computed for any product implementing
BaseProduct without modifying this module.

Mathematical Definition
=======================

V(t) = EPV(future outgo from t) - EPV(future income from t)
     = -(total_pv_net from sub-projection at duration t)

Boundary conditions: V(0) ~ 0, V(n) = 0.

Roll-Forward Identity (with lapses)
====================================

[V(t) + P - E] * (1+i) = q_{x+t} * SA + (1-q_{x+t}) * (1-l_t) * V(t+1)

The lapse factor (1-l_t) reduces the expected closing reserve because
lapsed policies exit without surrender value, releasing the reserve.

When lapse_rates is None, l_t = 0 and the identity reduces to the
pre-lapse version: [V(t) + P - E]*(1+i) = q*SA + p*V(t+1).
"""

from dataclasses import replace
from engine.assumptions import Assumptions
from engine.products.base_product import BaseProduct
from engine.projection import project


def compute_reserves(
    assumptions: Assumptions,
    solved_premium: float,
    product_class: type[BaseProduct],
) -> list[float]:
    """
    Compute prospective gross premium reserves at each duration t = 0..n.

    Parameters
    ----------
    assumptions : Assumptions
        Original assumptions (including lapse_rates if applicable).
    solved_premium : float
        The gross premium solved in the pricing phase.
    product_class : type[BaseProduct]
        Product class to instantiate for each sub-projection.

    Returns
    -------
    list[float]
        Reserves [V(0), V(1), ..., V(n)], length n+1.
    """
    n = assumptions.term
    reserves = [0.0] * (n + 1)

    for t in range(n):
        remaining_term = n - t
        remaining_qx = list(assumptions.qx[t:])
        remaining_lapse = (
            list(assumptions.lapse_rates[t:])
            if assumptions.lapse_rates is not None
            else None
        )

        sub_assumptions = Assumptions(
            entry_age=assumptions.entry_age + t,
            term=remaining_term,
            sum_assured=assumptions.sum_assured,
            interest_rate=assumptions.interest_rate,
            qx=remaining_qx,
            premium=solved_premium,
            expense_fixed=assumptions.expense_fixed,
            expense_pct=assumptions.expense_pct,
            lapse_rates=remaining_lapse,
        )

        product = product_class(sub_assumptions)
        result = project(product, sub_assumptions)
        summary = result["summary"]

        # V(t) = EPV(outgo) - EPV(income) = -total_pv_net
        reserves[t] = -summary["total_pv_net"]

    # V(n) = 0 exactly
    reserves[n] = 0.0

    return reserves


def compute_rollforward(
    assumptions: Assumptions,
    reserves: list[float],
    solved_premium: float,
) -> list[dict]:
    """
    Compute reserve roll-forward reconciliation for each year.

    With lapses:
    [V(t) + P - E] * (1+i) = q*SA + (1-q)*(1-l)*V(t+1) + profit(t)

    profit(t) should be ~0 for correctly computed reserves.

    When lapse_rates is None, l=0 and the formula reduces to
    the pre-lapse identity.

    Parameters
    ----------
    assumptions : Assumptions
        Original assumptions.
    reserves : list[float]
        Reserves [V(0), ..., V(n)].
    solved_premium : float
        The gross premium.

    Returns
    -------
    list[dict]
        One dict per year with roll-forward components and profit.
    """
    n = assumptions.term
    rows = []

    for t in range(n):
        V_open = reserves[t]
        V_close = reserves[t + 1]
        P = solved_premium
        q = assumptions.qx[t]
        p = 1.0 - q
        l = assumptions.lapse_rates[t] if assumptions.lapse_rates else 0.0
        SA = assumptions.sum_assured
        E = assumptions.expense_fixed + assumptions.expense_pct * P
        i = assumptions.interest_rate

        boy_amount = V_open + P - E
        investment_income = boy_amount * i
        claims = q * SA
        # Closing reserve adjusted for lapse persistency
        closing_reserve_exp = p * (1.0 - l) * V_close

        profit = boy_amount * (1.0 + i) - claims - closing_reserve_exp

        rows.append({
            "t": t,
            "opening_reserve": V_open,
            "premium": P,
            "expense": E,
            "boy_amount": boy_amount,
            "investment_income": investment_income,
            "claims": claims,
            "closing_reserve_exp": closing_reserve_exp,
            "profit": profit,
        })

    return rows
