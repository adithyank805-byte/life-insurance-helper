import type { PricingResult, ProjectionSummary } from '../services/api';

interface Props {
    pricing: PricingResult | null;
    summary: ProjectionSummary | null;
    reserves: number[] | null;
}

function formatNum(n: number, decimals = 2): string {
    return n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function Card({ label, value, accent }: { label: string; value: string; accent: string }) {
    return (
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 hover:border-[#475569] transition-colors">
            <p className="text-xs font-medium uppercase tracking-wider text-[#64748b] mb-1">{label}</p>
            <p className={`text-xl font-semibold ${accent} font-mono`}>{value}</p>
        </div>
    );
}

export default function Dashboard({ pricing, summary, reserves }: Props) {
    if (!pricing || !summary) return null;

    const peakReserve = reserves ? Math.max(...reserves) : 0;
    const peakT = reserves ? reserves.indexOf(peakReserve) : 0;

    return (
        <div className="space-y-4">
            <h2 className="text-lg font-semibold text-[#f1f5f9] flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#10b981]"></span>
                Results Dashboard
            </h2>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <Card label="Solved Premium" value={formatNum(pricing.premium)} accent="text-[#10b981]" />
                <Card label="Iterations" value={`${pricing.iterations}`} accent="text-[#f1f5f9]" />
                <Card label="f(P)" value={pricing.f_at_solution.toExponential(2)} accent="text-[#94a3b8]" />
                <Card label="Converged" value={pricing.converged ? 'Yes' : 'No'} accent={pricing.converged ? 'text-[#10b981]' : 'text-[#f43f5e]'} />
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <Card label="EPV Premiums" value={formatNum(summary.total_pv_premium)} accent="text-[#3b82f6]" />
                <Card label="EPV Claims" value={formatNum(summary.total_pv_claim)} accent="text-[#f43f5e]" />
                <Card label="EPV Expenses" value={formatNum(summary.total_pv_expense)} accent="text-[#f59e0b]" />
                <Card label="EPV Net" value={summary.total_pv_net.toExponential(2)} accent="text-[#94a3b8]" />
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <Card label="Terminal In-Force" value={formatNum(summary.terminal_inforce, 6)} accent="text-[#8b5cf6]" />
                <Card label="Total Deaths" value={formatNum(summary.total_deaths, 6)} accent="text-[#f43f5e]" />
                <Card label="Total Lapses" value={formatNum(summary.total_lapses, 6)} accent="text-[#f59e0b]" />
                <Card label={"Peak Reserve (t=" + peakT + ")"} value={formatNum(peakReserve)} accent="text-[#10b981]" />
            </div>
        </div>
    );
}
