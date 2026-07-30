import React, { useState, useMemo } from 'react';

const WIKI_BASE = 'https://oldschool.runescape.wiki/w/';

const formatGP = (n) => {
  if (n == null) return '—';
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
};

const COLS = [
  { key: 'name',          label: 'Herb',      align: 'left'  },
  { key: 'input_price',   label: 'Grimy',     align: 'right' },
  { key: 'output_price',  label: 'Clean',     align: 'right' },
  { key: 'profit_margin', label: 'Profit',    align: 'right' },
  { key: 'gp_xp',        label: 'GP/XP',     align: 'right' },
  { key: 'input_volume',  label: 'Buy Vol',   align: 'right' },
  { key: 'output_volume', label: 'Sell Vol',  align: 'right' },
  { key: 'level',         label: 'Level',     align: 'right' },
  { key: 'xp',           label: 'XP',        align: 'right' },
];

// Stacks abbr + full in same grid cell so column width is always the wider value.
// CSS handles the crossfade via .price-cell:hover selectors in index.css.
const PriceCell = ({ value }) => {
  const abbr = formatGP(value);
  const full = value != null ? value.toLocaleString() : '—';
  const same = abbr === full;
  return (
    <span className="price-cell">
      <span className="price-abbr">{abbr}</span>
      {!same && <span className="price-full">{full}</span>}
    </span>
  );
};

const HerbTable = ({ recipes }) => {
  const [sortKey, setSortKey] = useState('gp_xp');
  const [sortDir, setSortDir] = useState('desc');

  const herbs = useMemo(() =>
    recipes.filter(r => r.tags?.includes('herblore')),
    [recipes]
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
            const wikiName = herb.name.replace(/ /g, '_');
            const profitable = herb.profit_margin > 0;
            return (
              <tr key={herb.id} className={profitable ? 'row-profit' : 'row-loss'}>
                <td className="col-left herb-name">
                  <a href={`${WIKI_BASE}${wikiName}`} target="_blank" rel="noreferrer">
                    {herb.name}
                  </a>
                </td>
                <td className="col-right price-col"><PriceCell value={herb.input_price} /></td>
                <td className="col-right price-col"><PriceCell value={herb.output_price} /></td>
                <td className={`col-right profit-cell ${profitable ? 'green' : 'red'}`}>
                  {profitable ? '+' : ''}{formatGP(herb.profit_margin)}
                </td>
                <td className={`col-right ${profitable ? 'green' : 'red'}`}>
                  {herb.gp_xp != null ? herb.gp_xp.toFixed(2) : '—'}
                </td>
                <td className="col-right muted">{herb.input_volume != null ? herb.input_volume.toLocaleString() : '—'}</td>
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
