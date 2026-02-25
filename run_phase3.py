"""
Phase 3 Test Harness — Reserving Layer Validation

Computes prospective gross premium reserves at each duration and
validates through:

1. Reserve boundary conditions: V(0) ~ 0, V(n) = 0
2. Reserve shape: increasing then decreasing for level term (hump-shaped)
3. Roll-forward reconciliation: profit ~ 0 at every duration
4. No negative reserves (for level term with level premium)

The roll-forward identity is:

    [V(t) + P - E] * (1+i) = q_{x+t} * SA + p_{x+t} * V(t+1) + profit(t)

    profit(t) should be exactly 0 (within floating-point tolerance).
"""

from dataclasses import replace
from engine.product import LevelTermPolicy
from engine.pricing import solve_premium_bisection
from engine.reserving import compute_reserves, compute_rollforward

TOLERANCE = 1e-6
SEPARATOR = "=" * 80


def main():
    # =================================================================
    # SETUP: Solve premium first (reusing Phase 2)
    # =================================================================
    base_policy = LevelTermPolicy(
        entry_age=30,
        term=10,
        sum_assured=1_000_000.0,
        interest_rate=0.05,
        qx=[0.001, 0.001, 0.002, 0.002, 0.003, 0.003, 0.004, 0.004, 0.005, 0.005],
        premium=0.0,
        expense_fixed=100.0,
        expense_pct=0.05,
    )

    pricing_result = solve_premium_bisection(base_policy)
    P_solved = pricing_result["premium"]

    print(SEPARATOR)
    print("PHASE 3 -- PROSPECTIVE RESERVES")
    print(SEPARATOR)
    print(f"\nSolved Gross Premium: {P_solved:.6f}")

    # =================================================================
    # COMPUTE RESERVES
    # =================================================================
    reserves = compute_reserves(base_policy, P_solved)

    print(f"\n{'t':>3}  {'V(t)':>16}")
    print("-" * 22)
    for t, V in enumerate(reserves):
        print(f"{t:>3}  {V:>16.6f}")

    # =================================================================
    # RESERVE BOUNDARY CONDITIONS
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("VALIDATION CHECKS")
    print(SEPARATOR)

    all_passed = True

    # Check 1: V(0) ~ 0
    v0_ok = abs(reserves[0]) < TOLERANCE
    status = "PASS" if v0_ok else "FAIL"
    if not v0_ok:
        all_passed = False
    print(f"[{status}] Check 1: V(0) = {reserves[0]:.2e} (expected ~0, "
          f"threshold {TOLERANCE:.0e})")

    # Check 2: V(n) = 0
    vn_ok = reserves[-1] == 0.0
    status = "PASS" if vn_ok else "FAIL"
    if not vn_ok:
        all_passed = False
    print(f"[{status}] Check 2: V(n) = {reserves[-1]:.6f} (expected exactly 0)")

    # Check 3: No negative reserves
    no_negatives = all(V >= -TOLERANCE for V in reserves)
    status = "PASS" if no_negatives else "FAIL"
    if not no_negatives:
        all_passed = False
    min_v = min(reserves)
    print(f"[{status}] Check 3: No negative reserves "
          f"(min = {min_v:.6f})")

    # =================================================================
    # ROLL-FORWARD RECONCILIATION
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("ROLL-FORWARD RECONCILIATION")
    print(SEPARATOR)

    rollforward = compute_rollforward(base_policy, reserves, P_solved)

    header = (
        f"{'t':>3}  {'Opening V(t)':>14}  {'Premium':>12}  "
        f"{'Expense':>12}  {'Invest Inc':>14}  "
        f"{'Claims':>14}  {'Closing pV':>14}  {'Profit':>12}"
    )
    print(f"\n{header}")
    print("-" * len(header))

    max_profit_abs = 0.0
    for row in rollforward:
        print(
            f"{row['t']:>3}  "
            f"{row['opening_reserve']:>14.4f}  "
            f"{row['premium']:>12.4f}  "
            f"{row['expense']:>12.4f}  "
            f"{row['investment_income']:>14.4f}  "
            f"{row['claims']:>14.4f}  "
            f"{row['closing_reserve_exp']:>14.4f}  "
            f"{row['profit']:>12.2e}"
        )
        max_profit_abs = max(max_profit_abs, abs(row["profit"]))

    # Check 4: Roll-forward profit ~ 0 at every duration
    rf_ok = max_profit_abs < TOLERANCE
    status = "PASS" if rf_ok else "FAIL"
    if not rf_ok:
        all_passed = False
    print(f"\n[{status}] Check 4: Roll-forward reconciliation "
          f"(max |profit| = {max_profit_abs:.2e}, threshold {TOLERANCE:.0e})")

    # =================================================================
    # RESERVE MOVEMENT COMMENTARY
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("RESERVE MOVEMENT ANALYSIS")
    print(SEPARATOR)

    print(f"\n{'t':>3}  {'V(t)':>14}  {'Delta V':>14}  {'Direction':>12}")
    print("-" * 50)
    for t in range(len(reserves)):
        if t == 0:
            print(f"{t:>3}  {reserves[t]:>14.4f}  {'--':>14}  {'(inception)':>12}")
        else:
            delta = reserves[t] - reserves[t - 1]
            direction = "UP" if delta > 0 else ("DOWN" if delta < 0 else "FLAT")
            print(f"{t:>3}  {reserves[t]:>14.4f}  {delta:>14.4f}  {direction:>12}")

    # Find peak reserve
    peak_t = max(range(len(reserves)), key=lambda t: reserves[t])
    print(f"\nPeak reserve at t={peak_t}: V({peak_t}) = {reserves[peak_t]:.4f}")

    # =================================================================
    # FINAL RESULT
    # =================================================================
    print(f"\n{SEPARATOR}")
    final = "ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED"
    print(f">>> {final} <<<")
    print(SEPARATOR)

    return all_passed


if __name__ == "__main__":
    main()
