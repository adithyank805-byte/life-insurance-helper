import type { ProjectionRow } from '../services/api';

interface Props {
    rows: ProjectionRow[] | null;
}

function fmt(n: number, d = 2): string {
    return n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
}

export default function ProjectionTable({ rows }: Props) {
    if (!rows || rows.length === 0) return null;

    const headers = [
        { key: 't', label: 't', align: 'center' as const },
        { key: 'survival', label: 'In-Force', align: 'right' as const },
        { key: 'death_prob', label: 'Deaths', align: 'right' as const },
        { key: 'lapse_count', label: 'Lapses', align: 'right' as const },
        { key: 'premium_cf', label: 'Premium CF', align: 'right' as const },
        { key: 'claim_cf', label: 'Claim CF', align: 'right' as const },
        { key: 'expense_cf', label: 'Expense CF', align: 'right' as const },
        { key: 'net_cf', label: 'Net CF', align: 'right' as const },
        { key: 'pv_premium', label: 'PV Premium', align: 'right' as const },
        { key: 'pv_claim', label: 'PV Claim', align: 'right' as const },
        { key: 'pv_expense', label: 'PV Expense', align: 'right' as const },
        { key: 'pv_net_cf', label: 'PV Net', align: 'right' as const },
    ];

    return (
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-[#334155]">
                <h2 className="text-lg font-semibold text-[#f1f5f9] flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#3b82f6]"></span>
                    Projection Table
                </h2>
            </div>
            <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-[#0f172a]">
                        <tr>
                            {headers.map(h => (
                                <th key={h.key} className={`px-3 py-2 text-xs font-medium uppercase tracking-wider text-[#64748b] text-${h.align} whitespace-nowrap`}>
                                    {h.label}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row, i) => (
                            <tr key={row.t} className={`border-t border-[#1e293b] ${i % 2 === 0 ? 'bg-[#1e293b]' : 'bg-[#1a2537]'} hover:bg-[#334155]/30 transition-colors`}>
                                <td className="px-3 py-2 text-center font-medium text-[#94a3b8]">{row.t}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#8b5cf6]">{fmt(row.survival, 6)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#f43f5e]">{fmt(row.death_prob, 6)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#f59e0b]">{fmt(row.lapse_count, 6)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#10b981]">{fmt(row.premium_cf)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#f43f5e]">{fmt(row.claim_cf)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#f59e0b]">{fmt(row.expense_cf)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#f1f5f9]">{fmt(row.net_cf)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#3b82f6]">{fmt(row.pv_premium, 4)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#f43f5e]">{fmt(row.pv_claim, 4)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#f59e0b]">{fmt(row.pv_expense, 4)}</td>
                                <td className="px-3 py-2 text-right font-mono text-[#f1f5f9]">{fmt(row.pv_net_cf, 4)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
