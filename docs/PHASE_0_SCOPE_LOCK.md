# PHASE 0 — SCOPE LOCK

**Document Type:** Formal Scope Definition  
**Version:** 1.0  
**Date:** 2026-02-15  
**Status:** LOCKED — Awaiting Phase 1 instruction  

---

## 1. Product Scope

| Attribute | Specification |
|---|---|
| Product type | Level Term Life Insurance |
| Number of products | One (1) |
| Product variants | None |
| Riders / add-ons | None |

No other product types are in scope for Version 1. The architecture will support future product types through product definition classes; the projection kernel itself will remain product-agnostic.

---

## 2. Modeling Assumptions

### 2.1 Projection Basis

| Attribute | Specification |
|---|---|
| Time step | Annual (t = 0, 1, 2, …, n) |
| Claim payment timing | End of year of death |
| Premium payment timing | Beginning of year, contingent on survival to start of year |
| Projection term | Equal to policy term (fixed, finite) |

### 2.2 Mortality

| Attribute | Specification |
|---|---|
| Mortality input | Deterministic vector `qx = [q_{x}, q_{x+1}, …, q_{x+n-1}]` |
| Mortality type | Ultimate only |
| Select period | None — no select/ultimate differentiation |
| Mortality improvement | None |
| Mortality smoothing | None |
| Mortality source | User-supplied; engine does not generate or validate source tables |

### 2.3 Interest Rate

| Attribute | Specification |
|---|---|
| Interest rate | Single flat annual rate `i` |
| Discount factor | `v = 1 / (1 + i)` |
| Term structure | None — no yield curve |
| Rate variability | None — deterministic, constant across all projection years |

### 2.4 Premium

| Attribute | Specification |
|---|---|
| Premium pattern | Level (constant) annual premium `P` |
| Payment frequency | Annual |
| Premium payment term | Equal to policy term |
| Premium holidays | None |
| Premium waiver | None |

### 2.5 Benefits

| Attribute | Specification |
|---|---|
| Death benefit | Fixed sum assured `SA`, payable on death |
| Survival benefit | None |
| Maturity benefit | None |
| Benefit pattern | Level (constant) across policy term |

### 2.6 Expenses

| Attribute | Specification |
|---|---|
| Fixed expense | Constant annual per-policy amount `e_fixed`, incurred at start of each year if policy in-force |
| Percentage expense | Percentage of premium `e_pct × P`, incurred at start of each year if policy in-force |
| Acquisition expense | Not separately modeled |
| Expense inflation | None |
| Commission | None |

### 2.7 Persistency

| Attribute | Specification |
|---|---|
| Lapses | None — all policies persist until death or maturity |
| Surrenders | None |
| Paid-up conversions | None |
| Surrender values | None |

---

## 3. Mathematical Modeling Boundaries

### 3.1 Defined Quantities

For a life aged `x` at policy inception, with policy term `n` years:

| Symbol | Definition |
|---|---|
| `q_{x+t}` | Probability of death in year `(t, t+1)` for a life aged `x+t` at time `t` |
| `p_{x+t}` | `1 − q_{x+t}` — probability of surviving year `(t, t+1)` |
| `_tp_x` | `∏_{k=0}^{t−1} p_{x+k}` — probability of surviving from age `x` to age `x+t` |
| `_{t\|1}q_x` | `_tp_x · q_{x+t}` — probability of death in year `(t, t+1)` given alive at age `x` |
| `v` | `1 / (1 + i)` — annual discount factor |
| `v^t` | `(1 + i)^{−t}` — discount factor to time `t` |
| `SA` | Sum assured (death benefit) |
| `P` | Level annual premium |
| `e_fixed` | Fixed annual per-policy expense |
| `e_pct` | Expense loading as a proportion of premium |

### 3.2 Present Value Formulas

**PV of Benefits (death claims):**

```
PV_benefits = Σ_{t=0}^{n−1} SA · v^{t+1} · _{t|1}q_x
```

**PV of Premiums:**

```
PV_premiums = Σ_{t=0}^{n−1} P · v^t · _tp_x
```

**PV of Expenses:**

```
PV_expenses = Σ_{t=0}^{n−1} (e_fixed + e_pct · P) · v^t · _tp_x
```

### 3.3 Premium Solving (Equivalence Principle)

```
PV_premiums = PV_benefits + PV_expenses
```

Solving for `P`:

```
P · Σ_{t=0}^{n−1} v^t · _tp_x = Σ_{t=0}^{n−1} SA · v^{t+1} · _{t|1}q_x + Σ_{t=0}^{n−1} e_fixed · v^t · _tp_x + e_pct · P · Σ_{t=0}^{n−1} v^t · _tp_x
```

Rearranging:

```
P · (1 − e_pct) · Σ_{t=0}^{n−1} v^t · _tp_x = Σ_{t=0}^{n−1} SA · v^{t+1} · _{t|1}q_x + Σ_{t=0}^{n−1} e_fixed · v^t · _tp_x
```

Therefore:

```
P = [Σ_{t=0}^{n−1} SA · v^{t+1} · _{t|1}q_x + Σ_{t=0}^{n−1} e_fixed · v^t · _tp_x] / [(1 − e_pct) · Σ_{t=0}^{n−1} v^t · _tp_x]
```

### 3.4 Prospective Net Premium Reserve

At duration `t` (for a policy still in-force):

```
_tV = Σ_{k=0}^{n−t−1} SA · v^{k+1} · _{k|1}q_{x+t}  −  P_net · Σ_{k=0}^{n−t−1} v^k · _kp_{x+t}
```

Where `P_net` is the net premium (solved without expenses).

### 3.5 Numerical Constraints

| Constraint | Specification |
|---|---|
| `q_{x+t}` | Must satisfy `0 ≤ q_{x+t} ≤ 1` for all `t` |
| `i` | Must satisfy `i > −1` (typically `i > 0`) |
| `SA` | Must satisfy `SA > 0` |
| `n` | Must satisfy `n ≥ 1`, integer |
| `e_fixed` | Must satisfy `e_fixed ≥ 0` |
| `e_pct` | Must satisfy `0 ≤ e_pct < 1` |
| Mortality vector length | Must equal policy term `n` |

---

## 4. Architectural Commitments

1. **Product definitions are separated from projection logic.** The projection kernel executes generic cashflow arithmetic. Product-specific structures (premium pattern, benefit structure, expense rules) are defined in product definition classes.

2. **Future product expansion** (e.g., Whole Life, Endowment) will be achieved by creating new product definition classes. The projection kernel will NOT be modified to accommodate new products.

3. **Pricing and reserving are layered on top of projection outputs.** The projection kernel produces cashflow vectors. Pricing and reserving modules consume these vectors independently.

4. **No database, API, or UI layer** is part of the engine scope.

---

## 5. Explicit Exclusions — Version 1

The following are **not in scope** and will **not be built** in Version 1:

| Category | Excluded Item |
|---|---|
| **Products** | Whole life, endowment, universal life, annuities, unit-linked, group insurance |
| **Mortality** | Select/ultimate tables, mortality improvement (CMI, Lee-Carter), mortality smoothing, multiple decrement models |
| **Interest** | Yield curves, forward rates, stochastic interest rate models, reinvestment risk |
| **Persistency** | Lapse rates, surrender values, paid-up values, dynamic policyholder behavior |
| **Expenses** | Acquisition cost amortization, expense inflation, commission structures, renewal expense differentiation |
| **Premium** | Flexible premiums, single premiums, limited pay, premium holidays, modal factors |
| **Benefits** | Maturity benefits, survival benefits, riders, accelerated death benefits, substandard ratings |
| **Reinsurance** | All forms excluded |
| **Regulation** | IFRS 17, Solvency II, GAAP, statutory reserving frameworks, capital requirements |
| **Valuation** | Embedded value, market-consistent valuation, risk-neutral pricing |
| **Simulation** | Monte Carlo, stochastic scenarios, Economic Scenario Generators |
| **Infrastructure** | Database schemas, REST/GraphQL APIs, user interfaces, batch processing frameworks |
| **Reporting** | Financial statements, regulatory returns, dashboards |

---

## 6. Summary Statement

Version 1 of this engine is a **deterministic, annual-step, single-product (Level Term) actuarial projection engine**. It accepts a mortality vector, a flat interest rate, benefit and expense parameters, and produces:

1. A year-by-year cashflow projection
2. A gross premium via the equivalence principle
3. Prospective net premium reserves at each duration

It does nothing else. Expansion is handled structurally through product definitions, not through kernel modification.

---

**Scope is LOCKED. Awaiting Phase 1 instruction.**
