import React, { useState } from 'react';
import type { AssumptionsInput } from '../services/api';

interface Props {
    onSubmit: (input: AssumptionsInput) => void;
    loading: boolean;
}

const DEFAULT_QX = [0.001, 0.001, 0.002, 0.002, 0.003, 0.003, 0.004, 0.004, 0.005, 0.005];
const DEFAULT_LAPSE = [0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.02, 0.02, 0.01, 0.01];

export default function InputForm({ onSubmit, loading }: Props) {
    const [entryAge, setEntryAge] = useState(30);
    const [term, setTerm] = useState(10);
    const [sumAssured, setSumAssured] = useState(1_000_000);
    const [interestRate, setInterestRate] = useState(0.05);
    const [expenseFixed, setExpenseFixed] = useState(100);
    const [expensePct, setExpensePct] = useState(0.05);
    const [productType, setProductType] = useState('term');
    const [qxStr, setQxStr] = useState(DEFAULT_QX.join(', '));
    const [enableLapse, setEnableLapse] = useState(false);
    const [lapseStr, setLapseStr] = useState(DEFAULT_LAPSE.join(', '));
    const [error, setError] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        const qx = qxStr.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
        if (qx.length !== term) {
            setError(`Mortality vector has ${qx.length} values, expected ${term}`);
            return;
        }

        let lapseRates: number[] | null = null;
        if (enableLapse) {
            lapseRates = lapseStr.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
            if (lapseRates.length !== term) {
                setError(`Lapse vector has ${lapseRates.length} values, expected ${term}`);
                return;
            }
        }

        onSubmit({
            entry_age: entryAge,
            term,
            sum_assured: sumAssured,
            interest_rate: interestRate,
            qx,
            premium: 0,
            expense_fixed: expenseFixed,
            expense_pct: expensePct,
            lapse_rates: lapseRates,
            product_type: productType,
        });
    };

    const fieldClass = "w-full bg-[#0f172a] border border-[#334155] rounded-lg px-3 py-2 text-[#f1f5f9] focus:outline-none focus:border-[#3b82f6] focus:ring-1 focus:ring-[#3b82f6] transition-colors text-sm";
    const labelClass = "block text-xs font-medium text-[#94a3b8] mb-1 uppercase tracking-wider";

    return (
        <form onSubmit={handleSubmit} className="bg-[#1e293b] rounded-xl border border-[#334155] p-6">
            <h2 className="text-lg font-semibold text-[#f1f5f9] mb-5 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#3b82f6]"></span>
                Assumptions
            </h2>

            <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <label className={labelClass}>Product Type</label>
                    <select value={productType} onChange={e => setProductType(e.target.value)} className={fieldClass}>
                        <option value="term">Level Term</option>
                        <option value="endowment">Endowment</option>
                    </select>
                </div>
                <div>
                    <label className={labelClass}>Entry Age</label>
                    <input type="number" value={entryAge} onChange={e => setEntryAge(+e.target.value)} min={0} max={120} className={fieldClass} />
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <label className={labelClass}>Term (years)</label>
                    <input type="number" value={term} onChange={e => setTerm(+e.target.value)} min={1} max={100} className={fieldClass} />
                </div>
                <div>
                    <label className={labelClass}>Sum Assured</label>
                    <input type="number" value={sumAssured} onChange={e => setSumAssured(+e.target.value)} min={1} className={fieldClass} />
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                    <label className={labelClass}>Interest Rate</label>
                    <input type="number" value={interestRate} onChange={e => setInterestRate(+e.target.value)} step={0.005} className={fieldClass} />
                </div>
                <div>
                    <label className={labelClass}>Fixed Expense</label>
                    <input type="number" value={expenseFixed} onChange={e => setExpenseFixed(+e.target.value)} min={0} className={fieldClass} />
                </div>
                <div>
                    <label className={labelClass}>Expense %</label>
                    <input type="number" value={expensePct} onChange={e => setExpensePct(+e.target.value)} step={0.01} min={0} max={0.99} className={fieldClass} />
                </div>
            </div>

            <div className="mb-4">
                <label className={labelClass}>Mortality Vector (qx, comma-separated)</label>
                <textarea value={qxStr} onChange={e => setQxStr(e.target.value)} rows={2}
                    className={`${fieldClass} font-mono text-xs resize-none`} />
            </div>

            <div className="mb-4">
                <label className="flex items-center gap-2 cursor-pointer text-sm text-[#94a3b8] mb-2">
                    <input type="checkbox" checked={enableLapse} onChange={e => setEnableLapse(e.target.checked)}
                        className="w-4 h-4 rounded border-[#334155] bg-[#0f172a] text-[#3b82f6] focus:ring-[#3b82f6]" />
                    Enable Lapse Rates
                </label>
                {enableLapse && (
                    <textarea value={lapseStr} onChange={e => setLapseStr(e.target.value)} rows={2}
                        className={`${fieldClass} font-mono text-xs resize-none`}
                        placeholder="Lapse rates, comma-separated" />
                )}
            </div>

            {error && (
                <div className="bg-[#f43f5e]/10 border border-[#f43f5e]/30 text-[#f43f5e] text-sm rounded-lg px-3 py-2 mb-4">
                    {error}
                </div>
            )}

            <button type="submit" disabled={loading}
                className="w-full bg-[#3b82f6] hover:bg-[#2563eb] disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors text-sm">
                {loading ? (
                    <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
                        Computing...
                    </span>
                ) : 'Run Analysis'}
            </button>
        </form>
    );
}
