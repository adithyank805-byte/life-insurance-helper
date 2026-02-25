"""
Endowment Product — Endowment Life Insurance

Implements the BaseProduct interface for an Endowment policy.

An Endowment pays:
    - Death benefit SA if the policyholder dies during the term (same as Term)
    - Maturity benefit SA if the policyholder survives to the end of the term

Cashflow Definitions
====================

Premium (BOY, if alive):
    premium_cashflow(t) = P * survival(t)

Benefit:
    For t = 0, 1, ..., n-2 (non-maturity years):
        benefit_cashflow(t) = SA * death_prob(t)

    For t = n-1 (maturity year):
        benefit_cashflow(t) = SA * death_prob(t)           [death benefit]
                            + SA * (survival(t) - death_prob(t))  [maturity benefit]

    The maturity survival probability is derived from kernel-provided state:
        p(n) = p(n-1) - d(n-1) = survival(t) - death_prob(t)

    This is the identity p(n) = p(n-1) * (1 - q_{x+n-1}), NOT survival
    recursion — it uses only the two quantities already computed by the kernel.

    Both death and maturity benefits are paid at EOY, so the kernel's
    EOY discounting (v^{t+1}) applies correctly to the total.

Expense (BOY, if alive):
    expense_cashflow(t) = survival(t) * (E_fixed + E_pct * P)

No projection logic resides here. No survival recursion.
"""

from engine.assumptions import Assumptions
from engine.products.base_product import BaseProduct


class EndowmentProduct(BaseProduct):
    """
    Endowment Life Insurance product.

    Death benefit during term + maturity benefit at end of term.

    Parameters
    ----------
    assumptions : Assumptions
        Centralized assumptions including SA, premium, expenses, term.
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
        Death benefit during term + maturity benefit at end of term.

        For t < n-1:
            Benefit(t) = SA * d(t)

        For t = n-1 (maturity year):
            Benefit(t) = SA * d(t) + SA * p(n)
                       = SA * d(t) + SA * (p(t) - d(t))
                       = SA * p(t)

        Both components are paid at EOY, consistent with kernel discounting.
        """
        death_benefit = self.assumptions.sum_assured * state["death_prob"]

        if t == self.assumptions.term - 1:
            # Maturity benefit: SA * survival to end of term
            # p(n) = p(n-1) - d(n-1) = survival - death_prob
            survival_to_maturity = state["survival"] - state["death_prob"]
            maturity_benefit = self.assumptions.sum_assured * survival_to_maturity
            return death_benefit + maturity_benefit

        return death_benefit

    def expense_cashflow(self, t: int, state: dict) -> float:
        """
        Fixed + percentage expenses incurred at beginning of year if alive.

        Expense_CF(t) = _tp_x * (E_fixed + E_pct * P)
        """
        return state["survival"] * (
            self.assumptions.expense_fixed
            + self.assumptions.expense_pct * self.assumptions.premium
        )
