"""
Assumptions Module — Centralized Assumption Definitions

All model parameters are defined here in a single dataclass.
No scattered parameter definitions anywhere else in the engine.

This module also provides input validation, enforcing all
numerical constraints from the Phase 0 scope lock, extended
in Phase 6 with optional lapse rates.
"""

from dataclasses import dataclass, field


@dataclass
class Assumptions:
    """
    Centralized container for all actuarial assumptions.

    Attributes
    ----------
    entry_age : int
        Age at policy inception (x).
    term : int
        Policy term in years (n).
    sum_assured : float
        Death benefit amount (SA).
    interest_rate : float
        Flat annual interest rate (i) for discounting.
    qx : list[float]
        Deterministic mortality vector [q_x, q_{x+1}, ..., q_{x+n-1}].
        Length must equal term.
    premium : float
        Level annual premium (P).
    expense_fixed : float
        Fixed annual per-policy expense (E_fixed).
    expense_pct : float
        Expense loading as proportion of premium (E_pct).
    lapse_rates : list[float] or None
        Optional deterministic lapse rate vector [l_0, l_1, ..., l_{n-1}].
        Length must equal term if provided. None means no lapses (all zeros).
    """

    entry_age: int
    term: int
    sum_assured: float
    interest_rate: float
    qx: list[float]
    premium: float
    expense_fixed: float
    expense_pct: float
    lapse_rates: list[float] | None = None


def validate_assumptions(assumptions: Assumptions) -> None:
    """
    Validate all inputs before projection execution.

    Raises ValueError with a specific message if any constraint is violated.
    """
    if not isinstance(assumptions.term, int) or assumptions.term < 1:
        raise ValueError(
            f"Term must be a positive integer, got {assumptions.term}"
        )

    if len(assumptions.qx) != assumptions.term:
        raise ValueError(
            f"qx vector length ({len(assumptions.qx)}) must equal "
            f"term ({assumptions.term})"
        )

    for t, q in enumerate(assumptions.qx):
        if q < 0.0 or q > 1.0:
            raise ValueError(f"qx[{t}] = {q} is out of range [0, 1]")

    if assumptions.interest_rate <= -1.0:
        raise ValueError(
            f"Interest rate must be > -1, got {assumptions.interest_rate}"
        )

    if assumptions.sum_assured <= 0.0:
        raise ValueError(
            f"Sum assured must be > 0, got {assumptions.sum_assured}"
        )

    if assumptions.premium < 0.0:
        raise ValueError(
            f"Premium must be >= 0, got {assumptions.premium}"
        )

    if assumptions.expense_fixed < 0.0:
        raise ValueError(
            f"Fixed expense must be >= 0, got {assumptions.expense_fixed}"
        )

    if assumptions.expense_pct < 0.0 or assumptions.expense_pct >= 1.0:
        raise ValueError(
            f"Expense percentage must be in [0, 1), got {assumptions.expense_pct}"
        )

    # --- Lapse rates (optional) ---
    if assumptions.lapse_rates is not None:
        if len(assumptions.lapse_rates) != assumptions.term:
            raise ValueError(
                f"lapse_rates length ({len(assumptions.lapse_rates)}) must equal "
                f"term ({assumptions.term})"
            )
        for t, l in enumerate(assumptions.lapse_rates):
            if l < 0.0 or l > 1.0:
                raise ValueError(
                    f"lapse_rates[{t}] = {l} is out of range [0, 1]"
                )
