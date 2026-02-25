"""
Pydantic Models — API Input/Output Schemas

These models translate between HTTP JSON and the engine's Assumptions dataclass.
No actuarial logic here — only data validation and serialization.
"""

from pydantic import BaseModel, Field


# ---- Input Models ----

class AssumptionsInput(BaseModel):
    """JSON input schema for all API endpoints."""
    entry_age: int = Field(..., ge=0, le=120, description="Age at policy inception")
    term: int = Field(..., ge=1, le=100, description="Policy term in years")
    sum_assured: float = Field(..., gt=0, description="Death benefit amount")
    interest_rate: float = Field(..., gt=-1, description="Annual interest rate")
    qx: list[float] = Field(..., description="Mortality vector, length = term")
    premium: float = Field(0.0, ge=0, description="Level annual premium (for projection)")
    expense_fixed: float = Field(0.0, ge=0, description="Fixed annual expense")
    expense_pct: float = Field(0.0, ge=0, lt=1, description="Expense % of premium")
    lapse_rates: list[float] | None = Field(None, description="Optional lapse vector, length = term")
    product_type: str = Field("term", description="Product type: 'term' or 'endowment'")


# ---- Output Models ----

class ProjectionRow(BaseModel):
    t: int
    survival: float
    death_prob: float
    lapse_count: float
    premium_cf: float
    claim_cf: float
    expense_cf: float
    net_cf: float
    discount_boy: float
    discount_eoy: float
    pv_premium: float
    pv_claim: float
    pv_expense: float
    pv_net_cf: float


class ProjectionSummary(BaseModel):
    total_pv_premium: float
    total_pv_claim: float
    total_pv_expense: float
    total_pv_net: float
    terminal_inforce: float
    total_deaths: float
    total_lapses: float


class ProjectionResponse(BaseModel):
    rows: list[ProjectionRow]
    summary: ProjectionSummary


class PricingResult(BaseModel):
    premium: float
    f_at_solution: float
    iterations: int
    converged: bool
    tolerance: float


class PricingResponse(BaseModel):
    pricing: PricingResult
    projection: ProjectionResponse


class RollforwardRow(BaseModel):
    t: int
    opening_reserve: float
    premium: float
    expense: float
    boy_amount: float
    investment_income: float
    claims: float
    closing_reserve_exp: float
    profit: float


class ReserveResponse(BaseModel):
    reserves: list[float]
    rollforward: list[RollforwardRow]
    solved_premium: float
    projection: ProjectionResponse
