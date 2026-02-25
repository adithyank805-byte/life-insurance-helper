"""
Projection Module — Generic Deterministic Cashflow Projection Kernel

This kernel is FULLY PRODUCT-AGNOSTIC. It does NOT reference any specific
product type. It interacts with products ONLY through the BaseProduct
interface (premium_cashflow, benefit_cashflow, expense_cashflow).

Kernel Responsibilities
=======================
1. Execute time loop over projection years t = 0, 1, ..., n-1
2. Manage in-force recursion (survival + lapse decrements)
3. Compute death and lapse probabilities
4. Compute discount factors: v(t) = (1 + i)^{-t}
5. Call product-defined cashflow methods at each step
6. Apply discounting (BOY for premiums/expenses, EOY for benefits)
7. Produce projection table with per-year and summary outputs

In-Force Recursion (Phase 6)
=============================
Without lapses:
    IF(0) = 1
    IF(t) = IF(t-1) * (1 - q_{x+t-1})

With lapses:
    IF(0) = 1
    IF(t) = IF(t-1) * (1 - q_{x+t-1}) * (1 - l_{t-1})

Death probability in year t:
    d(t) = IF(t) * q_{x+t}

Lapse count in year t:
    lapse(t) = IF(t) * (1 - q_{x+t}) * l_t

Identity:
    IF(n) + Sum(d(t)) + Sum(lapse(t)) = 1.0

Products see state["survival"] = IF(t), state["death_prob"] = d(t).
They do not know about lapses — the reduced in-force probability
automatically reduces all cashflows proportionally.

Cashflow Timing
===============
- Premium and expense: beginning of year -> discounted at v(t)
- Benefit (claims):    end of year        -> discounted at v(t+1)
"""

from engine.assumptions import Assumptions, validate_assumptions
from engine.products.base_product import BaseProduct


# --------------------------------------------------------------------------
# Internal actuarial vector computations (private to projection kernel)
# --------------------------------------------------------------------------

def _compute_inforce_probs(
    qx: list[float],
    lapse_rates: list[float] | None = None,
) -> list[float]:
    """
    In-force probability recursion.

    IF(0) = 1
    IF(t) = IF(t-1) * (1 - q_{x+t-1}) * (1 - l_{t-1})

    When lapse_rates is None, lapse factor is 1.0 (no lapses).

    Returns [IF(0), IF(1), ..., IF(n)], length n+1.
    """
    n = len(qx)
    inforce = [0.0] * (n + 1)
    inforce[0] = 1.0

    for t in range(1, n + 1):
        lapse_factor = 1.0 - lapse_rates[t - 1] if lapse_rates else 1.0
        inforce[t] = inforce[t - 1] * (1.0 - qx[t - 1]) * lapse_factor

    return inforce


def _compute_death_probs(qx: list[float], inforce: list[float]) -> list[float]:
    """
    Death probability: d(t) = IF(t) * q_{x+t}.

    Returns [d(0), d(1), ..., d(n-1)], length n.
    """
    n = len(qx)
    death = [0.0] * n
    for t in range(n):
        death[t] = inforce[t] * qx[t]
    return death


def _compute_lapse_counts(
    qx: list[float],
    inforce: list[float],
    lapse_rates: list[float] | None = None,
) -> list[float]:
    """
    Lapse count: lapse(t) = IF(t) * (1 - q_{x+t}) * l_t.

    Returns [lapse(0), lapse(1), ..., lapse(n-1)], length n.
    """
    n = len(qx)
    lapses = [0.0] * n
    if lapse_rates is None:
        return lapses
    for t in range(n):
        lapses[t] = inforce[t] * (1.0 - qx[t]) * lapse_rates[t]
    return lapses


def _compute_discount_factors(interest_rate: float, n: int) -> list[float]:
    """
    Discount factors: v(t) = (1 + i)^{-t}, computed recursively.

    Returns [v(0), v(1), ..., v(n)], length n+1.
    """
    v_annual = 1.0 / (1.0 + interest_rate)
    discount = [0.0] * (n + 1)
    discount[0] = 1.0
    for t in range(1, n + 1):
        discount[t] = discount[t - 1] * v_annual
    return discount


# --------------------------------------------------------------------------
# Generic projection kernel
# --------------------------------------------------------------------------

def project(product: BaseProduct, assumptions: Assumptions) -> dict:
    """
    Execute a deterministic annual projection.

    The kernel computes actuarial vectors (in-force, death, lapse, discount),
    then calls the product's cashflow methods at each time step. No
    product-specific logic exists in this function.

    Parameters
    ----------
    product : BaseProduct
        Any product implementing the BaseProduct interface.
    assumptions : Assumptions
        Centralized model assumptions.

    Returns
    -------
    dict with keys:
        "rows" : list[dict]
            One dict per projection year (t=0..n-1), each containing:
            t, survival (=IF), death_prob, lapse_count,
            premium_cf, claim_cf, expense_cf, net_cf,
            discount_boy, discount_eoy,
            pv_premium, pv_claim, pv_expense, pv_net_cf.
        "summary" : dict
            total_pv_premium, total_pv_claim, total_pv_expense,
            total_pv_net, terminal_inforce, total_deaths, total_lapses.
    """
    validate_assumptions(assumptions)

    n = assumptions.term

    # --- Compute actuarial vectors ---
    inforce = _compute_inforce_probs(assumptions.qx, assumptions.lapse_rates)
    death = _compute_death_probs(assumptions.qx, inforce)
    lapses = _compute_lapse_counts(
        assumptions.qx, inforce, assumptions.lapse_rates
    )
    discount = _compute_discount_factors(assumptions.interest_rate, n)

    # --- Project cashflows year by year ---
    rows = []
    total_pv_premium = 0.0
    total_pv_claim = 0.0
    total_pv_expense = 0.0
    total_pv_net = 0.0

    for t in range(n):
        # Kernel-computed state passed to product
        # Products see "survival" = in-force probability at time t
        # Products see "death_prob" = death probability during year t
        # Products do NOT see lapse information — the reduced in-force
        # automatically reduces all product-computed cashflows.
        state = {
            "survival": inforce[t],
            "death_prob": death[t],
        }

        # Product-defined cashflows (no product logic in kernel)
        premium_cf = product.premium_cashflow(t, state)
        claim_cf = product.benefit_cashflow(t, state)
        expense_cf = product.expense_cashflow(t, state)
        net_cf = premium_cf - claim_cf - expense_cf

        # Present values with correct timing
        pv_premium = premium_cf * discount[t]        # BOY discounting
        pv_claim = claim_cf * discount[t + 1]        # EOY discounting
        pv_expense = expense_cf * discount[t]        # BOY discounting
        pv_net_cf = pv_premium - pv_claim - pv_expense

        # Accumulate totals
        total_pv_premium += pv_premium
        total_pv_claim += pv_claim
        total_pv_expense += pv_expense
        total_pv_net += pv_net_cf

        rows.append({
            "t": t,
            "survival": inforce[t],
            "death_prob": death[t],
            "lapse_count": lapses[t],
            "premium_cf": premium_cf,
            "claim_cf": claim_cf,
            "expense_cf": expense_cf,
            "net_cf": net_cf,
            "discount_boy": discount[t],
            "discount_eoy": discount[t + 1],
            "pv_premium": pv_premium,
            "pv_claim": pv_claim,
            "pv_expense": pv_expense,
            "pv_net_cf": pv_net_cf,
        })

    summary = {
        "total_pv_premium": total_pv_premium,
        "total_pv_claim": total_pv_claim,
        "total_pv_expense": total_pv_expense,
        "total_pv_net": total_pv_net,
        "terminal_inforce": inforce[n],
        "total_deaths": sum(death),
        "total_lapses": sum(lapses),
    }

    return {"rows": rows, "summary": summary}
