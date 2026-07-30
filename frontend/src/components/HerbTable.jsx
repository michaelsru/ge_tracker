import React, { useState, useMemo } from 'react';

const WIKI_BASE   = 'https://oldschool.runescape.wiki/w/';
const PRICES_BASE = 'https://prices.runescape.wiki/osrs/item/';
const INV_SIZE    = 28;

const formatGP = (n) => {
  if (n == null) return '—';
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000)     return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
};

const COLS = [
  { key: 'name',          label: 'Herb',        align: 'left'  },
  { key: 'input_price',   label: 'Grimy',       align: 'right' },
  { key: 'output_price',  label: 'Clean',       align: 'right' },
  { key: 'profit_margin', label: 'Profit',      align: 'right' },
  { key: 'gp_xp',        label: 'GP/XP',       align: 'right' },
  { key: 'hourly_profit', label: 'Hourly',      align: 'right' },
  { key: 'input_volume',  label: 'Buy Vol',     align: 'right' },
  { key: 'output_volume', label: 'Sell Vol',    align: 'right' },
  { key: 'level',         label: 'Level',       align: 'right' },
  { key: 'xp',           label: 'XP',          align: 'right' },
];

// Stacks abbr + full in same grid cell — column width = max(abbr, full).
const PriceCell = ({ value, itemId }) => {
  const abbr = formatGP(value);
  const full = value != null ? value.toLocaleString() : '—';
  return (
    <a
      className="price-cell"
      href={itemId ? `${PRICES_BASE}${itemId}` : undefined}
      target="_blank"
      rel="noreferrer"
    >
      <span className="price-abbr">{abbr}</span>
      <span className="price-full">{full}</span>
    </a>
  );
};

const HerbTable = ({ recipes }) => {
  const [sortKey, setSortKey]   = useState('hourly_profit');
  const [sortDir, setSortDir]   = useState('desc');
  const [secsPerInv, setSecsPerInv] = useState(3.5);

  const herbsPerHour = useMemo(
    () => INV_SIZE * (3600 / Math.max(secsPerInv, 0.1)),
    [secsPerInv]
  );

  const herbs = useMemo(() =>
    recipes
      .filter(r => r.tags?.includes('herblore'))
      .map(r => ({ ...r, hourly_profit: Math.round(r.profit_margin * herbsPerHour) })),
    [recipes, herbsPerHour]
  );

  const sorted = useMemo(() => {
    return [...herbs].sort((a, b) => {
      const av = a[sortKey] ?? -Infinity;
      const bv = b[sortKey] ?? -Infinity;
      if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortDir === 'asc' ? av - bv : bv - av;
    });
  }, [herbs, sortKey, sortDir]);

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const arrow = (key) => sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : '';

  return (
    <div className="herb-table-wrap">
      {/* Config bar */}
      <div className="herb-config">
        <label className="herb-config-label">
          Secs / inventory
          <input
            type="number"
            min="0.1"
            step="0.1"
            value={secsPerInv}
            onChange={e => setSecsPerInv(parseFloat(e.target.value) || 3.5)}
            className="herb-config-input"
          />
        </label>
        <span className="herb-config-rate">
          ≈ {Math.round(herbsPerHour).toLocaleString()} herbs/hr
        </span>
      </div>

      <table className="herb-table">
        <thead>
          <tr>
            {COLS.map(c => (
              <th
                key={c.key}
                className={`col-${c.align} ${sortKey === c.key ? 'active' : ''}`}
                onClick={() => handleSort(c.key)}
              >
                {c.label}{arrow(c.key)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(herb => {
            const wikiName  = herb.name.replace(/ /g, '_');
            const profitable = herb.profit_margin > 0;
            return (
              <tr key={herb.id} className={profitable ? 'row-profit' : 'row-loss'}>
                <td className="col-left herb-name">
                  <a href={`${WIKI_BASE}${wikiName}`} target="_blank" rel="noreferrer">
                    {herb.name}
                  </a>
                </td>
                <td className="col-right price-col"><PriceCell value={herb.input_price}  itemId={herb.inputs[0]?.id} /></td>
                <td className="col-right price-col"><PriceCell value={herb.output_price} itemId={herb.outputs[0]?.id} /></td>
                <td className={`col-right ${profitable ? 'green' : 'red'}`}>
                  {profitable ? '+' : ''}{formatGP(herb.profit_margin)}
                </td>
                <td className={`col-right ${profitable ? 'green' : 'red'}`}>
                  {herb.gp_xp != null ? herb.gp_xp.toFixed(2) : '—'}
                </td>
                <td className={`col-right font-bold ${profitable ? 'green' : 'red'}`}>
                  {profitable ? '+' : ''}{formatGP(herb.hourly_profit)}
                </td>
                <td className="col-right muted">{herb.input_volume  != null ? herb.input_volume.toLocaleString()  : '—'}</td>
                <td className="col-right muted">{herb.output_volume != null ? herb.output_volume.toLocaleString() : '—'}</td>
                <td className="col-right muted">{herb.level}</td>
                <td className="col-right muted">{herb.xp}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default HerbTable;
