"""
Base Product — Abstract Product Interface

The projection kernel interacts with products ONLY through this interface.
Every product type must implement these three methods:

    premium_cashflow(t, state)  -> float
    benefit_cashflow(t, state)  -> float
    expense_cashflow(t, state)  -> float

The projection kernel calls these methods at each time step, passing
a `state` dict containing kernel-computed actuarial quantities:

    state = {
        "survival": float,     # _tp_x — probability of surviving to time t
        "death_prob": float,   # _{t|1}q_x — probability of dying in year (t, t+1)
    }

Products define WHAT cashflows occur. The kernel defines WHEN and HOW
they are discounted and accumulated. No projection logic belongs here.

Architectural Principle
=======================

To add a new product type (e.g., Endowment, Whole Life), create a new
subclass of BaseProduct. The projection kernel (projection.py) is
NEVER modified to accommodate new products.
"""

from abc import ABC, abstractmethod


class BaseProduct(ABC):
    """Abstract base class for all insurance product types."""

    @abstractmethod
    def premium_cashflow(self, t: int, state: dict) -> float:
        """
        Compute premium cashflow at time t (beginning of year).

        Parameters
        ----------
        t : int
            Projection year (0-indexed).
        state : dict
            Kernel-computed state: {"survival": float, "death_prob": float}.

        Returns
        -------
        float
            Premium cashflow at time t.
        """
        ...

    @abstractmethod
    def benefit_cashflow(self, t: int, state: dict) -> float:
        """
        Compute benefit (claim) cashflow for year t (paid end of year).

        Parameters
        ----------
        t : int
            Projection year (0-indexed).
        state : dict
            Kernel-computed state: {"survival": float, "death_prob": float}.

        Returns
        -------
        float
            Benefit cashflow for year t.
        """
        ...

    @abstractmethod
    def expense_cashflow(self, t: int, state: dict) -> float:
        """
        Compute expense cashflow at time t (beginning of year).

        Parameters
        ----------
        t : int
            Projection year (0-indexed).
        state : dict
            Kernel-computed state: {"survival": float, "death_prob": float}.

        Returns
        -------
        float
            Expense cashflow at time t.
        """
        ...
