"""
FastAPI Application — Thin API Layer Over the Actuarial Engine

This file contains ZERO actuarial formulas.
It imports engine modules directly and translates between HTTP JSON
and engine dataclasses.

Endpoints:
    POST /projection  — run projection with given premium
    POST /pricing     — solve for premium + return projection
    POST /reserve     — compute reserves + roll-forward + projection
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import replace

from engine.assumptions import Assumptions
from engine.products.term_product import TermProduct
from engine.products.endowment_product import EndowmentProduct
from engine.projection import project
from engine.pricing import solve_premium_bisection
from engine.reserving import compute_reserves, compute_rollforward

from models import (
    AssumptionsInput,
    ProjectionResponse,
    ProjectionRow,
    ProjectionSummary,
    PricingResponse,
    PricingResult,
    ReserveResponse,
    RollforwardRow,
)

app = FastAPI(
    title="Actuarial Engine API",
    description="Deterministic actuarial projection, pricing, and reserving.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Helpers (data translation only, no math) ----

def _get_product_class(product_type: str):
    """Map product type string to product class."""
    mapping = {
        "term": TermProduct,
        "endowment": EndowmentProduct,
    }
    if product_type not in mapping:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown product_type '{product_type}'. Must be 'term' or 'endowment'.",
        )
    return mapping[product_type]


def _to_assumptions(inp: AssumptionsInput, premium_override: float | None = None) -> Assumptions:
    """Convert Pydantic input model to engine Assumptions dataclass."""
    return Assumptions(
        entry_age=inp.entry_age,
        term=inp.term,
        sum_assured=inp.sum_assured,
        interest_rate=inp.interest_rate,
        qx=inp.qx,
        premium=premium_override if premium_override is not None else inp.premium,
        expense_fixed=inp.expense_fixed,
        expense_pct=inp.expense_pct,
        lapse_rates=inp.lapse_rates,
    )


def _to_projection_response(result: dict) -> ProjectionResponse:
    """Convert engine projection output to Pydantic response model."""
    rows = [ProjectionRow(**row) for row in result["rows"]]
    summary = ProjectionSummary(**result["summary"])
    return ProjectionResponse(rows=rows, summary=summary)


# ---- Endpoints ----

@app.post("/projection", response_model=ProjectionResponse)
def run_projection(inp: AssumptionsInput):
    """Run a deterministic projection with the given premium."""
    try:
        assumptions = _to_assumptions(inp)
        product_class = _get_product_class(inp.product_type)
        product = product_class(assumptions)
        result = project(product, assumptions)
        return _to_projection_response(result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/pricing", response_model=PricingResponse)
def run_pricing(inp: AssumptionsInput):
    """Solve for the level annual premium and return the projection."""
    try:
        assumptions = _to_assumptions(inp)
        product_class = _get_product_class(inp.product_type)

        pricing_result = solve_premium_bisection(assumptions, product_class)
        solved_premium = pricing_result["premium"]

        # Re-run projection with solved premium
        priced_assumptions = replace(assumptions, premium=solved_premium)
        product = product_class(priced_assumptions)
        proj_result = project(product, priced_assumptions)

        return PricingResponse(
            pricing=PricingResult(
                premium=pricing_result["premium"],
                f_at_solution=pricing_result["f_at_solution"],
                iterations=pricing_result["iterations"],
                converged=pricing_result["converged"],
                tolerance=pricing_result["tolerance"],
            ),
            projection=_to_projection_response(proj_result),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/reserve", response_model=ReserveResponse)
def run_reserve(inp: AssumptionsInput):
    """Solve premium, compute reserves, roll-forward, and projection."""
    try:
        assumptions = _to_assumptions(inp)
        product_class = _get_product_class(inp.product_type)

        # Solve premium first
        pricing_result = solve_premium_bisection(assumptions, product_class)
        solved_premium = pricing_result["premium"]

        # Compute reserves
        reserves = compute_reserves(assumptions, solved_premium, product_class)

        # Compute roll-forward
        rollforward = compute_rollforward(assumptions, reserves, solved_premium)

        # Projection with solved premium
        priced_assumptions = replace(assumptions, premium=solved_premium)
        product = product_class(priced_assumptions)
        proj_result = project(product, priced_assumptions)

        return ReserveResponse(
            reserves=reserves,
            rollforward=[RollforwardRow(**row) for row in rollforward],
            solved_premium=solved_premium,
            projection=_to_projection_response(proj_result),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
