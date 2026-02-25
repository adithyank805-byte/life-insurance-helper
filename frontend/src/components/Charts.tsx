import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';
import type { ProjectionRow } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: '#94a3b8', font: { size: 11 } } },
        tooltip: { backgroundColor: '#1e293b', titleColor: '#f1f5f9', bodyColor: '#94a3b8', borderColor: '#334155', borderWidth: 1 },
    },
    scales: {
        x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } },
        y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } },
    },
};

interface Props {
    rows: ProjectionRow[] | null;
    reserves: number[] | null;
}

export default function Charts({ rows, reserves }: Props) {
    if (!rows || rows.length === 0) return null;

    const labels = rows.map(r => `${r.t}`);

    const inforceData = {
        labels,
        datasets: [{
            label: 'In-Force Probability',
            data: rows.map(r => r.survival),
            borderColor: '#8b5cf6',
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 3,
            pointBackgroundColor: '#8b5cf6',
        }],
    };

    const cashflowData = {
        labels,
        datasets: [
            {
                label: 'Premium CF',
                data: rows.map(r => r.premium_cf),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.3,
                pointRadius: 3,
            },
            {
                label: 'Claim CF',
                data: rows.map(r => r.claim_cf),
                borderColor: '#f43f5e',
                backgroundColor: 'rgba(244, 63, 94, 0.1)',
                tension: 0.3,
                pointRadius: 3,
            },
            {
                label: 'Expense CF',
                data: rows.map(r => r.expense_cf),
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                tension: 0.3,
                pointRadius: 3,
            },
        ],
    };

    const reserveLabels = reserves ? reserves.map((_, i) => `${i}`) : [];
    const reserveData = reserves ? {
        labels: reserveLabels,
        datasets: [{
            label: 'Reserve V(t)',
            data: reserves,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: '#10b981',
        }],
    } : null;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4">
                <h3 className="text-sm font-semibold text-[#f1f5f9] mb-3 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#8b5cf6]"></span>
                    In-Force Progression
                </h3>
                <div className="h-64">
                    <Line data={inforceData} options={{ ...chartDefaults, plugins: { ...chartDefaults.plugins, legend: { display: false } } }} />
                </div>
            </div>

            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4">
                <h3 className="text-sm font-semibold text-[#f1f5f9] mb-3 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#3b82f6]"></span>
                    Cashflow Projection
                </h3>
                <div className="h-64">
                    <Line data={cashflowData} options={chartDefaults} />
                </div>
            </div>

            {reserveData && (
                <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 lg:col-span-2">
                    <h3 className="text-sm font-semibold text-[#f1f5f9] mb-3 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
                        Reserve Progression
                    </h3>
                    <div className="h-64">
                        <Line data={reserveData} options={{ ...chartDefaults, plugins: { ...chartDefaults.plugins, legend: { display: false } } }} />
                    </div>
                </div>
            )}
        </div>
    );
}
