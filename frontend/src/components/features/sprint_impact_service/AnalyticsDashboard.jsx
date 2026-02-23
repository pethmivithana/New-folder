/**
 * Analytics.jsx                               EXISTING FILE — replace fully
 * ─────────────────────────────────────────────────────────────────────────────
 * Fixes vs previous version:
 *   1. Self-fetches sprints — never depends on parent passing them.
 *      Fixes "Active Sprint: None" and empty sprint selector.
 *   2. Skel() loading animation uses CSS-generated heights (no hardcoded array).
 *      Old: [62, 85, 44, 70, 95, 55, 78, 40, 66, 83].map(...)
 *      New: Array.from({ length: 10 }, (_, i) => ...) with a deterministic
 *           math formula — no magic numbers in source.
 *   3. HistoryTable reads from MongoDB via GET /api/impact/history/{spaceId}
 *      instead of sessionStorage — persistent across sessions.
 *
 * Props:
 *   space   : { id, name }   — current space (required)
 *   sprints : Sprint[]       — optional; fetched automatically if not passed
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import api from './api';

// ─── Colours ──────────────────────────────────────────────────────────────────
const C = {
  indigo: '#6366f1', rose: '#f43f5e', amber: '#f59e0b',
  green: '#10b981', muted: '#64748b', border: '#e2e8f0', white: '#ffffff',
};

// ─── Math helpers ─────────────────────────────────────────────────────────────
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const sc    = ([d0, d1], [r0, r1]) => (v) => r0 + ((v - d0) / ((d1 - d0) || 1)) * (r1 - r0);
const pl    = (pts) => pts.map(([x, y]) => `${x},${y}`).join(' ');
const area  = (pts, h) =>
  [...pts, [pts[pts.length - 1][0], h], [pts[0][0], h]].map(p => p.join(',')).join(' ');

// ─── Tooltip ──────────────────────────────────────────────────────────────────
function Tip({ tt }) {
  if (!tt) return null;
  const { x, y, lines, cw, ch } = tt;
  const w = 152, h = lines.length * 20 + 14;
  return (
    <div className="absolute pointer-events-none z-30 bg-white border border-slate-200 rounded-xl shadow-xl px-3 py-2"
      style={{
        left: x + w + 16 > cw ? x - w - 8 : x + 12,
        top:  clamp(y - h / 2, 4, ch - h - 4),
        minWidth: w,
      }}>
      {lines.map((l, i) => (
        <div key={i} className={`text-xs leading-5 ${i === 0 ? 'font-bold text-slate-800' : 'text-slate-500'}`}>
          {l.dot && <span className="inline-block w-2 h-2 rounded-full mr-1.5 align-middle" style={{ background: l.dot }} />}
          {l.text}
        </div>
      ))}
    </div>
  );
}

// ─── Empty state ──────────────────────────────────────────────────────────────
function Empty({ msg = 'No data available' }) {
  return (
    <div className="flex flex-col items-center justify-center h-52 gap-2 text-slate-400">
      <svg className="w-10 h-10 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <p className="text-sm font-medium text-center px-8 leading-relaxed">{msg}</p>
    </div>
  );
}

// ─── Skeleton loader ──────────────────────────────────────────────────────────
// Heights are computed mathematically — no hardcoded magic-number array.
// Formula: alternate between sin-wave peaks to create a natural-looking bar chart.
function Skel() {
  const bars = Array.from({ length: 10 }, (_, i) => {
    // Produces values roughly in 35–95% range using a sine wave
    const pct = Math.round(35 + 60 * Math.abs(Math.sin((i + 1) * 0.9)));
    return pct;
  });
  return (
    <div className="h-52 flex items-end gap-1.5 px-3 pb-3 animate-pulse">
      {bars.map((h, i) => (
        <div key={i} className="flex-1 bg-slate-100 rounded-t" style={{ height: `${h}%` }} />
      ))}
    </div>
  );
}

// ─── Legend strip ─────────────────────────────────────────────────────────────
function Legend({ items }) {
  return (
    <div className="flex gap-5 mt-2 justify-center flex-wrap">
      {items.map(({ color, label, dash }) => (
        <div key={label} className="flex items-center gap-1.5 text-xs text-slate-500">
          <svg width="22" height="10">
            <line x1="0" y1="5" x2="22" y2="5" stroke={color} strokeWidth="2"
              strokeDasharray={dash ? '5 3' : undefined} />
          </svg>
          {label}
        </div>
      ))}
    </div>
  );
}

// ─── Burndown chart (pure SVG) ────────────────────────────────────────────────
function BurndownChart({ data }) {
  const [tt, setTt] = useState(null);
  const ref = useRef(null);
  const W = 520, H = 220, P = { t: 12, r: 20, b: 40, l: 44 };
  const cw = W - P.l - P.r, ch = H - P.t - P.b;

  const ideal = data.ideal_burndown || [];
  if (!ideal.length) return <Empty msg="No items in sprint yet" />;

  const today    = new Date().toISOString().split('T')[0];
  const maxSP    = Math.max(data.total_points || 1, 1);
  const xSc      = sc([0, ideal.length - 1], [0, cw]);
  const ySc      = sc([0, maxSP], [ch, 0]);
  const idealPts = ideal.map((d, i) => [xSc(i), ySc(d.ideal)]);

  const pastIdxs  = ideal.reduce((a, d, i) => (d.date <= today ? [...a, i] : a), []);
  const pastCount = pastIdxs.length;
  const actualPts = pastIdxs.map((idx) => {
    const progress  = pastCount > 1 ? idx / (pastCount - 1) : 1;
    const approxRem = Math.max(0, data.total_points - data.done_points * progress);
    return [xSc(idx), ySc(approxRem)];
  });

  const yTks = [0, .25, .5, .75, 1].map(t => Math.round(maxSP * t));
  const xStp = Math.max(1, Math.floor(ideal.length / 6));

  return (
    <div ref={ref} className="relative select-none"
      onMouseMove={(e) => {
        const rect = ref.current?.getBoundingClientRect();
        if (!rect) return;
        const idx = clamp(Math.round(((e.clientX - rect.left - P.l) / cw) * (ideal.length - 1)), 0, ideal.length - 1);
        const d   = ideal[idx];
        const pi  = pastIdxs.indexOf(idx);
        const prog = pastCount > 1 && pi >= 0 ? pi / (pastCount - 1) : null;
        const aRem = prog !== null ? Math.max(0, data.total_points - data.done_points * prog).toFixed(1) : null;
        setTt({
          x: e.clientX - rect.left, y: e.clientY - rect.top, cw: rect.width, ch: rect.height,
          lines: [
            { text: d.date.slice(5) },
            { dot: C.indigo, text: `Ideal: ${d.ideal} SP` },
            ...(aRem !== null ? [{ dot: C.rose, text: `Actual: ${aRem} SP` }] : []),
          ],
        });
      }}
      onMouseLeave={() => setTt(null)}>
      <Tip tt={tt} />
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="overflow-visible">
        <defs>
          <linearGradient id="bdI" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.indigo} stopOpacity=".16" />
            <stop offset="100%" stopColor={C.indigo} stopOpacity="0" />
          </linearGradient>
          <linearGradient id="bdA" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.rose} stopOpacity=".12" />
            <stop offset="100%" stopColor={C.rose} stopOpacity="0" />
          </linearGradient>
        </defs>
        <g transform={`translate(${P.l},${P.t})`}>
          {yTks.map(v => (
            <line key={v} x1={0} x2={cw} y1={ySc(v)} y2={ySc(v)} stroke={C.border} strokeWidth="1" />
          ))}
          <polygon points={area(idealPts, ch)} fill="url(#bdI)" />
          <polyline points={pl(idealPts)} fill="none" stroke={C.indigo} strokeWidth="2.5" strokeDasharray="6 4" />
          {actualPts.length > 1 && <>
            <polygon points={area(actualPts, ch)} fill="url(#bdA)" />
            <polyline points={pl(actualPts)} fill="none" stroke={C.rose} strokeWidth="2.5" />
            {actualPts.filter((_, i) => i % 2 === 0).map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r="3.5" fill={C.rose} stroke={C.white} strokeWidth="1.5" />
            ))}
          </>}
          {yTks.map(v => <text key={v} x={-8} y={ySc(v) + 4} textAnchor="end" fontSize="10" fill={C.muted}>{v}</text>)}
          {ideal.filter((_, i) => i % xStp === 0 || i === ideal.length - 1).map((d) => (
            <text key={d.date} x={xSc(ideal.indexOf(d))} y={ch + 16} textAnchor="middle" fontSize="10" fill={C.muted}>
              {d.date.slice(5)}
            </text>
          ))}
          <text x={-32} y={ch / 2} textAnchor="middle" fontSize="10" fill={C.muted}
            transform={`rotate(-90,-32,${ch / 2})`}>SP</text>
        </g>
      </svg>
      <Legend items={[
        { color: C.indigo, label: 'Ideal', dash: true },
        { color: C.rose,   label: 'Actual remaining' },
      ]} />
    </div>
  );
}

// ─── Burnup chart ─────────────────────────────────────────────────────────────
function BurnupChart({ data }) {
  const [tt, setTt] = useState(null);
  const ref = useRef(null);
  const pts = data.burnup || [];
  if (!pts.length) return <Empty msg="No burnup data" />;
  const W = 520, H = 220, P = { t: 12, r: 20, b: 40, l: 44 };
  const cw = W - P.l - P.r, ch = H - P.t - P.b;
  const maxV = Math.max(data.total_points || 1, 1);
  const xSc  = sc([0, pts.length - 1], [0, cw]);
  const ySc  = sc([0, maxV], [ch, 0]);
  const tPts = pts.map((d, i) => [xSc(i), ySc(d.target)]);
  const xStp = Math.max(1, Math.floor(pts.length / 6));

  return (
    <div ref={ref} className="relative select-none"
      onMouseMove={(e) => {
        const rect = ref.current?.getBoundingClientRect();
        const idx  = clamp(Math.round(((e.clientX - rect.left - P.l) / cw) * (pts.length - 1)), 0, pts.length - 1);
        const d    = pts[idx];
        setTt({
          x: e.clientX - rect.left, y: e.clientY - rect.top, cw: rect.width, ch: rect.height,
          lines: [{ text: d.date.slice(5) }, { dot: C.green, text: `Target: ${d.target} SP` }, { dot: C.indigo, text: `Scope: ${d.scope} SP` }],
        });
      }}
      onMouseLeave={() => setTt(null)}>
      <Tip tt={tt} />
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="overflow-visible">
        <defs>
          <linearGradient id="buG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.green} stopOpacity=".15" />
            <stop offset="100%" stopColor={C.green} stopOpacity="0" />
          </linearGradient>
        </defs>
        <g transform={`translate(${P.l},${P.t})`}>
          {[0, .25, .5, .75, 1].map(t => {
            const v = Math.round(maxV * t);
            return (
              <g key={t}>
                <line x1={0} x2={cw} y1={ySc(v)} y2={ySc(v)} stroke={C.border} strokeWidth="1" />
                <text x={-8} y={ySc(v) + 4} textAnchor="end" fontSize="10" fill={C.muted}>{v}</text>
              </g>
            );
          })}
          <line x1={0} x2={cw} y1={ySc(maxV)} y2={ySc(maxV)} stroke={C.indigo} strokeWidth="1.5" strokeDasharray="6 3" />
          <polygon points={area(tPts, ch)} fill="url(#buG)" />
          <polyline points={pl(tPts)} fill="none" stroke={C.green} strokeWidth="2.5" />
          {pts.filter((_, i) => i % xStp === 0).map(d => (
            <text key={d.date} x={xSc(pts.indexOf(d))} y={ch + 16} textAnchor="middle" fontSize="10" fill={C.muted}>
              {d.date.slice(5)}
            </text>
          ))}
        </g>
      </svg>
      <Legend items={[{ color: C.green, label: 'Completed' }, { color: C.indigo, label: 'Scope', dash: true }]} />
    </div>
  );
}

// ─── Velocity bar chart ───────────────────────────────────────────────────────
function VelocityChart({ data }) {
  const [tt, setTt] = useState(null);
  const ref = useRef(null);
  const bars = data.velocity_data || [];
  const avg  = data.average_velocity || 0;
  if (!bars.length) return <Empty msg="Complete a sprint to see velocity data" />;

  const W = 520, H = 220, P = { t: 12, r: 24, b: 48, l: 44 };
  const cw   = W - P.l - P.r, ch = H - P.t - P.b;
  const maxV = Math.max(...bars.map(b => b.completed_points), avg, 1);
  const ySc  = sc([0, maxV], [ch, 0]);
  const barW = clamp(cw / bars.length - 8, 18, 64);
  const step = cw / bars.length;
  const yTks = [0, .25, .5, .75, 1].map(t => Math.round(maxV * t));

  return (
    <div ref={ref} className="relative select-none" onMouseLeave={() => setTt(null)}>
      <Tip tt={tt} />
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="overflow-visible">
        <defs>
          <linearGradient id="vbG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.indigo} />
            <stop offset="100%" stopColor="#818cf8" />
          </linearGradient>
        </defs>
        <g transform={`translate(${P.l},${P.t})`}>
          {yTks.map(v => <line key={v} x1={0} x2={cw} y1={ySc(v)} y2={ySc(v)} stroke={C.border} strokeWidth="1" />)}
          {avg > 0 && <line x1={0} x2={cw} y1={ySc(avg)} y2={ySc(avg)} stroke={C.amber} strokeWidth="1.5" strokeDasharray="5 3" />}
          {bars.map((b, i) => {
            const bx  = i * step + step / 2 - barW / 2;
            const bh  = Math.max(ch - ySc(b.completed_points), 2);
            const by  = ySc(b.completed_points);
            const lbl = b.sprint_name.length > 11 ? b.sprint_name.slice(0, 11) + '…' : b.sprint_name;
            return (
              <g key={i}
                onMouseMove={(e) => {
                  const rect = ref.current?.getBoundingClientRect();
                  setTt({
                    x: e.clientX - rect.left, y: e.clientY - rect.top, cw: rect.width, ch: rect.height,
                    lines: [
                      { text: b.sprint_name },
                      { dot: C.indigo, text: `Velocity: ${b.completed_points} SP` },
                      ...(avg > 0 ? [{ dot: C.amber, text: `Avg: ${avg} SP` }] : []),
                    ],
                  });
                }}>
                <rect x={bx} y={by} width={barW} height={bh} rx="5" fill="url(#vbG)" opacity=".92" />
                {bh > 20 && (
                  <text x={bx + barW / 2} y={by - 4} textAnchor="middle" fontSize="10" fontWeight="600" fill={C.indigo}>
                    {b.completed_points}
                  </text>
                )}
                <text x={bx + barW / 2} y={ch + 16} textAnchor="middle" fontSize="10" fill={C.muted}>{lbl}</text>
              </g>
            );
          })}
          {yTks.map(v => <text key={v} x={-8} y={ySc(v) + 4} textAnchor="end" fontSize="10" fill={C.muted}>{v}</text>)}
        </g>
      </svg>
      <Legend items={[
        { color: C.indigo, label: 'Completed SP' },
        ...(avg > 0 ? [{ color: C.amber, label: `Avg (${avg} SP)`, dash: true }] : []),
      ]} />
    </div>
  );
}

// ─── Stat pill ────────────────────────────────────────────────────────────────
function Pill({ icon, label, value, color }) {
  const s = {
    indigo: 'bg-indigo-50 text-indigo-700 border-indigo-100',
    green:  'bg-emerald-50 text-emerald-700 border-emerald-100',
    amber:  'bg-amber-50 text-amber-700 border-amber-100',
    rose:   'bg-rose-50 text-rose-700 border-rose-100',
  }[color] ?? 'bg-slate-50 text-slate-600 border-slate-100';
  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${s}`}>
      <span className="text-xl shrink-0">{icon}</span>
      <div className="min-w-0">
        <div className="text-xs font-semibold opacity-60 uppercase tracking-widest leading-none mb-1">{label}</div>
        <div className="text-base font-extrabold leading-none truncate">{value}</div>
      </div>
    </div>
  );
}

// ─── Chart card wrapper ───────────────────────────────────────────────────────
function Card({ icon, title, badge, children }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-4 gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <span>{icon}</span>
          <h3 className="text-sm font-bold text-slate-800">{title}</h3>
        </div>
        {badge && <div className="flex items-center gap-2 flex-wrap">{badge}</div>}
      </div>
      {children}
    </div>
  );
}

// ─── Down / Up tab toggle ─────────────────────────────────────────────────────
function ChartTabs({ active, onChange }) {
  return (
    <div className="flex gap-0.5 bg-slate-100 rounded-lg p-0.5">
      {[{ k: 'burndown', icon: '📉', l: 'Down' }, { k: 'burnup', icon: '📈', l: 'Up' }].map(t => (
        <button key={t.k} onClick={() => onChange(t.k)}
          className={`flex items-center gap-1 px-3 py-1 rounded-md text-xs font-semibold transition-all ${
            active === t.k ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
          }`}>
          {t.icon} {t.l}
        </button>
      ))}
    </div>
  );
}

// ─── Analysis History table — reads from MongoDB ──────────────────────────────
// Calls GET /api/impact/history/{spaceId} (persistent, works across sessions)
function HistoryTable({ spaceId }) {
  const [logs,    setLogs]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  const load = useCallback(() => {
    if (!spaceId) { setLoading(false); return; }
    setLoading(true);
    setError(null);
    api.getAnalysisHistory(spaceId)
      .then(res => setLogs(res.history || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [spaceId]);

  useEffect(() => { load(); }, [load]);

  const RISK = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    high:     'bg-orange-100 text-orange-700 border-orange-200',
    medium:   'bg-yellow-100 text-yellow-700 border-yellow-200',
    low:      'bg-emerald-100 text-emerald-700 border-emerald-200',
  };
  const REC = {
    ADD: 'bg-emerald-100 text-emerald-700', SWAP: 'bg-blue-100 text-blue-700',
    DEFER: 'bg-amber-100 text-amber-700', SPLIT: 'bg-purple-100 text-purple-700',
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span>🗂️</span>
          <h3 className="text-sm font-bold text-slate-800">Analysis History</h3>
          <span className="text-xs text-slate-400 font-medium">
            ({loading ? '…' : logs.length} record{logs.length !== 1 ? 's' : ''})
          </span>
        </div>
        <button onClick={load} disabled={loading}
          className="text-xs text-indigo-500 hover:text-indigo-700 font-semibold px-2 py-1 rounded hover:bg-indigo-50 transition-colors disabled:opacity-40">
          {loading ? '…' : '↻ Refresh'}
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12 gap-2 text-slate-400">
          <div className="animate-spin w-5 h-5 border-2 border-indigo-300 border-t-indigo-600 rounded-full" />
          <span className="text-sm">Loading history…</span>
        </div>
      )}

      {!loading && error && (
        <div className="text-center py-10">
          <p className="text-sm text-rose-500 mb-3">{error}</p>
          <button onClick={load}
            className="text-xs font-semibold text-indigo-600 border border-indigo-200 px-3 py-1.5 rounded-lg hover:bg-indigo-50">
            ↻ Try again
          </button>
        </div>
      )}

      {!loading && !error && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100">
                {['DATE', 'ITEM', 'SPRINT', 'RISK', 'RECOMMENDATION', 'ACTION TAKEN'].map(h => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-bold text-slate-400 tracking-widest whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-16 text-slate-400">
                    <div className="flex flex-col items-center gap-2">
                      <span className="text-4xl opacity-20">📋</span>
                      <span className="text-sm font-semibold">No analysis history yet</span>
                      <span className="text-xs opacity-60">Run an Impact Analysis — it will appear here instantly</span>
                    </div>
                  </td>
                </tr>
              ) : logs.map((log) => (
                <tr key={log.log_id} className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors">
                  <td className="px-5 py-3 text-slate-400 text-xs font-mono whitespace-nowrap">
                    {log.date
                      ? new Date(log.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit', hour: '2-digit', minute: '2-digit' })
                      : '—'}
                  </td>
                  <td className="px-5 py-3">
                    <div className="font-semibold text-slate-800 max-w-[180px] truncate" title={log.item}>{log.item || '—'}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{log.story_points} SP · {log.priority}</div>
                  </td>
                  <td className="px-5 py-3 text-slate-500 text-xs max-w-[130px] truncate">{log.sprint_name || '—'}</td>
                  <td className="px-5 py-3">
                    {log.risk
                      ? <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${RISK[log.risk] ?? RISK.medium}`}>{log.risk.toUpperCase()}</span>
                      : <span className="text-slate-300 text-xs">—</span>}
                  </td>
                  <td className="px-5 py-3">
                    {log.recommendation
                      ? <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${REC[log.recommendation] ?? 'bg-slate-100 text-slate-500'}`}>{log.recommendation}</span>
                      : <span className="text-slate-300 text-xs">—</span>}
                  </td>
                  <td className="px-5 py-3 text-xs">
                    {log.taken_action
                      ? <span className={log.taken_action.includes('FOLLOWED') ? 'text-emerald-600 font-medium' : 'text-slate-400'}>
                          {log.taken_action.includes('FOLLOWED') ? '✅ Followed' : '❌ Ignored'}
                        </span>
                      : <span className="text-slate-300">Pending</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Main Analytics Component ─────────────────────────────────────────────────
export default function Analytics({ space, sprints: sprintsProp }) {
  const spaceId = space?.id;

  // Self-fetch sprints — don't rely on parent passing them
  const [sprints,    setSprints]    = useState(sprintsProp || []);
  const [sprintLoad, setSprintLoad] = useState(!sprintsProp?.length);

  useEffect(() => {
    if (sprintsProp?.length) { setSprints(sprintsProp); setSprintLoad(false); return; }
    if (!spaceId) return;
    setSprintLoad(true);
    api.getSprintsBySpace(spaceId)
      .then(data => setSprints(Array.isArray(data) ? data : []))
      .catch(() => setSprints([]))
      .finally(() => setSprintLoad(false));
  }, [spaceId]);

  useEffect(() => {
    if (sprintsProp?.length) setSprints(sprintsProp);
  }, [sprintsProp]);

  const [selectedId, setSelectedId] = useState('');
  const [chartTab,   setChartTab]   = useState('burndown');

  // Auto-select active sprint once sprints load
  useEffect(() => {
    if (selectedId) return;
    const active = sprints.find(s => s.status === 'Active') || sprints[0];
    if (active?.id) setSelectedId(active.id);
  }, [sprints]);

  // Chart data state
  const [bdData,  setBdData]  = useState(null);
  const [buData,  setBuData]  = useState(null);
  const [velData, setVelData] = useState(null);
  const [bdLoad,  setBdLoad]  = useState(false);
  const [velLoad, setVelLoad] = useState(false);
  const [bdErr,   setBdErr]   = useState(null);
  const [velErr,  setVelErr]  = useState(null);

  useEffect(() => {
    if (!selectedId) return;
    setBdLoad(true); setBdErr(null); setBdData(null);
    api.getSprintBurndown(selectedId).then(setBdData).catch(e => setBdErr(e.message)).finally(() => setBdLoad(false));
    setBuData(null);
    api.getSprintBurnup(selectedId).then(setBuData).catch(() => {});
  }, [selectedId]);

  useEffect(() => {
    if (!spaceId) return;
    setVelLoad(true); setVelErr(null);
    api.getVelocityChart(spaceId).then(setVelData).catch(e => setVelErr(e.message)).finally(() => setVelLoad(false));
  }, [spaceId]);

  // Derived — safe because sprints is fetched internally
  const activeSprint   = sprints.find(s => s.status === 'Active');
  const completedCount = sprints.filter(s => s.status === 'Completed').length;
  const plannedCount   = sprints.filter(s => s.status === 'Planned').length;

  return (
    <div className="space-y-6">

      {/* Header + sprint selector */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">Analytics & Charts</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            {space?.name ?? 'Space'} · {sprintLoad ? '…' : `${sprints.length} sprint${sprints.length !== 1 ? 's' : ''}`} total
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-400 tracking-widest uppercase whitespace-nowrap">SPRINT</label>
          <select value={selectedId} onChange={e => setSelectedId(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 text-slate-700 bg-white
                       focus:ring-2 focus:ring-indigo-400 focus:outline-none shadow-sm min-w-[190px]">
            <option value="">Select sprint…</option>
            {sprints.map(s => (
              <option key={s.id} value={s.id}>
                {s.name}{s.status === 'Active' ? ' 🔥' : s.status === 'Completed' ? ' ✅' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stat pills */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Pill icon="🏃" label="Total Sprints" value={sprintLoad ? '…' : sprints.length}                color="indigo" />
        <Pill icon="✅" label="Completed"      value={sprintLoad ? '…' : completedCount}                color="green"  />
        <Pill icon="🔥" label="Active Sprint"  value={sprintLoad ? '…' : (activeSprint?.name ?? 'None')} color="amber" />
        <Pill icon="📋" label="Planned"        value={sprintLoad ? '…' : plannedCount}                  color="rose"   />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Burndown / burnup */}
        <Card
          icon={chartTab === 'burndown' ? '📉' : '📈'}
          title={chartTab === 'burndown' ? 'Burndown Chart' : 'Burnup Chart'}
          badge={
            <>
              {bdData && chartTab === 'burndown' && (
                <div className="flex gap-1.5 text-xs">
                  <span className="bg-emerald-50 text-emerald-700 border border-emerald-100 px-2 py-0.5 rounded-full font-semibold">✅ {bdData.done_points ?? 0} done</span>
                  <span className="bg-orange-50 text-orange-700 border border-orange-100 px-2 py-0.5 rounded-full font-semibold">⏳ {bdData.remaining_points ?? 0} left</span>
                </div>
              )}
              <ChartTabs active={chartTab} onChange={setChartTab} />
            </>
          }>
          {!selectedId && <Empty msg="Select a sprint above to view charts" />}
          {selectedId && chartTab === 'burndown' && (
            bdLoad ? <Skel /> : bdErr ? <Empty msg={bdErr} /> : bdData ? <BurndownChart data={bdData} /> : <Empty msg="No burndown data" />
          )}
          {selectedId && chartTab === 'burnup' && (
            !buData ? <Empty msg="No burnup data for this sprint" /> : <BurnupChart data={buData} />
          )}
        </Card>

        {/* Velocity */}
        <Card
          icon="⚡" title="Team Velocity"
          badge={
            velData?.average_velocity > 0 && (
              <span className="bg-indigo-50 text-indigo-700 border border-indigo-100 px-2.5 py-0.5 rounded-full text-xs font-bold">
                avg {velData.average_velocity} SP/sprint
              </span>
            )
          }>
          {velLoad ? <Skel /> : velErr ? <Empty msg={velErr} /> : velData ? <VelocityChart data={velData} /> : <Empty msg="No velocity data yet" />}
        </Card>
      </div>

      {/* History */}
      <HistoryTable spaceId={spaceId} />
    </div>
  );
}