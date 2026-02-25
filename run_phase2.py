"""
Phase 2 Test Harness — Pricing Layer Validation

Solves for the level annual premium using bisection and validates
the result through:

1. Convergence diagnostics — f(P) at solution ~ 0
2. Verification projection — re-run kernel with solved premium, confirm PV net ~ 0
3. Sensitivity analysis — directional checks under assumption shocks:
   - Increase interest rate   -> premium must DECREASE
   - Increase mortality       -> premium must INCREASE
   - Increase expenses        -> premium must INCREASE
   - Decrease term            -> premium must DECREASE

If any directional check fails, an explicit warning is printed
stating the projection kernel may be incorrect.
"""

from dataclasses import replace
from engine.product import LevelTermPolicy
from engine.pricing import solve_premium_bisection
from engine.projection import project


SEPARATOR = "=" * 72


def main():
    # =================================================================
    # BASE CASE
    # =================================================================
    base_policy = LevelTermPolicy(
        entry_age=30,
        term=10,
        sum_assured=1_000_000.0,
        interest_rate=0.05,
        qx=[0.001, 0.001, 0.002, 0.002, 0.003, 0.003, 0.004, 0.004, 0.005, 0.005],
        premium=0.0,   # will be solved
        expense_fixed=100.0,
        expense_pct=0.05,
    )

    print(SEPARATOR)
    print("PHASE 2 -- PREMIUM SOLVING (BISECTION METHOD)")
    print(SEPARATOR)

    result = solve_premium_bisection(base_policy)
    P_solved = result["premium"]

    print(f"\nSolved Premium:       {P_solved:>16.6f}")
    print(f"f(P) at solution:     {result['f_at_solution']:>16.2e}")
    print(f"Iterations:           {result['iterations']:>16d}")
    print(f"Converged:            {str(result['converged']):>16s}")
    print(f"Tolerance:            {result['tolerance']:>16.0e}")
    print(f"Final bracket:        [{result['bracket_final'][0]:.8f}, "
          f"{result['bracket_final'][1]:.8f}]")

    # =================================================================
    # VERIFICATION: Re-run projection with solved premium
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("VERIFICATION: PROJECTION WITH SOLVED PREMIUM")
    print(SEPARATOR)

    verified_policy = replace(base_policy, premium=P_solved)
    proj = project(verified_policy)
    summary = proj["summary"]

    print(f"\nTotal PV of Premiums:  {summary['total_pv_premium']:>16.6f}")
    print(f"Total PV of Claims:    {summary['total_pv_claim']:>16.6f}")
    print(f"Total PV of Expenses:  {summary['total_pv_expense']:>16.6f}")
    print(f"Total PV of Net CFs:   {summary['total_pv_net']:>16.6f}")

    pv_balance = abs(summary["total_pv_net"])
    balance_ok = pv_balance < 1e-4  # within 0.01 cent
    status = "PASS" if balance_ok else "FAIL"
    print(f"\n[{status}] PV balance check: |PV_net| = {pv_balance:.2e} "
          f"(threshold: 1e-4)")

    # =================================================================
    # PROJECTION TABLE WITH SOLVED PREMIUM
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("PROJECTION TABLE (SOLVED PREMIUM)")
    print(SEPARATOR)

    header = (
        f"{'t':>3}  {'Survival':>12}  {'Death Prob':>12}  "
        f"{'Premium CF':>12}  {'Claim CF':>14}  {'Expense CF':>12}  "
        f"{'Net CF':>14}  {'PV Net CF':>14}"
    )
    print(header)
    print("-" * len(header))

    for row in proj["rows"]:
        print(
            f"{row['t']:>3}  "
            f"{row['survival']:>12.8f}  "
            f"{row['death_prob']:>12.8f}  "
            f"{row['premium_cf']:>12.2f}  "
            f"{row['claim_cf']:>14.2f}  "
            f"{row['expense_cf']:>12.2f}  "
            f"{row['net_cf']:>14.2f}  "
            f"{row['pv_net_cf']:>14.6f}"
        )

    # =================================================================
    # SENSITIVITY ANALYSIS
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("SENSITIVITY ANALYSIS")
    print(SEPARATOR)

    all_passed = balance_ok
    sensitivities = []

    # --- Shock 1: Increase interest rate (5% -> 6%) ---
    shocked_policy = replace(base_policy, interest_rate=0.06)
    shocked_result = solve_premium_bisection(shocked_policy)
    P_shocked = shocked_result["premium"]
    direction = "DECREASE" if P_shocked < P_solved else "INCREASE"
    expected = "DECREASE"
    ok = direction == expected
    if not ok:
        all_passed = False
    sensitivities.append({
        "shock": "Interest rate 5% -> 6%",
        "base_P": P_solved,
        "shocked_P": P_shocked,
        "change": P_shocked - P_solved,
        "expected": expected,
        "actual": direction,
        "ok": ok,
    })

    # --- Shock 2: Increase mortality (all qx * 1.5) ---
    shocked_qx = [q * 1.5 for q in base_policy.qx]
    shocked_policy = replace(base_policy, qx=shocked_qx)
    shocked_result = solve_premium_bisection(shocked_policy)
    P_shocked = shocked_result["premium"]
    direction = "INCREASE" if P_shocked > P_solved else "DECREASE"
    expected = "INCREASE"
    ok = direction == expected
    if not ok:
        all_passed = False
    sensitivities.append({
        "shock": "Mortality * 1.5",
        "base_P": P_solved,
        "shocked_P": P_shocked,
        "change": P_shocked - P_solved,
        "expected": expected,
        "actual": direction,
        "ok": ok,
    })

    # --- Shock 3: Increase fixed expense (100 -> 200) ---
    shocked_policy = replace(base_policy, expense_fixed=200.0)
    shocked_result = solve_premium_bisection(shocked_policy)
    P_shocked = shocked_result["premium"]
    direction = "INCREASE" if P_shocked > P_solved else "DECREASE"
    expected = "INCREASE"
    ok = direction == expected
    if not ok:
        all_passed = False
    sensitivities.append({
        "shock": "Fixed expense 100 -> 200",
        "base_P": P_solved,
        "shocked_P": P_shocked,
        "change": P_shocked - P_solved,
        "expected": expected,
        "actual": direction,
        "ok": ok,
    })

    # --- Shock 4: Increase expense percentage (5% -> 10%) ---
    shocked_policy = replace(base_policy, expense_pct=0.10)
    shocked_result = solve_premium_bisection(shocked_policy)
    P_shocked = shocked_result["premium"]
    direction = "INCREASE" if P_shocked > P_solved else "DECREASE"
    expected = "INCREASE"
    ok = direction == expected
    if not ok:
        all_passed = False
    sensitivities.append({
        "shock": "Expense pct 5% -> 10%",
        "base_P": P_solved,
        "shocked_P": P_shocked,
        "change": P_shocked - P_solved,
        "expected": expected,
        "actual": direction,
        "ok": ok,
    })

    # --- Shock 5: Decrease term (10 -> 5 years) ---
    shocked_qx_short = base_policy.qx[:5]
    shocked_policy = replace(base_policy, term=5, qx=shocked_qx_short)
    shocked_result = solve_premium_bisection(shocked_policy)
    P_shocked = shocked_result["premium"]
    direction = "DECREASE" if P_shocked < P_solved else "INCREASE"
    expected = "DECREASE"
    ok = direction == expected
    if not ok:
        all_passed = False
    sensitivities.append({
        "shock": "Term 10 -> 5 years",
        "base_P": P_solved,
        "shocked_P": P_shocked,
        "change": P_shocked - P_solved,
        "expected": expected,
        "actual": direction,
        "ok": ok,
    })

    # --- Print sensitivity results ---
    print(f"\n{'Shock':<28} {'Base P':>12} {'Shocked P':>12} "
          f"{'Change':>12} {'Expected':>10} {'Actual':>10} {'Status':>8}")
    print("-" * 100)

    for s in sensitivities:
        status = "PASS" if s["ok"] else "FAIL"
        print(
            f"{s['shock']:<28} {s['base_P']:>12.4f} {s['shocked_P']:>12.4f} "
            f"{s['change']:>12.4f} {s['expected']:>10} {s['actual']:>10} "
            f"[{status}]"
        )

    print("-" * 100)

    if not all_passed:
        print(
            "\n*** WARNING: One or more sensitivity checks FAILED. ***"
            "\n*** The projection kernel may contain an error.      ***"
        )
    else:
        print(f"\n>>> ALL CHECKS PASSED <<<")

    return all_passed


if __name__ == "__main__":
    main()
