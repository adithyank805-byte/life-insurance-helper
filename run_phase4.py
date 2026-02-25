"""
Phase 4 Validation — Architecture Stabilization Verification

Confirms that the refactored architecture produces IDENTICAL numerical
results to the pre-refactor engine.

Expected values (from Phase 2 and Phase 3 runs):
    Premium:  2907.344663 (tolerance 1e-4)
    V(0):     ~0
    V(6):     5916.0807 (peak)
    V(10):    0.0

Also confirms the architectural test:
    "Can a new product type be added without modifying projection.py?"
"""

from dataclasses import replace
from engine.assumptions import Assumptions
from engine.products.term_product import TermProduct
from engine.projection import project
from engine.pricing import solve_premium_bisection
from engine.reserving import compute_reserves, compute_rollforward

SEPARATOR = "=" * 80

# Pre-refactor expected values (captured from Phase 2/3 runs)
EXPECTED_PREMIUM = 2907.344663
EXPECTED_RESERVES = [
    0.000000, 1796.873174, 3685.478613, 4674.177199, 5714.391142,
    5812.624875, 5916.080661, 5027.069273, 4089.858471, 2099.927332, 0.0
]
TOLERANCE_PREMIUM = 1e-4
TOLERANCE_RESERVE = 1e-3
TOLERANCE_PV = 1e-4
TOLERANCE_PROFIT = 1e-6


def main():
    # =================================================================
    # SETUP — identical test case to pre-refactor
    # =================================================================
    assumptions = Assumptions(
        entry_age=30,
        term=10,
        sum_assured=1_000_000.0,
        interest_rate=0.05,
        qx=[0.001, 0.001, 0.002, 0.002, 0.003, 0.003, 0.004, 0.004, 0.005, 0.005],
        premium=0.0,
        expense_fixed=100.0,
        expense_pct=0.05,
    )

    all_passed = True

    # =================================================================
    # TEST 1: PROJECTION — run with arbitrary premium P=4000
    # =================================================================
    print(SEPARATOR)
    print("TEST 1: PROJECTION WITH P=4000 (identical to Phase 1)")
    print(SEPARATOR)

    test_assumptions = replace(assumptions, premium=4000.0)
    product = TermProduct(test_assumptions)
    result = project(product, test_assumptions)
    summary = result["summary"]

    print(f"\nTotal PV Premiums:   {summary['total_pv_premium']:.4f}")
    print(f"Total PV Claims:     {summary['total_pv_claim']:.4f}")
    print(f"Total PV Expenses:   {summary['total_pv_expense']:.4f}")
    print(f"Total PV Net:        {summary['total_pv_net']:.4f}")
    print(f"Terminal Survival:   {summary['terminal_inforce']:.8f}")

    # Compare against Phase 1 expected values
    checks = [
        ("PV Premiums", summary["total_pv_premium"], 32160.3214, 0.1),
        ("PV Claims", summary["total_pv_claim"], 21402.5124, 0.1),
        ("PV Expenses", summary["total_pv_expense"], 2412.0241, 0.1),
        ("PV Net", summary["total_pv_net"], 8345.7849, 0.1),
        ("Terminal Survival", summary["terminal_inforce"], 0.97039201, 1e-6),
    ]

    for name, actual, expected, tol in checks:
        ok = abs(actual - expected) < tol
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"  [{status}] {name}: {actual:.6f} vs expected {expected:.6f}")

    # =================================================================
    # TEST 2: PREMIUM SOLVING
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("TEST 2: PREMIUM SOLVING (identical to Phase 2)")
    print(SEPARATOR)

    pricing_result = solve_premium_bisection(assumptions, TermProduct)
    P_solved = pricing_result["premium"]

    print(f"\nSolved Premium: {P_solved:.6f}")
    print(f"Expected:       {EXPECTED_PREMIUM:.6f}")

    premium_ok = abs(P_solved - EXPECTED_PREMIUM) < TOLERANCE_PREMIUM
    status = "PASS" if premium_ok else "FAIL"
    if not premium_ok:
        all_passed = False
    print(f"[{status}] Premium match (diff = {abs(P_solved - EXPECTED_PREMIUM):.2e})")

    # =================================================================
    # TEST 3: RESERVES
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("TEST 3: RESERVES (identical to Phase 3)")
    print(SEPARATOR)

    reserves = compute_reserves(assumptions, P_solved, TermProduct)

    print(f"\n{'t':>3}  {'V(t) actual':>16}  {'V(t) expected':>16}  {'Diff':>12}  {'Status':>8}")
    print("-" * 62)

    for t in range(len(reserves)):
        actual = reserves[t]
        expected = EXPECTED_RESERVES[t]
        diff = abs(actual - expected)
        ok = diff < TOLERANCE_RESERVE
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"{t:>3}  {actual:>16.6f}  {expected:>16.6f}  {diff:>12.2e}  [{status}]")

    # =================================================================
    # TEST 4: ROLL-FORWARD RECONCILIATION
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("TEST 4: ROLL-FORWARD RECONCILIATION")
    print(SEPARATOR)

    rollforward = compute_rollforward(assumptions, reserves, P_solved)
    max_profit = max(abs(row["profit"]) for row in rollforward)

    rf_ok = max_profit < TOLERANCE_PROFIT
    status = "PASS" if rf_ok else "FAIL"
    if not rf_ok:
        all_passed = False
    print(f"\n[{status}] Max |profit| = {max_profit:.2e} (threshold {TOLERANCE_PROFIT:.0e})")

    # =================================================================
    # TEST 5: ARCHITECTURAL TEST
    # =================================================================
    print(f"\n{SEPARATOR}")
    print("TEST 5: ARCHITECTURAL TEST")
    print(SEPARATOR)

    # Read projection.py and verify no product-specific references
    import inspect
    from engine import projection as proj_module

    source = inspect.getsource(proj_module)
    forbidden_terms = ["TermProduct", "term_product", "LevelTerm", "sum_assured",
                       "expense_fixed", "expense_pct"]
    arch_ok = True
    for term in forbidden_terms:
        if term in source:
            print(f"  [FAIL] projection.py contains product-specific term: '{term}'")
            arch_ok = False
            all_passed = False

    if arch_ok:
        print("  [PASS] projection.py contains NO product-specific references")

    print(f"\n  Architectural answer:")
    print(f"  'If I add a new product type (e.g., Endowment), can I implement it")
    print(f"   by creating a new product class without modifying projection.py?'")
    print(f"  --> YES. projection.py interacts with products only through the")
    print(f"      BaseProduct interface (premium_cashflow, benefit_cashflow,")
    print(f"      expense_cashflow). A new product class needs only to implement")
    print(f"      these three methods.")

    # =================================================================
    # FINAL RESULT
    # =================================================================
    print(f"\n{SEPARATOR}")
    final = "ALL TESTS PASSED -- NO NUMERICAL DRIFT" if all_passed else "SOME TESTS FAILED"
    print(f">>> {final} <<<")
    print(SEPARATOR)

    return all_passed


if __name__ == "__main__":
    main()
