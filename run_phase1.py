"""
Phase 1 Test Harness — Projection Kernel Validation

Runs a deterministic projection for a sample Level Term policy and
performs reconciliation checks to verify mathematical correctness.

Sample Inputs
=============
- Entry age:    30
- Term:         10 years
- Sum assured:  1,000,000
- Interest:     5% flat
- Premium:      4,000 (arbitrary, not solved)
- Fixed expense: 100 per year
- Expense %:    5% of premium
- qx:           [0.001, 0.001, 0.002, 0.002, 0.003, 0.003, 0.004, 0.004, 0.005, 0.005]

Reconciliation Checks
=====================
1. Survival is monotonically non-increasing
2. Terminal survival + cumulative deaths = 1.0 (within tolerance)
3. Discount factors are monotonically decreasing
4. Total PV of net CFs = sum of component PVs
5. Cashflow signs are logically correct
"""

from engine.product import LevelTermPolicy
from engine.projection import project

TOLERANCE = 1e-10


def main():
    # --- Define sample policy ---
    policy = LevelTermPolicy(
        entry_age=30,
        term=10,
        sum_assured=1_000_000.0,
        interest_rate=0.05,
        qx=[0.001, 0.001, 0.002, 0.002, 0.003, 0.003, 0.004, 0.004, 0.005, 0.005],
        premium=4_000.0,
        expense_fixed=100.0,
        expense_pct=0.05,
    )

    # --- Run projection ---
    result = project(policy)
    rows = result["rows"]
    summary = result["summary"]

    # --- Print projection table ---
    header = (
        f"{'t':>3}  {'Survival':>12}  {'Death Prob':>12}  "
        f"{'Premium CF':>12}  {'Claim CF':>12}  {'Expense CF':>12}  "
        f"{'Net CF':>12}  {'v(t)':>12}  {'v(t+1)':>12}  {'PV Net CF':>12}"
    )
    print("=" * len(header))
    print("PHASE 1 — DETERMINISTIC PROJECTION TABLE")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for row in rows:
        print(
            f"{row['t']:>3}  "
            f"{row['survival']:>12.8f}  "
            f"{row['death_prob']:>12.8f}  "
            f"{row['premium_cf']:>12.2f}  "
            f"{row['claim_cf']:>12.2f}  "
            f"{row['expense_cf']:>12.2f}  "
            f"{row['net_cf']:>12.2f}  "
            f"{row['discount_boy']:>12.8f}  "
            f"{row['discount_eoy']:>12.8f}  "
            f"{row['pv_net_cf']:>12.4f}"
        )

    print("-" * len(header))
    print(f"\nTotal PV of Premiums:  {summary['total_pv_premium']:>16.4f}")
    print(f"Total PV of Claims:    {summary['total_pv_claim']:>16.4f}")
    print(f"Total PV of Expenses:  {summary['total_pv_expense']:>16.4f}")
    print(f"Total PV of Net CFs:   {summary['total_pv_net']:>16.4f}")
    print(f"Terminal Survival:     {summary['terminal_survival']:>16.8f}")
    print(f"Total Death Probs:     {summary['total_deaths']:>16.8f}")

    # --- Reconciliation Checks ---
    print("\n" + "=" * 60)
    print("RECONCILIATION CHECKS")
    print("=" * 60)

    all_passed = True

    # Check 1: Survival monotonically non-increasing
    survival_mono = all(
        rows[t + 1]["survival"] <= rows[t]["survival"]
        for t in range(len(rows) - 1)
    )
    status = "PASS" if survival_mono else "FAIL"
    if not survival_mono:
        all_passed = False
    print(f"[{status}] Check 1: Survival is monotonically non-increasing")

    # Check 2: Terminal survival + cumulative deaths = 1.0
    identity = summary["terminal_survival"] + summary["total_deaths"]
    identity_ok = abs(identity - 1.0) < TOLERANCE
    status = "PASS" if identity_ok else "FAIL"
    if not identity_ok:
        all_passed = False
    print(
        f"[{status}] Check 2: p(n) + Sum(d(t)) = {identity:.15f} "
        f"(expected 1.0, diff = {abs(identity - 1.0):.2e})"
    )

    # Check 3: Discount factors monotonically decreasing
    discount_mono = all(
        rows[t + 1]["discount_boy"] < rows[t]["discount_boy"]
        for t in range(len(rows) - 1)
    )
    status = "PASS" if discount_mono else "FAIL"
    if not discount_mono:
        all_passed = False
    print(f"[{status}] Check 3: Discount factors monotonically decreasing")

    # Check 4: Total PV consistency
    pv_check_sum = (
        summary["total_pv_premium"]
        - summary["total_pv_claim"]
        - summary["total_pv_expense"]
    )
    pv_diff = abs(pv_check_sum - summary["total_pv_net"])
    pv_consistent = pv_diff < TOLERANCE
    status = "PASS" if pv_consistent else "FAIL"
    if not pv_consistent:
        all_passed = False
    print(
        f"[{status}] Check 4: PV(P) - PV(C) - PV(E) = {pv_check_sum:.6f}, "
        f"Total PV Net = {summary['total_pv_net']:.6f}, "
        f"diff = {pv_diff:.2e}"
    )

    # Check 5: Cashflow signs
    signs_ok = True
    for row in rows:
        if row["premium_cf"] < 0:
            signs_ok = False
        if row["claim_cf"] < 0:
            signs_ok = False
        if row["expense_cf"] < 0:
            signs_ok = False
    status = "PASS" if signs_ok else "FAIL"
    if not signs_ok:
        all_passed = False
    print(f"[{status}] Check 5: All cashflow signs logically correct")

    print("-" * 60)
    final = "ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED"
    print(f"\n>>> {final} <<<\n")

    return all_passed


if __name__ == "__main__":
    main()
