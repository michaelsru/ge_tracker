import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import SkillTable from './components/SkillTable';

const fetchPrices = () => axios.get('/api/prices').then(r => r.data);
const fetchTimers = () => axios.get('/api/timers').then(r => r.data);

const ALL_TAB = 'All';

function App() {
  const [activeTab, setActiveTab] = useState(ALL_TAB);
  const qc = useQueryClient();

  const { data: recipes = [], dataUpdatedAt, isError } = useQuery({
    queryKey: ['prices'],
    queryFn: fetchPrices,
    refetchInterval: 60_000,
  });

  const { data: skillTabs = [] } = useQuery({
    queryKey: ['timers'],
    queryFn: fetchTimers,
    staleTime: Infinity, // only re-fetch on explicit refresh
  });

  // Reset active tab if it no longer exists after timers load
  useEffect(() => {
    if (activeTab !== ALL_TAB && !skillTabs.find(t => t.id === activeTab)) {
      setActiveTab(ALL_TAB);
    }
  }, [skillTabs]);

  const allTabs   = [ALL_TAB, ...skillTabs.map(t => t.id)];
  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : 'Never';
  const skillTab  = skillTabs.find(t => t.id === activeTab) ?? null;
  const rateMap   = Object.fromEntries(skillTabs.map(t => [t.tag, t.rateConfig]));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="w-full px-6 pt-8 pb-4">
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

        <div className="flex gap-1 border-b border-slate-800">
          {allTabs.map(tab => (
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

      <main className="w-full px-6 py-6">
        {isError && (
          <div className="mb-4 px-4 py-3 bg-red-950 border border-red-800 rounded text-red-400 text-sm">
            ⚠ Failed to fetch prices — is the backend running?
          </div>
        )}

        <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
          {skillTab && (
            <div className="px-6 py-4 border-b border-slate-800">
              <h2 className="text-base font-semibold text-slate-200">{skillTab.title}</h2>
              <p className="text-xs text-slate-500 mt-0.5">Click column headers to sort</p>
            </div>
          )}
          <SkillTable
            key={activeTab}
            recipes={recipes}
            tag={skillTab?.tag ?? null}
            rateConfig={skillTab?.rateConfig ?? null}
            rateMap={skillTab ? null : rateMap}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
