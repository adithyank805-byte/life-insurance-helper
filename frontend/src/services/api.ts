import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export interface AssumptionsInput {
    entry_age: number;
    term: number;
    sum_assured: number;
    interest_rate: number;
    qx: number[];
    premium: number;
    expense_fixed: number;
    expense_pct: number;
    lapse_rates: number[] | null;
    product_type: string;
}

export interface ProjectionRow {
    t: number;
    survival: number;
    death_prob: number;
    lapse_count: number;
    premium_cf: number;
    claim_cf: number;
    expense_cf: number;
    net_cf: number;
    discount_boy: number;
    discount_eoy: number;
    pv_premium: number;
    pv_claim: number;
    pv_expense: number;
    pv_net_cf: number;
}

export interface ProjectionSummary {
    total_pv_premium: number;
    total_pv_claim: number;
    total_pv_expense: number;
    total_pv_net: number;
    terminal_inforce: number;
    total_deaths: number;
    total_lapses: number;
}

export interface ProjectionResponse {
    rows: ProjectionRow[];
    summary: ProjectionSummary;
}

export interface PricingResult {
    premium: number;
    f_at_solution: number;
    iterations: number;
    converged: boolean;
    tolerance: number;
}

export interface PricingResponse {
    pricing: PricingResult;
    projection: ProjectionResponse;
}

export interface RollforwardRow {
    t: number;
    opening_reserve: number;
    premium: number;
    expense: number;
    boy_amount: number;
    investment_income: number;
    claims: number;
    closing_reserve_exp: number;
    profit: number;
}

export interface ReserveResponse {
    reserves: number[];
    rollforward: RollforwardRow[];
    solved_premium: number;
    projection: ProjectionResponse;
}

export async function runPricing(input: AssumptionsInput): Promise<PricingResponse> {
    const res = await axios.post<PricingResponse>(`${API_BASE}/pricing`, input);
    return res.data;
}

export async function runReserve(input: AssumptionsInput): Promise<ReserveResponse> {
    const res = await axios.post<ReserveResponse>(`${API_BASE}/reserve`, input);
    return res.data;
}

export async function runProjection(input: AssumptionsInput): Promise<ProjectionResponse> {
    const res = await axios.post<ProjectionResponse>(`${API_BASE}/projection`, input);
    return res.data;
}
