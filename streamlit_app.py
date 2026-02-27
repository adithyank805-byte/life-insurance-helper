"""
Streamlit App — Life Insurance Actuarial Engine

Premium web interface for deterministic actuarial projections,
pricing, and reserving. Wraps the engine modules directly —
ZERO actuarial formulas in this file.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import replace

from engine.assumptions import Assumptions
from engine.products.term_product import TermProduct
from engine.products.endowment_product import EndowmentProduct
from engine.projection import project
from engine.pricing import solve_premium_bisection
from engine.reserving import compute_reserves, compute_rollforward


# ─────────────────────────────────────────────────────────────
# Page Config & Custom Styling
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Life Insurance Actuarial Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Hero header */
.hero-header {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    color: white;
    box-shadow: 0 8px 32px rgba(48, 43, 99, 0.3);
}

.hero-header h1 {
    margin: 0;
    font-weight: 700;
    font-size: 2rem;
    letter-spacing: -0.5px;
}

.hero-header p {
    margin: 0.5rem 0 0;
    opacity: 0.85;
    font-size: 1rem;
    font-weight: 300;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.metric-card .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #8b8fa3;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.metric-card .value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #e0e0ff;
}

.metric-card .value.green { color: #4ade80; }
.metric-card .value.blue { color: #60a5fa; }
.metric-card .value.amber { color: #fbbf24; }
.metric-card .value.rose { color: #fb7185; }
.metric-card .value.purple { color: #c084fc; }

/* Section dividers */
.section-divider {
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    margin: 1.5rem 0;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 100%);
}

[data-testid="stSidebar"] .stMarkdown h2 {
    color: #e0e0ff;
    font-weight: 600;
    font-size: 1.1rem;
}

/* Dataframe styling */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}

/* Tab styling override */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 10px 24px;
    font-weight: 500;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Plotly Theme
# ─────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13),
    margin=dict(l=40, r=40, t=50, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
)

COLORS = {
    "premium": "#60a5fa",
    "claim": "#fb7185",
    "expense": "#fbbf24",
    "net": "#4ade80",
    "reserve": "#c084fc",
    "survival": "#38bdf8",
    "death": "#f87171",
    "lapse": "#facc15",
}


# ─────────────────────────────────────────────────────────────
# Helper: Generate sample mortality rates
# ─────────────────────────────────────────────────────────────

def generate_sample_qx(entry_age: int, term: int) -> list[float]:
    """Generate illustrative mortality rates using a Makeham-like formula."""
    qx = []
    for t in range(term):
        age = entry_age + t
        # Simplified Makeham: q(x) = 0.0005 + 0.00005 * 10^(0.04 * x)
        q = 0.0005 + 0.00005 * (10 ** (0.04 * age))
        q = min(q, 0.999)  # cap
        qx.append(round(q, 6))
    return qx


# ─────────────────────────────────────────────────────────────
# Helper: Render metric card
# ─────────────────────────────────────────────────────────────

def metric_card(label: str, value: str, color: str = ""):
    color_class = f" {color}" if color else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value{color_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Helper: Product class mapping
# ─────────────────────────────────────────────────────────────

PRODUCT_MAP = {
    "Term Life": TermProduct,
    "Endowment": EndowmentProduct,
}


# ─────────────────────────────────────────────────────────────
# Sidebar — Input Controls
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Policy Assumptions")

    product_type = st.selectbox(
        "Product Type",
        options=list(PRODUCT_MAP.keys()),
        index=0,
        help="Term Life: death benefit only. Endowment: death + maturity benefit.",
    )

    st.markdown("---")
    st.markdown("#### 👤 Policyholder")
    entry_age = st.slider("Entry Age", 18, 80, 30, help="Age at policy inception")
    term = st.slider("Policy Term (years)", 1, 50, 10, help="Duration of coverage")

    st.markdown("---")
    st.markdown("#### 💰 Financial")
    sum_assured = st.number_input(
        "Sum Assured (₹)",
        min_value=10_000.0,
        max_value=100_000_000.0,
        value=100_000.0,
        step=10_000.0,
        format="%.0f",
    )
    interest_rate = st.slider(
        "Interest Rate (%)",
        0.5, 15.0, 5.0, step=0.25,
        help="Annual discount rate",
    ) / 100.0

    st.markdown("---")
    st.markdown("#### 📊 Expenses")
    expense_fixed = st.number_input(
        "Fixed Annual Expense (₹)",
        min_value=0.0,
        max_value=100_000.0,
        value=100.0,
        step=50.0,
        format="%.0f",
    )
    expense_pct = st.slider(
        "Expense % of Premium",
        0.0, 50.0, 5.0, step=0.5,
        help="Loading as percentage of premium",
    ) / 100.0

    st.markdown("---")
    st.markdown("#### 📉 Lapse Rates")
    enable_lapses = st.toggle("Enable Lapse Modeling", value=False)
    lapse_rates = None
    if enable_lapses:
        lapse_style = st.radio(
            "Lapse Pattern",
            ["Flat Rate", "Decreasing (Select & Ultimate)"],
            horizontal=True,
        )
        if lapse_style == "Flat Rate":
            flat_lapse = st.slider("Annual Lapse Rate (%)", 0.0, 30.0, 5.0, step=0.5) / 100.0
            lapse_rates = [flat_lapse] * term
        else:
            yr1_lapse = st.slider("Year 1 Lapse (%)", 0.0, 40.0, 15.0, step=1.0) / 100.0
            ult_lapse = st.slider("Ultimate Lapse (%)", 0.0, 20.0, 3.0, step=0.5) / 100.0
            # Linear decrease from year 1 to ultimate over 5 years
            lapse_rates = []
            for t in range(term):
                if t < 5:
                    l = yr1_lapse - (yr1_lapse - ult_lapse) * t / 5
                else:
                    l = ult_lapse
                lapse_rates.append(round(l, 4))

    st.markdown("---")
    st.markdown("#### 💀 Mortality")
    qx_mode = st.radio(
        "Mortality Source",
        ["Auto-Generate (Makeham)", "Manual Entry"],
        horizontal=True,
    )
    if qx_mode == "Auto-Generate (Makeham)":
        qx = generate_sample_qx(entry_age, term)
        with st.expander("View Generated qx Vector"):
            st.dataframe(
                pd.DataFrame({"Year": range(term), "Age": [entry_age + t for t in range(term)], "qx": qx}),
                use_container_width=True,
                hide_index=True,
            )
    else:
        qx_input = st.text_area(
            "Enter qx values (comma-separated)",
            value=", ".join(str(q) for q in generate_sample_qx(entry_age, term)),
            height=120,
        )
        try:
            qx = [float(x.strip()) for x in qx_input.split(",") if x.strip()]
            if len(qx) != term:
                st.error(f"Expected {term} values, got {len(qx)}")
                st.stop()
        except ValueError:
            st.error("Invalid qx values. Please enter comma-separated numbers.")
            st.stop()


# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="hero-header">
        <h1>🛡️ Life Insurance Actuarial Engine</h1>
        <p>Deterministic projection, premium pricing, and reserve computation</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# Build Assumptions
# ─────────────────────────────────────────────────────────────

product_class = PRODUCT_MAP[product_type]


# ─────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────

tab_projection, tab_pricing, tab_reserves = st.tabs([
    "📈 Projection",
    "💲 Premium Pricing",
    "📊 Reserves & Roll-Forward",
])


# ═══════════════════════════════════════════════════════════════
# TAB 1: PROJECTION
# ═══════════════════════════════════════════════════════════════

with tab_projection:
    st.markdown("### Run Projection with Given Premium")
    premium_input = st.number_input(
        "Annual Premium (₹)",
        min_value=0.0,
        max_value=sum_assured,
        value=min(3000.0, sum_assured),
        step=100.0,
        format="%.2f",
        key="proj_premium",
    )

    if st.button("▶️ Run Projection", key="btn_projection", type="primary", use_container_width=True):
        try:
            assumptions = Assumptions(
                entry_age=entry_age, term=term, sum_assured=sum_assured,
                interest_rate=interest_rate, qx=qx, premium=premium_input,
                expense_fixed=expense_fixed, expense_pct=expense_pct,
                lapse_rates=lapse_rates,
            )
            product = product_class(assumptions)
            result = project(product, assumptions)

            summary = result["summary"]
            rows = result["rows"]

            # ── Summary Metrics ──
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                metric_card("EPV Premiums", f"₹{summary['total_pv_premium']:,.2f}", "blue")
            with c2:
                metric_card("EPV Claims", f"₹{summary['total_pv_claim']:,.2f}", "rose")
            with c3:
                metric_card("EPV Expenses", f"₹{summary['total_pv_expense']:,.2f}", "amber")
            with c4:
                metric_card("EPV Net", f"₹{summary['total_pv_net']:,.2f}",
                            "green" if summary['total_pv_net'] >= 0 else "rose")

            c5, c6, c7 = st.columns(3)
            with c5:
                metric_card("Terminal In-Force", f"{summary['terminal_inforce']:.4f}", "purple")
            with c6:
                metric_card("Total Deaths", f"{summary['total_deaths']:.4f}", "rose")
            with c7:
                metric_card("Total Lapses", f"{summary['total_lapses']:.4f}", "amber")

            # ── Charts ──
            st.markdown("---")
            df = pd.DataFrame(rows)

            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                fig_cf = go.Figure()
                fig_cf.add_trace(go.Bar(x=df["t"], y=df["premium_cf"], name="Premium", marker_color=COLORS["premium"]))
                fig_cf.add_trace(go.Bar(x=df["t"], y=[-c for c in df["claim_cf"]], name="Claims (neg)", marker_color=COLORS["claim"]))
                fig_cf.add_trace(go.Bar(x=df["t"], y=[-e for e in df["expense_cf"]], name="Expenses (neg)", marker_color=COLORS["expense"]))
                fig_cf.update_layout(**PLOTLY_LAYOUT, title="Cashflows by Year", barmode="group",
                                     xaxis_title="Year", yaxis_title="Amount (₹)")
                st.plotly_chart(fig_cf, use_container_width=True)

            with col_chart2:
                fig_surv = go.Figure()
                fig_surv.add_trace(go.Scatter(x=df["t"], y=df["survival"], mode="lines+markers",
                                              name="In-Force", line=dict(color=COLORS["survival"], width=3)))
                fig_surv.add_trace(go.Bar(x=df["t"], y=df["death_prob"], name="Deaths", marker_color=COLORS["death"], opacity=0.6))
                if lapse_rates:
                    fig_surv.add_trace(go.Bar(x=df["t"], y=df["lapse_count"], name="Lapses", marker_color=COLORS["lapse"], opacity=0.6))
                fig_surv.update_layout(**PLOTLY_LAYOUT, title="Survivorship & Decrements",
                                       xaxis_title="Year", yaxis_title="Probability")
                st.plotly_chart(fig_surv, use_container_width=True)

            # ── PV Waterfall ──
            fig_pv = go.Figure(go.Waterfall(
                name="PV Waterfall",
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=["EPV Premium", "EPV Claims", "EPV Expenses", "EPV Net"],
                y=[summary["total_pv_premium"], -summary["total_pv_claim"],
                   -summary["total_pv_expense"], summary["total_pv_net"]],
                connector=dict(line=dict(color="rgba(255,255,255,0.2)")),
                increasing=dict(marker_color=COLORS["premium"]),
                decreasing=dict(marker_color=COLORS["claim"]),
                totals=dict(marker_color=COLORS["net"] if summary["total_pv_net"] >= 0 else COLORS["claim"]),
            ))
            fig_pv.update_layout(**PLOTLY_LAYOUT, title="Present Value Waterfall", yaxis_title="Amount (₹)")
            st.plotly_chart(fig_pv, use_container_width=True)

            # ── Data Table ──
            with st.expander("📋 Full Projection Table", expanded=False):
                display_df = df.copy()
                display_df.columns = [
                    "Year", "Survival", "Death Prob", "Lapse Count",
                    "Premium CF", "Claim CF", "Expense CF", "Net CF",
                    "Disc BOY", "Disc EOY",
                    "PV Premium", "PV Claim", "PV Expense", "PV Net CF",
                ]
                st.dataframe(display_df, use_container_width=True, hide_index=True)

        except (ValueError, RuntimeError) as e:
            st.error(f"❌ {e}")


# ═══════════════════════════════════════════════════════════════
# TAB 2: PRICING
# ═══════════════════════════════════════════════════════════════

with tab_pricing:
    st.markdown("### Solve for Breakeven Premium")
    st.info("The engine uses bisection root-finding to solve for the premium that makes EPV(Net) = 0.", icon="ℹ️")

    if st.button("▶️ Solve Premium", key="btn_pricing", type="primary", use_container_width=True):
        try:
            assumptions = Assumptions(
                entry_age=entry_age, term=term, sum_assured=sum_assured,
                interest_rate=interest_rate, qx=qx, premium=0.0,
                expense_fixed=expense_fixed, expense_pct=expense_pct,
                lapse_rates=lapse_rates,
            )
            pricing_result = solve_premium_bisection(assumptions, product_class)
            solved_premium = pricing_result["premium"]

            # Re-run projection with solved premium
            priced_assumptions = replace(assumptions, premium=solved_premium)
            product = product_class(priced_assumptions)
            proj_result = project(product, priced_assumptions)
            summary = proj_result["summary"]

            # ── Pricing Result ──
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                metric_card("Solved Premium", f"₹{solved_premium:,.2f}", "green")
            with c2:
                metric_card("Converged", "✅ Yes" if pricing_result["converged"] else "❌ No",
                            "green" if pricing_result["converged"] else "rose")
            with c3:
                metric_card("Iterations", str(pricing_result["iterations"]), "blue")
            with c4:
                metric_card("f(P) at Solution", f"{pricing_result['f_at_solution']:.2e}", "purple")

            # ── Summary Metrics ──
            st.markdown("---")
            c5, c6, c7, c8 = st.columns(4)
            with c5:
                metric_card("EPV Premiums", f"₹{summary['total_pv_premium']:,.2f}", "blue")
            with c6:
                metric_card("EPV Claims", f"₹{summary['total_pv_claim']:,.2f}", "rose")
            with c7:
                metric_card("EPV Expenses", f"₹{summary['total_pv_expense']:,.2f}", "amber")
            with c8:
                metric_card("EPV Net", f"₹{summary['total_pv_net']:,.2f}",
                            "green" if abs(summary['total_pv_net']) < 1 else "amber")

            # ── Premium Sensitivity ──
            st.markdown("---")
            st.markdown("#### Premium Sensitivity Analysis")
            deltas = [-20, -10, -5, 0, 5, 10, 20]
            sens_data = []
            for d in deltas:
                test_p = solved_premium * (1 + d / 100)
                test_a = replace(assumptions, premium=test_p)
                test_prod = product_class(test_a)
                test_res = project(test_prod, test_a)
                sens_data.append({
                    "Premium Δ (%)": f"{d:+d}%",
                    "Premium (₹)": round(test_p, 2),
                    "EPV Net (₹)": round(test_res["summary"]["total_pv_net"], 2),
                })

            sens_df = pd.DataFrame(sens_data)
            fig_sens = go.Figure()
            fig_sens.add_trace(go.Scatter(
                x=[d for d in deltas],
                y=[s["EPV Net (₹)"] for s in sens_data],
                mode="lines+markers",
                line=dict(color=COLORS["net"], width=3),
                marker=dict(size=10),
                name="EPV Net",
            ))
            fig_sens.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
            fig_sens.update_layout(**PLOTLY_LAYOUT, title="EPV Net vs Premium Change",
                                    xaxis_title="Premium Change (%)", yaxis_title="EPV Net (₹)")
            st.plotly_chart(fig_sens, use_container_width=True)

            st.dataframe(sens_df, use_container_width=True, hide_index=True)

            # ── Projection Table ──
            with st.expander("📋 Full Projection Table (at solved premium)", expanded=False):
                df = pd.DataFrame(proj_result["rows"])
                df.columns = [
                    "Year", "Survival", "Death Prob", "Lapse Count",
                    "Premium CF", "Claim CF", "Expense CF", "Net CF",
                    "Disc BOY", "Disc EOY",
                    "PV Premium", "PV Claim", "PV Expense", "PV Net CF",
                ]
                st.dataframe(df, use_container_width=True, hide_index=True)

        except (ValueError, RuntimeError) as e:
            st.error(f"❌ {e}")


# ═══════════════════════════════════════════════════════════════
# TAB 3: RESERVES & ROLL-FORWARD
# ═══════════════════════════════════════════════════════════════

with tab_reserves:
    st.markdown("### Prospective Gross Premium Reserves")
    st.info("Reserves are computed by running sub-projections at each duration. Roll-forward verifies V(t) identity.", icon="ℹ️")

    if st.button("▶️ Compute Reserves", key="btn_reserves", type="primary", use_container_width=True):
        try:
            assumptions = Assumptions(
                entry_age=entry_age, term=term, sum_assured=sum_assured,
                interest_rate=interest_rate, qx=qx, premium=0.0,
                expense_fixed=expense_fixed, expense_pct=expense_pct,
                lapse_rates=lapse_rates,
            )
            # Solve premium
            pricing_result = solve_premium_bisection(assumptions, product_class)
            solved_premium = pricing_result["premium"]

            # Reserves
            reserves = compute_reserves(assumptions, solved_premium, product_class)

            # Roll-forward
            rollforward = compute_rollforward(assumptions, reserves, solved_premium)

            # ── Summary Metrics ──
            st.markdown("---")
            max_reserve = max(reserves)
            max_reserve_t = reserves.index(max_reserve)
            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card("Solved Premium", f"₹{solved_premium:,.2f}", "green")
            with c2:
                metric_card("Peak Reserve", f"₹{max_reserve:,.2f}", "purple")
            with c3:
                metric_card("Peak at Year", str(max_reserve_t), "blue")

            # ── Reserve Curve ──
            st.markdown("---")
            fig_res = go.Figure()
            fig_res.add_trace(go.Scatter(
                x=list(range(len(reserves))),
                y=reserves,
                mode="lines+markers",
                name="Reserve V(t)",
                line=dict(color=COLORS["reserve"], width=3),
                marker=dict(size=8),
                fill="tozeroy",
                fillcolor="rgba(192, 132, 252, 0.15)",
            ))
            fig_res.update_layout(**PLOTLY_LAYOUT, title="Reserve Curve V(t)",
                                   xaxis_title="Duration (t)", yaxis_title="Reserve (₹)")
            st.plotly_chart(fig_res, use_container_width=True)

            # ── Roll-Forward Table ──
            st.markdown("---")
            st.markdown("#### Roll-Forward Reconciliation")
            rf_df = pd.DataFrame(rollforward)
            rf_df.columns = [
                "Year", "Opening Reserve", "Premium", "Expense",
                "BOY Amount", "Investment Income", "Claims",
                "Closing Reserve (Exp)", "Profit",
            ]

            # Profit should be ~0, highlight if not
            max_profit_err = rf_df["Profit"].abs().max()
            if max_profit_err < 0.01:
                st.success(f"✅ Roll-forward validated — max profit deviation: {max_profit_err:.2e}", icon="✅")
            else:
                st.warning(f"⚠️ Roll-forward profit deviation: {max_profit_err:.4f}", icon="⚠️")

            # ── Roll-forward chart ──
            col1, col2 = st.columns(2)
            with col1:
                fig_rf = go.Figure()
                fig_rf.add_trace(go.Bar(x=rf_df["Year"], y=rf_df["Premium"], name="Premium", marker_color=COLORS["premium"]))
                fig_rf.add_trace(go.Bar(x=rf_df["Year"], y=rf_df["Investment Income"], name="Investment", marker_color=COLORS["net"]))
                fig_rf.add_trace(go.Bar(x=rf_df["Year"], y=[-c for c in rf_df["Claims"]], name="Claims (neg)", marker_color=COLORS["claim"]))
                fig_rf.add_trace(go.Bar(x=rf_df["Year"], y=[-e for e in rf_df["Expense"]], name="Expense (neg)", marker_color=COLORS["expense"]))
                fig_rf.update_layout(**PLOTLY_LAYOUT, title="Roll-Forward Components", barmode="group",
                                     xaxis_title="Year", yaxis_title="Amount (₹)")
                st.plotly_chart(fig_rf, use_container_width=True)

            with col2:
                fig_profit = go.Figure()
                fig_profit.add_trace(go.Scatter(
                    x=rf_df["Year"], y=rf_df["Profit"],
                    mode="lines+markers",
                    name="Profit",
                    line=dict(color=COLORS["net"], width=2),
                    marker=dict(size=6),
                ))
                fig_profit.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
                fig_profit.update_layout(**PLOTLY_LAYOUT, title="Profit per Year (should be ~0)",
                                          xaxis_title="Year", yaxis_title="Profit (₹)")
                st.plotly_chart(fig_profit, use_container_width=True)

            # ── Data Tables ──
            with st.expander("📋 Reserve Schedule", expanded=False):
                res_df = pd.DataFrame({
                    "Duration (t)": range(len(reserves)),
                    "Reserve V(t) (₹)": [round(r, 4) for r in reserves],
                })
                st.dataframe(res_df, use_container_width=True, hide_index=True)

            with st.expander("📋 Full Roll-Forward Table", expanded=False):
                st.dataframe(rf_df, use_container_width=True, hide_index=True)

        except (ValueError, RuntimeError) as e:
            st.error(f"❌ {e}")


# ─────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 1rem; opacity: 0.5; font-size: 0.8rem;">
        Life Insurance Actuarial Engine • Deterministic Projection, Pricing & Reserving<br>
        Built with Streamlit • Engine: Product-agnostic cashflow projection kernel
    </div>
    """,
    unsafe_allow_html=True,
)
