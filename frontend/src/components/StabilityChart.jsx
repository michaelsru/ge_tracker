import React, { useMemo } from 'react';
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
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const StabilityChart = ({ history, inputs, outputs }) => {
    const data = useMemo(() => {
        if (!history || Object.keys(history).length === 0) return { labels: [], datasets: [] };

        // 1. Collect all timestamps to unify x-axis
        const allTimestamps = new Set();
        Object.values(history).forEach(points => {
            points.forEach(p => allTimestamps.add(p.timestamp));
        });

        const sortedTimestamps = Array.from(allTimestamps).sort((a, b) => a - b);
        const labels = sortedTimestamps.map(t => new Date(t * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));

        // 2. Create Datasets
        const datasets = [];

        // Helper to find closest price for a timestamp (fill gaps)
        const getPriceAtTime = (points, timestamp) => {
            const point = points.find(p => p.timestamp === timestamp);
            return point ? point.price : null; // Chart.js handles null as gap or span
        };

        // Inputs (Dimmer)
        inputs.forEach(item => {
            if (history[item.id]) {
                const prices = sortedTimestamps.map(t => getPriceAtTime(history[item.id], t));
                datasets.push({
                    label: item.name,
                    data: prices,
                    borderColor: 'rgb(71, 85, 105)', // Slate 600
                    backgroundColor: 'transparent',
                    borderWidth: 1, // Thin
                    pointRadius: 0,
                    tension: 0.1,
                });
            }
        });

        // Outputs (Highlighted)
        outputs.forEach(item => {
            if (history[item.id]) {
                const prices = sortedTimestamps.map(t => getPriceAtTime(history[item.id], t));
                datasets.push({
                    label: item.name,
                    data: prices,
                    borderColor: 'rgb(34, 197, 94)', // Green 500
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    borderWidth: 2, // Thick
                    pointRadius: 0, // Clean line
                    tension: 0.1,
                });
            }
        });

        return { labels, datasets };
    }, [history, inputs, outputs]);

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: (context) => {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += new Intl.NumberFormat('en-US').format(context.parsed.y) + ' gp';
                        }
                        return label;
                    }
                }
            },
        },
        scales: {
            x: {
                display: false,
                grid: { display: false }
            },
            y: {
                display: true,
                ticks: { color: '#9CA3AF' },
                grid: { color: '#334155' }
            },
        },
    };

    return <div className="h-24 w-full"><Line data={data} options={options} /></div>;
};

export default StabilityChart;
