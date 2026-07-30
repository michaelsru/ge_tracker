import React, { useState, useMemo } from 'react';
import axios from 'axios';
import { useQuery, useQueryClient } from '@tanstack/react-query';

const WIKI_BASE   = 'https://oldschool.runescape.wiki/w/';
const PRICES_BASE = 'https://prices.runescape.wiki/osrs/item/';

const formatGP = (n) => {
  if (n == null) return '—';
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000)     return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
};

const BASE_COLS = [
  { key: 'name',          label: 'Item',        align: 'left'  },
  { key: 'input_price',   label: 'Input',       align: 'right' },
  { key: 'output_price',  label: 'Output',      align: 'right' },
  { key: 'profit_margin', label: 'Profit',      align: 'right' },
  { key: 'gp_xp',        label: 'GP/XP',       align: 'right' },
  { key: 'hourly_profit', label: 'Hourly GP',   align: 'right', requiresRate: true },
  { key: 'xp_hour',      label: 'XP/hr',       align: 'right', requiresRate: true },
  { key: 'capital',       label: 'Capital',     align: 'right', requiresRate: true },
  { key: 'input_volume',  label: 'Buy Vol',     align: 'right' },
  { key: 'output_volume', label: 'Sell Vol',    align: 'right' },
  { key: 'level',         label: 'Level',       align: 'right' },
  { key: 'xp',           label: 'XP',          align: 'right' },
  { key: 'actions',      label: '',           align: 'center' },
];

const PriceCell = ({ value, itemId, name }) => {
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
      <span className="price-full">
        {name && <span className="price-name">{name}</span>}
        <span className="price-val">{full}</span>
      </span>
    </a>
  );
};

// Single input → PriceCell. Multiple → total with hover breakdown.
const InputCell = ({ items, total }) => {
  if (items.length === 1) {
    return <PriceCell value={total} itemId={items[0].id} name={items[0].name} />;
  }
  return (
    <span className="input-multi">
      <span className="input-multi-total">{formatGP(total)}</span>
      <span className="input-multi-breakdown">
        {items.map(item => (
          <a
            key={item.id}
            className="input-multi-row"
            href={`${PRICES_BASE}${item.id}`}
            target="_blank"
            rel="noreferrer"
          >
            <span className="input-multi-name">{item.name}</span>
            <span className="input-multi-price">{item.price != null ? item.price.toLocaleString() : '—'}</span>
          </a>
        ))}
        <span className="input-multi-row input-multi-footer">
          <span className="input-multi-name">Total</span>
          <span className="input-multi-price">{total != null ? total.toLocaleString() : '—'}</span>
        </span>
      </span>
    </span>
  );
};

/**
 * rateConfig shapes:
 *   { mode: 'inventory', label: 'Secs / inventory', default: 3.5, invSize: 28 }
 * rateConfig: { loopSecs: number, conversionsPerLoop: number }
 * unitsPerHour = conversionsPerLoop * 3600 / loopSecs
 */
const uphFromConfig = (rc) => {
  if (!rc || rc.loopSecs <= 0 || rc.conversionsPerLoop <= 0) return 0;
  return rc.conversionsPerLoop * (3600 / rc.loopSecs);
};

const SkillTable = ({ recipes, tag = null, rateConfig = null, rateMap = null }) => {
  const qc = useQueryClient();
  const [sortKey, setSortKey]   = useState('profit_margin');
  const [sortDir, setSortDir]   = useState('desc');
  const [overrides, setOverrides] = useState({});
  const [showHidden, setShowHidden] = useState(false);

  // Re-use the cached timers fetch — no extra network request
  const { data: timers = [] } = useQuery({
    queryKey: ['timers'],
    queryFn: () => axios.get('/api/timers').then(r => r.data),
    staleTime: Infinity,
  });

  const fetchedConfig = (tag ? timers.find(t => t.tag === tag)?.rateConfig : null) ?? rateConfig;

  // User override wins; fetched config is the default (resolves after async load)
  const loopSecs    = overrides.loopSecs    ?? fetchedConfig?.loopSecs    ?? 1;
  const convPerLoop = overrides.convPerLoop ?? fetchedConfig?.conversionsPerLoop ?? 1;

  const hasRate = rateConfig || rateMap;
  const COLS = hasRate ? BASE_COLS : BASE_COLS.filter(c => !c.requiresRate);

  const unitsPerHour = useMemo(() => {
    if (!rateConfig) return 0;
    return uphFromConfig({ loopSecs, conversionsPerLoop: convPerLoop });
  }, [loopSecs, convPerLoop, rateConfig]);

  const rows = useMemo(() =>
    recipes
      .filter(r => tag === null || r.tags?.includes(tag))
      .map(r => {
        let uph = rateConfig ? unitsPerHour : 0;
        if (!rateConfig && rateMap) {
          const matchTag = r.tags?.find(t => rateMap[t]);
          if (matchTag) uph = uphFromConfig(rateMap[matchTag]);
        }
        return {
          ...r,
          hourly_profit: uph > 0 ? Math.round(r.profit_margin * uph) : null,
          xp_hour:       uph > 0 && r.xp ? Math.round(r.xp * uph) : null,
          capital:       uph > 0 && r.input_price ? Math.round(r.input_price * uph) : null,
        };
      }),
    [recipes, tag, unitsPerHour, rateConfig, rateMap]
  );

  const sorted = useMemo(() => {
    return [...rows].sort((a, b) => {
      const av = a[sortKey] ?? -Infinity;
      const bv = b[sortKey] ?? -Infinity;
      if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortDir === 'asc' ? av - bv : bv - av;
    });
  }, [rows, sortKey, sortDir]);

  const visibleSorted = useMemo(() => {
    return sorted.filter(r => showHidden || !r.hidden);
  }, [sorted, showHidden]);

  const hiddenCount = useMemo(() => {
    return rows.filter(r => r.hidden).length;
  }, [rows]);

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const toggleHide = async (recipeId, currentHidden) => {
    await axios.patch(`/api/recipes/${recipeId}`, { hidden: !currentHidden });
    qc.invalidateQueries({ queryKey: ['prices'] });
  };

  const [saved, setSaved] = useState(false);

  const saveTimer = async () => {
    await axios.patch(`/api/timers/${tag}`, { loopSecs, conversionsPerLoop: convPerLoop });
    qc.invalidateQueries({ queryKey: ['timers'] });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  const arrow = (key) => sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : '';

  return (
    <div className="herb-table-wrap">
      {(rateConfig || hiddenCount > 0) && (
        <div className="herb-config">
          {rateConfig && (
            <>
              <label className="herb-config-label">
                Loop time (s)
                <input
                  type="number" min="0.01" step="0.1"
                  value={loopSecs}
                  onChange={e => setOverrides(o => ({ ...o, loopSecs: parseFloat(e.target.value) }))}
                  className="herb-config-input"
                />
              </label>
              <label className="herb-config-label">
                Per loop
                <input
                  type="number" min="1" step="1"
                  value={convPerLoop}
                  onChange={e => setOverrides(o => ({ ...o, convPerLoop: parseInt(e.target.value) }))}
                  className="herb-config-input"
                />
              </label>
              <span className="herb-config-rate">
                ≈ {Math.round(unitsPerHour).toLocaleString()} units/hr
              </span>
              <button onClick={saveTimer} className={`herb-config-save ${saved ? 'saved' : ''}`}>
                {saved ? '✓ Saved' : 'Set'}
              </button>
            </>
          )}
          {hiddenCount > 0 && (
            <button
              onClick={() => setShowHidden(v => !v)}
              className={`herb-config-save ${showHidden ? 'saved' : ''}`}
              style={{ marginLeft: 'auto' }}
            >
              {showHidden ? `Hide Hidden (${hiddenCount})` : `Show Hidden (${hiddenCount})`}
            </button>
          )}
        </div>
      )}
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
          {visibleSorted.map(row => {
            const wikiName   = row.name.replace(/ /g, '_');
            const profitable = row.profit_margin > 0;
            return (
              <tr key={row.id} className={`${profitable ? 'row-profit' : 'row-loss'} ${row.hidden ? 'herb-row-hidden' : ''}`}>
                <td className="col-left herb-name">
                  <a href={`${WIKI_BASE}${wikiName}`} target="_blank" rel="noreferrer">
                    {row.name}
                  </a>
                </td>
                <td className="col-right price-col"><InputCell items={row.inputs} total={row.input_price} /></td>
                <td className="col-right price-col"><PriceCell value={row.output_price} itemId={row.outputs[0]?.id} name={row.outputs[0]?.name} /></td>
                <td className={`col-right ${profitable ? 'green' : 'red'}`}>
                  {profitable ? '+' : ''}{formatGP(row.profit_margin)}
                </td>
                <td className={`col-right ${profitable ? 'green' : 'red'}`}>
                  {row.gp_xp != null ? row.gp_xp.toFixed(2) : '—'}
                </td>
                {hasRate && (
                  <td className={`col-right font-bold ${profitable ? 'green' : 'red'}`}>
                    {row.hourly_profit != null ? (profitable ? '+' : '') + formatGP(row.hourly_profit) : '—'}
                  </td>
                )}
                {hasRate && (
                  <td className="col-right muted">
                    {row.xp_hour != null ? row.xp_hour.toLocaleString() : '—'}
                  </td>
                )}
                {hasRate && (
                  <td className="col-right muted">
                    {row.capital != null ? formatGP(row.capital) : '—'}
                  </td>
                )}
                <td className="col-right muted">{row.input_volume  != null ? row.input_volume.toLocaleString()  : '—'}</td>
                <td className="col-right muted">{row.output_volume != null ? row.output_volume.toLocaleString() : '—'}</td>
                <td className="col-right muted">{row.level}</td>
                <td className="col-right muted">{row.xp}</td>
                <td className="col-center">
                  <button
                    onClick={() => toggleHide(row.id, row.hidden)}
                    title={row.hidden ? "Unhide recipe" : "Hide recipe"}
                    className="herb-hide-btn"
                  >
                    {row.hidden ? 'Unhide' : 'Hide'}
                  </button>
                </td>
              </tr>
            );
          })}
          {visibleSorted.length === 0 && (
            <tr>
              <td colSpan={COLS.length} className="col-left muted" style={{ padding: '2rem 1rem' }}>
                No data — check backend is running and recipes are configured.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default SkillTable;
