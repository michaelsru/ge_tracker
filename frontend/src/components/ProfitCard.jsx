import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StabilityChart from './StabilityChart';

const ProfitCard = ({ recipe }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);

    // Format numbers
    const formatGP = (num) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num;
    };

    // Fetch history for all inputs and outputs
    useEffect(() => {
        const fetchAllHistory = async () => {
            setLoading(true);
            const allIds = [...recipe.inputs.map(i => i.id), ...recipe.outputs.map(i => i.id)];
            const uniqueIds = [...new Set(allIds)];

            try {
                const promises = uniqueIds.map(id =>
                    axios.get(`/api/history/${id}`).then(res => ({ id, data: res.data }))
                );

                const results = await Promise.all(promises);
                const historyMap = {};
                results.forEach(item => {
                    historyMap[item.id] = item.data;
                });
                setHistory(historyMap);
            } catch (err) {
                console.error("Failed to fetch history", err);
            } finally {
                setLoading(false);
            }
        };

        if (recipe.inputs.length || recipe.outputs.length) {
            fetchAllHistory();
        }
    }, [recipe.inputs, recipe.outputs]);

    return (
        <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700 hover:border-blue-500 transition-colors">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-xl font-bold text-white mb-2">{recipe.name}</h3>

                    <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                            <span className="text-slate-500 text-xs font-bold uppercase tracking-wider bg-slate-900/50 px-1.5 py-0.5 rounded">In</span>
                            {recipe.inputs.map(i => (
                                <span key={i.id} className="text-xs text-slate-300 bg-slate-700 px-2 py-1 rounded border border-slate-600">
                                    {i.name}
                                </span>
                            ))}
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                            <span className="text-slate-500 text-xs font-bold uppercase tracking-wider bg-slate-900/50 px-1.5 py-0.5 rounded">Out</span>
                            {recipe.outputs.map(i => (
                                <span key={i.id} className="text-xs text-slate-300 bg-slate-700 px-2 py-1 rounded border border-slate-600">
                                    {i.name}
                                </span>
                            ))}
                        </div>

                        <div className="pt-2">
                            <span className={`text-xs font-bold px-2 py-1 rounded-full border ${recipe.is_profitable ? 'bg-green-950 text-green-400 border-green-800' : 'bg-red-950 text-red-400 border-red-800'}`}>
                                ROI: {recipe.roi}%
                            </span>
                        </div>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-2xl font-mono font-bold text-green-400">
                        {recipe.profit_margin > 0 ? '+' : ''}{formatGP(recipe.profit_margin)}
                    </div>
                    <div className="text-slate-500 text-xs uppercase tracking-wider">Profit</div>
                </div>
            </div>

            {/* Chart */}
            <div className="mt-4 bg-slate-900/50 rounded-md p-2 h-32">
                {loading ? (
                    <div className="flex items-center justify-center h-full text-slate-500">Loading Chart...</div>
                ) : (
                    <StabilityChart history={history} inputs={recipe.inputs} outputs={recipe.outputs} />
                )}
            </div>
        </div>
    );
};

export default ProfitCard;
