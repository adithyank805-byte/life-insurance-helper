import type { RollforwardRow } from '../services/api';

interface Props {
    reserves: number[] | null;
    rollforward: RollforwardRow[] | null;
}

function fmt(n: number, d = 2): string {
    return n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
}

export default function ReserveSchedule({ reserves, rollforward }: Props) {
    if (!reserves || !rollforward) return null;

    return (
        <div className="space-y-4">
            {/* Reserve Schedule */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-[#334155]">
                    <h2 className="text-lg font-semibold text-[#f1f5f9] flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-[#10b981]"></span>
                        Reserve Schedule
                    </h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-[#0f172a]">
                            <tr>
                                <th className="px-4 py-2 text-xs font-medium uppercase text-[#64748b] text-center">t</th>
                                <th className="px-4 py-2 text-xs font-medium uppercase text-[#64748b] text-right">V(t)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reserves.map((v, t) => (
                                <tr key={t} className={`border-t border-[#1e293b] ${t % 2 === 0 ? 'bg-[#1e293b]' : 'bg-[#1a2537]'}`}>
                                    <td className="px-4 py-2 text-center text-[#94a3b8]">{t}</td>
                                    <td className="px-4 py-2 text-right font-mono text-[#10b981]">{fmt(v, 4)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Roll-Forward Reconciliation */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-[#334155]">
                    <h2 className="text-lg font-semibold text-[#f1f5f9] flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-[#f59e0b]"></span>
                        Roll-Forward Reconciliation
                    </h2>
                </div>
                <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-[#0f172a]">
                            <tr>
                                {['t', 'Opening V(t)', 'Premium', 'Expense', 'BOY Amount', 'Interest', 'Claims', 'Closing pV', 'Profit'].map(h => (
                                    <th key={h} className="px-3 py-2 text-xs font-medium uppercase tracking-wider text-[#64748b] text-right whitespace-nowrap first:text-center">
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {rollforward.map((row, i) => {
                                const profitColor = Math.abs(row.profit) < 1e-4 ? 'text-[#10b981]' : 'text-[#f43f5e]';
                                return (
                                    <tr key={row.t} className={`border-t border-[#1e293b] ${i % 2 === 0 ? 'bg-[#1e293b]' : 'bg-[#1a2537]'}`}>
                                        <td className="px-3 py-2 text-center text-[#94a3b8]">{row.t}</td>
                                        <td className="px-3 py-2 text-right font-mono text-[#f1f5f9]">{fmt(row.opening_reserve, 4)}</td>
                                        <td className="px-3 py-2 text-right font-mono text-[#10b981]">{fmt(row.premium)}</td>
                                        <td className="px-3 py-2 text-right font-mono text-[#f59e0b]">{fmt(row.expense)}</td>
                                        <td className="px-3 py-2 text-right font-mono text-[#3b82f6]">{fmt(row.boy_amount, 4)}</td>
                                        <td className="px-3 py-2 text-right font-mono text-[#8b5cf6]">{fmt(row.investment_income, 4)}</td>
                                        <td className="px-3 py-2 text-right font-mono text-[#f43f5e]">{fmt(row.claims)}</td>
                                        <td className="px-3 py-2 text-right font-mono text-[#f1f5f9]">{fmt(row.closing_reserve_exp, 4)}</td>
                                        <td className={`px-3 py-2 text-right font-mono ${profitColor}`}>{row.profit.toExponential(2)}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
