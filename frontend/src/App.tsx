import { useState } from 'react';
import InputForm from './components/InputForm';
import Dashboard from './components/Dashboard';
import ProjectionTable from './components/ProjectionTable';
import ReserveSchedule from './components/ReserveSchedule';
import Charts from './components/Charts';
import type { AssumptionsInput, PricingResult, ProjectionRow, ProjectionSummary, RollforwardRow } from './services/api';
import { runReserve } from './services/api';

type Tab = 'dashboard' | 'projection' | 'reserves' | 'charts';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  const [pricing, setPricing] = useState<PricingResult | null>(null);
  const [summary, setSummary] = useState<ProjectionSummary | null>(null);
  const [rows, setRows] = useState<ProjectionRow[] | null>(null);
  const [reserves, setReserves] = useState<number[] | null>(null);
  const [rollforward, setRollforward] = useState<RollforwardRow[] | null>(null);

  const handleSubmit = async (input: AssumptionsInput) => {
    setLoading(true);
    setError('');
    try {
      // Single API call — reserve endpoint returns pricing + projection + reserves + rollforward
      const res = await runReserve(input);

      setPricing({
        premium: res.solved_premium,
        f_at_solution: 0,
        iterations: 0,
        converged: true,
        tolerance: 0,
      });
      setSummary(res.projection.summary);
      setRows(res.projection.rows);
      setReserves(res.reserves);
      setRollforward(res.rollforward);
      setActiveTab('dashboard');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'API error');
      } else {
        setError('Connection failed — is the backend running on port 8000?');
      }
    } finally {
      setLoading(false);
    }
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'projection', label: 'Projection' },
    { key: 'reserves', label: 'Reserves' },
    { key: 'charts', label: 'Charts' },
  ];

  return (
    <div className="min-h-screen bg-[#0f172a]">
      {/* Header */}
      <header className="border-b border-[#1e293b] bg-[#0f172a]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#3b82f6] to-[#8b5cf6] flex items-center justify-center text-white font-bold text-sm">
              A
            </div>
            <div>
              <h1 className="text-lg font-semibold text-[#f1f5f9]">Actuarial Engine</h1>
              <p className="text-xs text-[#64748b]">Deterministic Projection • Pricing • Reserving</p>
            </div>
          </div>
          <div className="flex items-center gap-1 bg-[#1e293b] rounded-lg p-1">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                disabled={!rows}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === tab.key
                    ? 'bg-[#3b82f6] text-white'
                    : 'text-[#94a3b8] hover:text-[#f1f5f9] hover:bg-[#334155] disabled:opacity-40 disabled:cursor-not-allowed'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <main className="max-w-[1400px] mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6">
          {/* Left Sidebar — Input Form */}
          <aside className="lg:sticky lg:top-20 lg:self-start">
            <InputForm onSubmit={handleSubmit} loading={loading} />
          </aside>

          {/* Right Panel — Results */}
          <section className="min-w-0 space-y-6">
            {error && (
              <div className="bg-[#f43f5e]/10 border border-[#f43f5e]/30 text-[#f43f5e] rounded-xl px-4 py-3 text-sm">
                <strong>Error:</strong> {error}
              </div>
            )}

            {!rows && !loading && (
              <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-12 text-center">
                <div className="w-16 h-16 rounded-full bg-[#334155] mx-auto mb-4 flex items-center justify-center">
                  <svg className="w-8 h-8 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-[#f1f5f9] font-medium mb-1">No Results Yet</h3>
                <p className="text-[#64748b] text-sm">Configure assumptions and click "Run Analysis" to begin.</p>
              </div>
            )}

            {rows && activeTab === 'dashboard' && (
              <Dashboard pricing={pricing} summary={summary} reserves={reserves} />
            )}

            {rows && activeTab === 'projection' && (
              <ProjectionTable rows={rows} />
            )}

            {rows && activeTab === 'reserves' && (
              <ReserveSchedule reserves={reserves} rollforward={rollforward} />
            )}

            {rows && activeTab === 'charts' && (
              <Charts rows={rows} reserves={reserves} />
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
