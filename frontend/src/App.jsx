import React, { useState } from 'react';
import axios from 'axios';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import ProfitCard from './components/ProfitCard';
import HerbTable from './components/HerbTable';

const fetchPrices = () => axios.get('/api/prices').then(r => r.data);

const TABS = ['All', 'Herblore', 'Cooking'];

function App() {
  const [activeTab, setActiveTab] = useState('All');
  const qc = useQueryClient();

  const { data: recipes = [], dataUpdatedAt, isError } = useQuery({
    queryKey: ['prices'],
    queryFn: fetchPrices,
    refetchInterval: 60_000,
  });

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : 'Never';

  const nonHerblore = recipes.filter(r =>
    !r.tags?.includes('herblore') &&
    (activeTab === 'All' || r.tags?.includes(activeTab.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="max-w-7xl mx-auto px-8 pt-8 pb-4">
        <div className="flex justify-between items-end mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 text-transparent bg-clip-text">
              OSRS GE Tracker
            </h1>
            <p className="text-slate-400 mt-1 text-sm">Real-time prices · refreshes every 60s</p>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span>Updated: {lastUpdated}</span>
            <button
              onClick={() => qc.invalidateQueries({ queryKey: ['prices'] })}
              className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-slate-300 transition-colors"
            >
              ↻ Refresh
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-slate-800">
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-6">
        {isError && (
          <div className="mb-4 px-4 py-3 bg-red-950 border border-red-800 rounded text-red-400 text-sm">
            ⚠ Failed to fetch prices — is the backend running?
          </div>
        )}

        {activeTab === 'Herblore' ? (
          <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800">
              <h2 className="text-base font-semibold text-slate-200">Herb Cleaning</h2>
              <p className="text-xs text-slate-500 mt-0.5">Click column headers to sort</p>
            </div>
            <div className="px-2 py-2">
              <HerbTable recipes={recipes} />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {nonHerblore.map(r => <ProfitCard key={r.id} recipe={r} />)}
            {nonHerblore.length === 0 && (
              <div className="col-span-full text-center py-20 text-slate-600">
                No recipes tracked. Check backend configuration.
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
