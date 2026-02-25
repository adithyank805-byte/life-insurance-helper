"""
Term Product — Level Term Life Insurance

Implements the BaseProduct interface for Level Term Insurance.

Cashflow Definitions
====================

Premium (BOY, if alive):
    premium_cashflow(t) = P * survival(t)

Benefit (EOY, on death):
    benefit_cashflow(t) = SA * death_prob(t)

Expense (BOY, if alive):
    expense_cashflow(t) = survival(t) * (E_fixed + E_pct * P)

This class contains NO projection logic — no survival recursion,
no discounting, no time-loop management. It only defines WHAT
cashflows occur for a Level Term product.
"""

from engine.assumptions import Assumptions
from engine.products.base_product import BaseProduct


class TermProduct(BaseProduct):
    """
    Level Term Life Insurance product.

    Parameters
    ----------
    assumptions : Assumptions
        Centralized assumptions including SA, premium, expenses.
    """

    def __init__(self, assumptions: Assumptions):
        self.assumptions = assumptions

    def premium_cashflow(self, t: int, state: dict) -> float:
        """
        Level premium paid at beginning of year if alive.

        Premium_CF(t) = P * _tp_x
        """
        return self.assumptions.premium * state["survival"]

    def benefit_cashflow(self, t: int, state: dict) -> float:
        """
        Death benefit paid at end of year on death.

        Claim_CF(t) = SA * _{t|1}q_x
        """
        return self.assumptions.sum_assured * state["death_prob"]

    def expense_cashflow(self, t: int, state: dict) -> float:
        """
        Fixed + percentage expenses incurred at beginning of year if alive.

        Expense_CF(t) = _tp_x * (E_fixed + E_pct * P)
        """
        return state["survival"] * (
            self.assumptions.expense_fixed
            + self.assumptions.expense_pct * self.assumptions.premium
        )
