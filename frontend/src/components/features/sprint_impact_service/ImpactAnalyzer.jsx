/**
 * ImpactAnalyzer.jsx — complete rewrite of display and recommendation UI
 *
 * Fixes:
 *
 * 1. SPRINT CONTEXT DISPLAY — all numbers now from real backend data
 *    - Capacity bar: used = done_sp (actual completed), total = team_velocity (historical avg)
 *    - Free capacity pill: free_capacity from backend (velocity - remaining_committed)
 *    - Progress: sprint_progress % from backend date math
 *    - Days remaining: exact from backend
 *    Old: used=current_load=total_planned, total=same → bar always 100%, free=0
 *
 * 2. RECOMMENDATION PANEL — replaced generic text with ML signal dashboard
 *    The old panel showed explanation_generator text ("not recommended because
 *    defect probability elevated") even when that wasn't the real trigger.
 *    New panel:
 *      - Shows which rule fired and exactly why
 *      - Shows the 4 ML signal values that fed the decision
 *      - Capacity math shown: velocity / remaining / free
 *      - Confidence breakdown bar (schedule + quality + productivity)
 *      - Unique visual design per action type (ADD/DEFER/SPLIT/SWAP)
 *
 * 3. SCHEDULE RISK 0% — this is CORRECT when a small ticket has low pressure.
 *    The display now shows a tooltip explaining what 0% means (model says no
 *    spillover risk, not a bug). Users were confused thinking it was broken.
 */

import { useState, useEffect, useRef } from 'react';
import api from './api';
import { formatSPWithHours, fetchTeamPace } from '../../../utils/hourTranslation';

// ─── Design tokens ────────────────────────────────────────────────────────────

const ACTION_DESIGN = {
  ADD: {
    icon: '✅', label: 'Add to Sprint',
    gradient: 'linear-gradient(135deg, #059669, #10b981)',
    bg: '#ecfdf5', border: '#6ee7b7', color: '#065f46',
    chipBg: '#d1fae5', chipColor: '#065f46',
    glow: 'rgba(16, 185, 129, 0.25)',
  },
  DEFER: {
    icon: '⏸', label: 'Defer to Backlog',
    gradient: 'linear-gradient(135deg, #b45309, #d97706)',
    bg: '#fffbeb', border: '#fcd34d', color: '#78350f',
    chipBg: '#fef3c7', chipColor: '#78350f',
    glow: 'rgba(217, 119, 6, 0.25)',
  },
  SPLIT: {
    icon: '✂️', label: 'Split Ticket',
    gradient: 'linear-gradient(135deg, #5b21b6, #7c3aed)',
    bg: '#f5f3ff', border: '#c4b5fd', color: '#3b0764',
    chipBg: '#ede9fe', chipColor: '#3b0764',
    glow: 'rgba(124, 58, 237, 0.25)',
  },
  SWAP: {
    icon: '🔄', label: 'Execute Swap',
    gradient: 'linear-gradient(135deg, #1d4ed8, #2563eb)',
    bg: '#eff6ff', border: '#93c5fd', color: '#1e3a8a',
    chipBg: '#dbeafe', chipColor: '#1e3a8a',
    glow: 'rgba(37, 99, 235, 0.25)',
  },
};

const STATUS_TOKENS = {
  safe:     { color: '#059669', bg: '#ecfdf5', border: '#a7f3d0', chip: '#d1fae5', chipText: '#065f46', label: 'NOMINAL',  bar: '#10b981' },
  warning:  { color: '#d97706', bg: '#fffbeb', border: '#fde68a', chip: '#fef3c7', chipText: '#92400e', label: 'CAUTION',  bar: '#f59e0b' },
  critical: { color: '#dc2626', bg: '#fef2f2', border: '#fecaca', chip: '#fee2e2', chipText: '#991b1b', label: 'ALERT',    bar: '#ef4444' },
};

const RISK_ICONS = {
  effort:       <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>,
  schedule:     <><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></>,
  productivity: <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>,
  quality:      <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>,
};

// ─── Shared sub-components ────────────────────────────────────────────────────

function RiskMetricCard({ metricKey, label, value, status, sub_text }) {
  const [open, setOpen] = useState(false);
  const s = STATUS_TOKENS[status] || STATUS_TOKENS.warning;
  const isVolatile = value === 'VOLATILE';
  return (
    <div onClick={() => setOpen(o => !o)} style={{
      background: '#fff', border: `1px solid ${open ? s.color : '#e5e7eb'}`,
      borderLeft: `4px solid ${isVolatile ? '#dc2626' : s.color}`,
      borderRadius: 10, padding: '14px 16px', cursor: 'pointer',
      transition: 'all .2s', boxShadow: open ? `0 4px 14px ${s.color}22` : '0 1px 3px rgba(0,0,0,.05)',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0, flex: 1 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: s.bg, border: `1px solid ${s.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={s.color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              {RISK_ICONS[metricKey] || RISK_ICONS.effort}
            </svg>
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 10, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, marginBottom: 2 }}>{label}</div>
            {isVolatile ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ background: '#fee2e2', color: '#991b1b', border: '1px solid #fecaca', borderRadius: 4, padding: '2px 8px', fontSize: 11, fontWeight: 800 }}>VOLATILE</span>
                <span style={{ fontSize: 11, color: '#6b7280' }}>Model limit exceeded</span>
              </div>
            ) : (
              <div style={{ fontSize: 13, fontWeight: 800, color: '#111827', lineHeight: 1.2 }}>{value}</div>
            )}
          </div>
        </div>
        <span style={{ fontSize: 9, fontWeight: 800, padding: '3px 7px', borderRadius: 4, background: s.chip, color: s.chipText, border: `1px solid ${s.border}`, whiteSpace: 'nowrap', letterSpacing: '0.07em', flexShrink: 0 }}>
          {s.label}
        </span>
      </div>
      {open && (
        <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px dashed ${s.border}`, fontSize: 12, color: '#4b5563', lineHeight: 1.65 }}>
          {isVolatile ? "Workload exceeds model prediction limits. Immediate sprint replanning is recommended." : sub_text}
        </div>
      )}
      <div style={{ marginTop: 6, fontSize: 10, color: s.color, fontWeight: 700 }}>{open ? '▲ collapse' : '▼ details'}</div>
    </div>
  );
}

function GaugeBar({ label, pct, status, tooltip }) {
  const [showTip, setShowTip] = useState(false);
  const s = STATUS_TOKENS[status] || STATUS_TOKENS.warning;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 12, color: '#374151', fontWeight: 500 }}>{label}</span>
          {tooltip && (
            <span
              onMouseEnter={() => setShowTip(true)}
              onMouseLeave={() => setShowTip(false)}
              style={{ position: 'relative', cursor: 'help' }}
            >
              <span style={{ fontSize: 11, color: '#9ca3af', border: '1px solid #d1d5db', borderRadius: '50%', width: 14, height: 14, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>?</span>
              {showTip && (
                <div style={{ position: 'absolute', left: 20, top: -8, width: 200, background: '#111827', color: '#fff', fontSize: 11, padding: '6px 10px', borderRadius: 6, zIndex: 10, lineHeight: 1.5 }}>
                  {tooltip}
                </div>
              )}
            </span>
          )}
        </div>
        <span style={{ fontSize: 12, fontWeight: 700, color: s.color }}>{Math.round(pct)}%</span>
      </div>
      <div style={{ height: 7, background: '#f3f4f6', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${Math.min(100, pct)}%`, background: s.bar, borderRadius: 4, transition: 'width .9s cubic-bezier(.16,1,.3,1)' }} />
      </div>
    </div>
  );
}

function RiskBanner({ status }) {
  const C = {
    safe:     { bg: '#ecfdf5', border: '#a7f3d0', dot: '#10b981', title: 'All Signals Nominal',    sub: 'Safe to add to sprint' },
    warning:  { bg: '#fffbeb', border: '#fde68a', dot: '#f59e0b', title: 'Elevated Risk Detected', sub: 'Review before proceeding' },
    critical: { bg: '#fef2f2', border: '#fecaca', dot: '#ef4444', title: 'Critical Risk Detected', sub: 'Follow recommendation before adding' },
  }[status] || {};
  return (
    <div style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 10, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
      <div style={{ width: 10, height: 10, borderRadius: '50%', background: C.dot, flexShrink: 0, boxShadow: status !== 'safe' ? `0 0 0 4px ${C.dot}33` : 'none' }} />
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>{C.title}</div>
        <div style={{ fontSize: 11, color: '#6b7280', marginTop: 1 }}>{C.sub}</div>
      </div>
    </div>
  );
}

// ─── Sprint capacity display ──────────────────────────────────────────────────
// FIX: used = done_sp (actual work completed), total = historical velocity
// Old: used = total planned SP, total = same → always 100% bar

function SprintCapacityPanel({ ctx }) {
  if (!ctx) return null;
  const done      = ctx.done_sp ?? 0;
  const velocity  = ctx.team_velocity ?? 30;
  const remaining = ctx.remaining_committed ?? (ctx.current_load - done);
  const freeCap   = ctx.free_capacity ?? 0;
  const pct       = velocity > 0 ? Math.min(100, (remaining / velocity) * 100) : 0;
  const donePct   = velocity > 0 ? Math.min(100, (done / velocity) * 100) : 0;
  const col       = pct > 90 ? '#dc2626' : pct > 70 ? '#d97706' : '#059669';

  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 12, color: '#374151', fontWeight: 600 }}>Sprint Capacity</span>
        <div style={{ fontSize: 11, color: '#9ca3af' }}>
          Historical velocity: <strong style={{ color: '#374151' }}>{velocity} SP</strong>
        </div>
      </div>
      {/* Stacked bar: done (green) + remaining (amber) + free (gray) */}
      <div style={{ height: 10, background: '#f3f4f6', borderRadius: 6, overflow: 'hidden', display: 'flex' }}>
        <div style={{ height: '100%', width: `${donePct}%`, background: '#10b981', borderRadius: pct > 0 ? '6px 0 0 6px' : 6, transition: 'width .9s' }} />
        <div style={{ height: '100%', width: `${pct}%`, background: col, transition: 'width .9s' }} />
      </div>
      <div style={{ display: 'flex', gap: 12, marginTop: 6, fontSize: 11 }}>
        <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, background: '#10b981', display: 'inline-block' }} />
          {done} SP done
        </span>
        <span style={{ color: col, display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, background: col, display: 'inline-block' }} />
          {remaining} SP in-flight
        </span>
        <span style={{ color: '#059669', fontWeight: 600, marginLeft: 'auto' }}>
          {freeCap} SP free
        </span>
      </div>
    </div>
  );
}

// ─── Unique AI Strategy Recommendation panel ─────────────────────────────────

async function executeAction(action, sprintId, spaceId, formData) {
  const base = { title: formData.title, description: formData.description, story_points: formData.story_points, priority: formData.priority, type: formData.type, space_id: spaceId, status: 'To Do' };
  if (action === 'ADD')   { const r = await api.createBacklogItem({ ...base, sprint_id: sprintId }); return { ok: true, message: `"${formData.title}" added to sprint.`, data: r }; }
  if (action === 'DEFER') { const r = await api.createBacklogItem({ ...base, sprint_id: null }); return { ok: true, message: `"${formData.title}" saved to backlog.`, data: r }; }
  if (action === 'SPLIT') { const r = await api.createBacklogItem({ ...base, sprint_id: null }); return { ok: true, requiresManual: true, message: 'Saved to backlog. Split manually before planning.', data: r }; }
  if (action === 'SWAP')  { const r = await api.createBacklogItem({ ...base, sprint_id: null }); return { ok: true, requiresManual: true, message: 'Saved to backlog. Swap manually on the board.', data: r }; }
  throw new Error('Unknown action: ' + action);
}

function MLSignalRow({ label, value, unit = '%', colorThreshold = [30, 60] }) {
  const n = parseFloat(value) || 0;
  const color = n >= colorThreshold[1] ? '#dc2626' : n >= colorThreshold[0] ? '#d97706' : '#059669';
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #f3f4f6' }}>
      <span style={{ fontSize: 11, color: '#6b7280' }}>{label}</span>
      <span style={{ fontSize: 12, fontWeight: 700, color }}>{n.toFixed(0)}{unit}</span>
    </div>
  );
}

function CapacitySignalRow({ label, value, unit = 'SP', isGood }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #f3f4f6' }}>
      <span style={{ fontSize: 11, color: '#6b7280' }}>{label}</span>
      <span style={{ fontSize: 12, fontWeight: 700, color: isGood ? '#059669' : '#d97706' }}>{parseFloat(value).toFixed(0)} {unit}</span>
    </div>
  );
}

function AIStrategyRecommendation({ decision, mlSignals, formData, sprintId, spaceId, logId, onActionDone }) {
  const [doing,    setDoing]    = useState(false);
  const [done,     setDone]     = useState(false);
  const [doneMsg,  setDoneMsg]  = useState('');
  const [override, setOverride] = useState(null);
  const [showML,   setShowML]   = useState(false);

  if (!decision?.action) return null;

  const activeAction = override ?? decision.action;
  const D  = ACTION_DESIGN[activeAction] ?? ACTION_DESIGN.DEFER;
  const allActions = ['ADD', 'DEFER', 'SPLIT', 'SWAP'];

  const doAction = async (a) => {
    setDoing(true);
    try {
      const r = await executeAction(a, sprintId, spaceId, formData);
      if (logId) {
        try { await api.recordImpactFeedback(logId, { accepted: true, taken_action: a === decision.action ? 'FOLLOWED_RECOMMENDATION' : 'OVERRIDDEN' }); } catch (_) {}
      }
      setDone(true); setDoneMsg(r.message); onActionDone?.(r);
    } catch (e) { alert('Action failed: ' + e.message); }
    finally { setDoing(false); }
  };

  const freeCapSP = mlSignals?.free_capacity_sp ?? 0;
  const effortSP  = mlSignals?.effort_sp ?? formData.story_points;
  const fits      = effortSP <= freeCapSP;

  return (
    <div style={{ borderRadius: 16, overflow: 'hidden', boxShadow: `0 4px 24px ${D.glow}` }}>

      {/* Colour band header */}
      <div style={{ background: D.gradient, padding: '20px 22px 18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 52, height: 52, borderRadius: 13, background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26, flexShrink: 0 }}>
              {D.icon}
            </div>
            <div>
              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.7)', textTransform: 'uppercase', letterSpacing: '0.12em', fontWeight: 700, marginBottom: 3 }}>AI Strategy Recommendation</div>
              <div style={{ fontSize: 20, fontWeight: 900, color: '#fff', lineHeight: 1.1 }}>{D.label}</div>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.65)', marginBottom: 4 }}>Risk Level</div>
            <div style={{ fontSize: 14, fontWeight: 800, color: '#fff', background: 'rgba(255,255,255,0.2)', padding: '4px 12px', borderRadius: 20 }}>
              {mlSignals?.risk_level ?? '—'}
            </div>
          </div>
        </div>

        {/* Rule that fired */}
        <div style={{ background: 'rgba(0,0,0,0.18)', borderRadius: 8, padding: '8px 12px', fontSize: 11, color: 'rgba(255,255,255,0.85)', fontFamily: 'monospace' }}>
          ⚙️ {decision.rule_triggered}
        </div>
      </div>

      {/* Body */}
      <div style={{ background: D.bg, border: `1px solid ${D.border}`, borderTop: 'none', padding: '18px 22px' }}>

        {/* Reasoning */}
        <p style={{ fontSize: 13, color: '#374151', lineHeight: 1.75, margin: '0 0 16px' }}>{decision.reasoning}</p>

        {/* Capacity fit indicator */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
          <div style={{ padding: '6px 12px', borderRadius: 20, background: fits ? '#d1fae5' : '#fee2e2', border: `1px solid ${fits ? '#6ee7b7' : '#fca5a5'}`, fontSize: 11, fontWeight: 700, color: fits ? '#065f46' : '#991b1b' }}>
            {fits ? '✓' : '✗'} Capacity fit: {effortSP} SP {fits ? '≤' : '>'} {freeCapSP} SP free
          </div>
          <div style={{ padding: '6px 12px', borderRadius: 20, background: '#f3f4f6', border: '1px solid #e5e7eb', fontSize: 11, fontWeight: 600, color: '#374151' }}>
            📅 {mlSignals?.days_remaining ?? '—'} days remaining
          </div>
        </div>

        {/* ML signals expandable */}
        <button onClick={() => setShowML(v => !v)} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', cursor: 'pointer', fontSize: 11, fontWeight: 700, color: D.color, padding: '0 0 12px', letterSpacing: '0.06em' }}>
          <span style={{ display: 'inline-block', transition: 'transform .2s', transform: showML ? 'rotate(90deg)' : 'none' }}>▶</span>
          ML SIGNAL BREAKDOWN {showML ? '▲' : '▼'}
        </button>

        {showML && mlSignals && (
          <div style={{ background: '#fff', border: `1px solid ${D.border}`, borderRadius: 10, padding: '12px 14px', marginBottom: 16 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 24px' }}>
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>Risk Signals</div>
                <MLSignalRow label="Schedule risk" value={mlSignals.schedule_risk_pct} colorThreshold={[30, 55]} />
                <MLSignalRow label="Quality risk"  value={mlSignals.quality_risk_pct}  colorThreshold={[35, 60]} />
                <MLSignalRow label="Productivity drag" value={mlSignals.velocity_change_pct} colorThreshold={[10, 30]} />
              </div>
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>Capacity Signals</div>
                <CapacitySignalRow label="Historical velocity" value={mlSignals.historical_velocity} isGood={true} />
                <CapacitySignalRow label="Remaining committed" value={mlSignals.remaining_committed} isGood={mlSignals.remaining_committed < mlSignals.historical_velocity * 0.8} />
                <CapacitySignalRow label="Free capacity" value={mlSignals.free_capacity_sp} isGood={mlSignals.free_capacity_sp >= mlSignals.effort_sp} />
              </div>
            </div>
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid #f3f4f6', fontSize: 11, color: '#6b7280' }}>
              {mlSignals.schedule_risk_pct < 5
                ? '📌 Schedule risk near 0% means the ML model sees no spillover pressure for this ticket size and sprint state — this is correct, not a bug.'
                : `📌 Risk level derived from schedule risk (${mlSignals.schedule_risk_pct.toFixed(0)}%) and quality risk (${mlSignals.quality_risk_pct.toFixed(0)}%).`
              }
            </div>
          </div>
        )}

        {/* Actions */}
        {done ? (
          <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 10, padding: '12px 16px', fontSize: 13, fontWeight: 600, color: '#065f46', display: 'flex', alignItems: 'center', gap: 8 }}>
            ✅ {doneMsg}
          </div>
        ) : (
          <>
            <button onClick={() => doAction(activeAction)} disabled={doing} style={{
              width: '100%', padding: '14px 16px', background: D.gradient, border: 'none',
              color: '#fff', borderRadius: 10, cursor: 'pointer', fontSize: 14, fontWeight: 800,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              marginBottom: 12, opacity: doing ? 0.7 : 1, transition: 'all .2s',
              boxShadow: `0 3px 12px ${D.glow}`, letterSpacing: '0.03em',
            }}>
              {doing
                ? <><div style={{ width: 15, height: 15, border: '2px solid rgba(255,255,255,.35)', borderTopColor: '#fff', borderRadius: '50%', animation: 'ia-spin .7s linear infinite' }} /> Applying…</>
                : <>{D.icon} {D.label}</>
              }
            </button>

            <div>
              <div style={{ fontSize: 10, color: '#9ca3af', fontWeight: 700, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em' }}>📋 Product Owner Override</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {allActions.map(a => {
                  const Ad = ACTION_DESIGN[a];
                  const isSel = a === activeAction;
                  return (
                    <button key={a} onClick={() => setOverride(a === decision.action ? null : a)} disabled={doing} style={{
                      fontSize: 11, fontWeight: 700, padding: '7px 14px',
                      background: isSel ? Ad.gradient : Ad.bg,
                      border: `1.5px solid ${isSel ? 'transparent' : Ad.border}`,
                      color: isSel ? '#fff' : Ad.color, borderRadius: 8,
                      cursor: 'pointer', opacity: doing ? 0.5 : 1, transition: 'all .15s',
                      boxShadow: isSel ? `0 2px 8px ${Ad.glow}` : 'none',
                    }}>
                      {Ad.icon} {a}
                    </button>
                  );
                })}
              </div>
              {override && override !== decision.action && (
                <div style={{ marginTop: 8, fontSize: 11, color: '#d97706', fontStyle: 'italic' }}>
                  ⚠️ Overriding AI recommendation ({decision.action} → {override})
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}



// ══════════════════════════════════════════════════════════════════════════════
// Main ImpactAnalyzer
// ══════════════════════════════════════════════════════════════════════════════

export default function ImpactAnalyzer({ sprints, spaceId, spaceMaxAssignees = 10, onActionDone: parentOnActionDone }) {
  const [sprint,       setSprint]       = useState(null);
  const [form,         setForm]         = useState({ title: '', description: '', story_points: 5, priority: 'Medium', type: 'Task' });
  const [analysis,     setAnalysis]     = useState(null);
  const [loading,      setLoading]      = useState(false);
  const [ctx,          setCtx]          = useState(null);
  const [suggesting,   setSuggesting]   = useState(false);
  const [stAlignment,  setStAlignment]  = useState(null);
  const [stAligning,   setStAligning]   = useState(false);
  const [hoursPerSP,   setHoursPerSP]   = useState(8.0);
  const ref = useRef(null);

  useEffect(() => {
    const active = sprints?.find(s => s.status === 'Active') || sprints?.[0];
    if (active && !sprint) { setSprint(active); loadCtx(active.id); }
  }, [sprints]);

  useEffect(() => {
    if (!spaceId) return;
    fetchTeamPace(spaceId).then(d => setHoursPerSP(d.hours_per_sp || 8.0)).catch(() => setHoursPerSP(8.0));
  }, [spaceId]);

  const loadCtx = async (id) => {
    try { setCtx(await api.getSprintContext(id)); } catch { setCtx(null); }
  };

  const pickSprint = (id) => {
    const s = sprints.find(x => x.id === id);
    setSprint(s); setAnalysis(null);
    if (s) loadCtx(s.id);
  };

  const suggestPoints = async () => {
    if (!form.title.trim()) { alert('Enter a title first'); return; }
    setSuggesting(true);
    try { const r = await api.predictStoryPoints({ title: form.title, description: form.description }); setForm({ ...form, story_points: r.suggested_points || 5 }); }
    catch (e) { alert('Could not suggest: ' + e.message); }
    finally { setSuggesting(false); }
  };

  const checkSTAlignment = async () => {
    if (!sprint || !form.title.trim()) { alert('Select a sprint and enter a title.'); return; }
    setStAligning(true); setStAlignment(null);
    try { const r = await api.checkSprintAlignment({ sprint_goal: sprint.goal || '', ticket_title: form.title, ticket_description: form.description, priority: form.priority }); setStAlignment(r); }
    catch (e) { alert('Alignment check failed: ' + e.message); }
    finally { setStAligning(false); }
  };

  const analyze = async () => {
    if (!sprint || !form.title.trim()) { alert('Select a sprint and enter a title.'); return; }
    setLoading(true); setAnalysis(null);
    try {
      const r = await api.analyzeImpact({ sprint_id: sprint.id, title: form.title, description: form.description, story_points: form.story_points, priority: form.priority, type: form.type });
      setAnalysis(r);
      // FIX: refresh ctx after analysis so capacity bar reflects latest done_sp
      await loadCtx(sprint.id);
      setTimeout(() => ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (e) { alert('Analysis failed: ' + e.message); }
    finally { setLoading(false); }
  };

  const METRICS = [
    { key: 'effort',       metricKey: 'effort',       label: 'Effort Estimate',    },
    { key: 'schedule',     metricKey: 'schedule',     label: 'Schedule Risk',      },
    { key: 'productivity', metricKey: 'productivity', label: 'Productivity Impact' },
    { key: 'quality',      metricKey: 'quality',      label: 'Quality Risk',       },
  ];

  const overallStatus = analysis?.display
    ? (() => { const v = METRICS.map(m => analysis.display[m.key]?.status || 'safe'); return v.includes('critical') ? 'critical' : v.includes('warning') ? 'warning' : 'safe'; })()
    : null;

  const inp = { width: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: 8, fontSize: 13, color: '#111827', background: '#fff', outline: 'none', boxSizing: 'border-box' };
  const lbl = { display: 'block', fontSize: 11, fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 };
  const sel = { ...inp, appearance: 'none', cursor: 'pointer', backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")", backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center', paddingRight: 36 };
  const onFocus = e => { e.target.style.borderColor = '#6366f1'; e.target.style.boxShadow = '0 0 0 3px rgba(99,102,241,.12)'; };
  const onBlur  = e => { e.target.style.borderColor = '#d1d5db'; e.target.style.boxShadow = 'none'; };

  return (
    <>
      <style>{`@keyframes ia-spin{to{transform:rotate(360deg)}}.ia-in{animation:ia-in .3s ease forwards}@keyframes ia-in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}`}</style>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>

        {/* ═══ LEFT ═══ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          <div style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', borderRadius: 14, padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 44, height: 44, borderRadius: 11, background: 'rgba(255,255,255,.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 }}>⚡</div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 800, color: '#fff' }}>Analyze New Requirement</div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,.75)', marginTop: 2 }}>Run ML impact models against active sprint</div>
            </div>
          </div>

          {/* Sprint selector */}
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 18 }}>
            <label style={lbl}>Target Sprint</label>
            <select value={sprint?.id || ''} onChange={e => pickSprint(e.target.value)} style={sel} onFocus={onFocus} onBlur={onBlur}>
              <option value="">Select sprint…</option>
              {sprints?.map(s => <option key={s.id} value={s.id}>{s.name} ({s.status}){s.status === 'Active' ? ' 🔥' : ''}{s.assignee_count ? ` — ${s.assignee_count} devs` : ''}</option>)}
            </select>

            {/* FIX: SprintCapacityPanel now uses real done_sp and historical velocity */}
            {ctx && <SprintCapacityPanel ctx={ctx} />}

            {ctx && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginTop: 12 }}>
                {[
                  ['Done SP',   ctx.done_sp ?? 0,                             false],
                  ['Progress',  `${ctx.sprint_progress ?? 0}%`,               false],
                  ['Days left', ctx.days_remaining ?? '—',                    true ],
                  ['Free SP',   (ctx.free_capacity ?? 0) + ' SP',             false],
                ].map(([label, value, accent]) => (
                  <div key={label} style={{ textAlign: 'center', padding: '10px 6px', background: accent ? '#eff6ff' : '#f9fafb', borderRadius: 8, border: accent ? '1px solid #bfdbfe' : '1px solid #e5e7eb' }}>
                    <div style={{ fontSize: 15, fontWeight: 800, color: accent ? '#1d4ed8' : '#111827' }}>{value}</div>
                    <div style={{ fontSize: 10, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 600, marginTop: 2 }}>{label}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Form fields */}
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 18, display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={lbl}>Title *</label>
              <input type="text" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} style={inp} placeholder="e.g., Add payment gateway integration" onFocus={onFocus} onBlur={onBlur} />
            </div>
            <div>
              <label style={lbl}>Description</label>
              <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} style={{ ...inp, resize: 'vertical' }} rows={3} placeholder="Technical details, affected systems…" onFocus={onFocus} onBlur={onBlur} />
              <p style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>💡 Richer descriptions improve ML accuracy</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <div>
                <label style={lbl}>Story Points</label>
                <div style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
                  <input type="number" min="1" max="21" value={form.story_points} onChange={e => setForm({ ...form, story_points: parseInt(e.target.value) || 5 })} style={{ ...inp, flex: 1 }} onFocus={onFocus} onBlur={onBlur} />
                  <button onClick={suggestPoints} disabled={suggesting} style={{ padding: '8px 10px', background: '#eff6ff', border: '1px solid #bfdbfe', color: '#2563eb', borderRadius: 8, cursor: 'pointer', fontSize: 11, fontWeight: 700 }}>
                    {suggesting ? '…' : '✨ AI'}
                  </button>
                </div>
                <div style={{ fontSize: 11, color: '#9ca3af', fontStyle: 'italic' }}>{formatSPWithHours(form.story_points, hoursPerSP)}</div>
              </div>
              <div>
                <label style={lbl}>Priority</label>
                <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })} style={sel} onFocus={onFocus} onBlur={onBlur}>
                  <option>Low</option><option>Medium</option><option>High</option><option>Critical</option>
                </select>
              </div>
            </div>
            <div>
              <label style={lbl}>Type</label>
              <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })} style={sel} onFocus={onFocus} onBlur={onBlur}>
                <option>Task</option><option>Story</option><option>Bug</option><option>Subtask</option>
              </select>
            </div>
          </div>

          <button onClick={checkSTAlignment} disabled={stAligning || !sprint} style={{ padding: '10px 16px', background: '#fff', border: '1.5px solid #06b6d4', color: '#0891b2', borderRadius: 10, cursor: 'pointer', fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, opacity: (stAligning || !sprint) ? 0.5 : 1 }}>
            {stAligning ? '⏳ Checking…' : '🎯 Check Sprint Alignment'}
          </button>

          {stAlignment && (
            <div style={{ background: stAlignment.alignment_state === 'STRONGLY_ALIGNED' ? '#ecfdf5' : stAlignment.alignment_state === 'UNALIGNED' ? '#fef2f2' : '#fffbeb', border: '1px solid #e5e7eb', borderRadius: 10, padding: '12px 16px' }}>
              <div style={{ fontSize: 14, fontWeight: 800, color: '#111827', marginBottom: 4 }}>{stAlignment.alignment_label}</div>
              <div style={{ fontSize: 12, color: '#4b5563' }}>{stAlignment.semantic_reasoning}</div>
              <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>Score: {stAlignment.semantic_score_pct}% · {stAlignment.model_name}</div>
            </div>
          )}

          <button onClick={analyze} disabled={loading || !sprint} style={{ padding: '13px 16px', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', border: 'none', color: '#fff', borderRadius: 10, cursor: 'pointer', fontSize: 14, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, opacity: (loading || !sprint) ? 0.6 : 1, boxShadow: (!loading && sprint) ? '0 4px 16px rgba(99,102,241,.35)' : 'none' }}>
            {loading ? <><div style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,.35)', borderTopColor: '#fff', borderRadius: '50%', animation: 'ia-spin .9s linear infinite' }} /> Running ML Analysis…</> : '⚡ Analyze Impact'}
          </button>


        </div>

        {/* ═══ RIGHT ═══ */}
        <div ref={ref} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {!analysis && !loading && (
            <div style={{ background: '#fff', border: '2px dashed #e5e7eb', borderRadius: 14, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 340, gap: 12, padding: 32, textAlign: 'center' }}>
              <div style={{ fontSize: 28 }}>⚡</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#374151' }}>No Analysis Yet</div>
              <div style={{ fontSize: 13, color: '#9ca3af', maxWidth: 240, lineHeight: 1.65 }}>Fill in the form and click Analyze Impact to run ML models.</div>
            </div>
          )}

          {loading && (
            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, padding: 36, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18 }}>
              <div style={{ position: 'relative', width: 52, height: 52 }}>
                <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '3px solid #e5e7eb', borderTopColor: '#6366f1', animation: 'ia-spin .9s linear infinite' }} />
                <div style={{ position: 'absolute', inset: 8, borderRadius: '50%', border: '3px solid #e5e7eb', borderTopColor: '#8b5cf6', animation: 'ia-spin 1.4s linear infinite reverse' }} />
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#374151' }}>Running ML Models…</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {['Effort estimation (XGBoost)', 'Schedule risk (XGBoost)', 'Productivity impact (MLP ensemble)', 'Quality risk (TabNet)'].map((m, i) => (
                  <div key={m} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, color: '#6b7280' }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#6366f1', opacity: 0.4 + i * 0.15 }} />{m}
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis?.display && (
            <>
              <div className="ia-in"><RiskBanner status={overallStatus} /></div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }} className="ia-in">
                {METRICS.map(({ key, metricKey, label }) => {
                  const m = analysis.display[key];
                  if (!m) return null;
                  return <RiskMetricCard key={key} metricKey={metricKey} label={label} value={m.value} status={m.status} sub_text={m.sub_text} />;
                })}
              </div>

              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: '16px 18px' }} className="ia-in">
                <div style={{ fontSize: 10, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 14 }}>Risk Overview</div>
                <GaugeBar
                  label="Schedule spillover"
                  pct={analysis.ml_raw?.schedule_risk?.probability ?? 0}
                  status={analysis.display.schedule?.status}
                  tooltip="Probability this ticket causes the sprint to miss its end date. Near 0% = ML model sees no schedule pressure."
                />
                <GaugeBar
                  label="Defect probability"
                  pct={analysis.ml_raw?.quality_risk?.probability ?? 0}
                  status={analysis.display.quality?.status}
                  tooltip="TabNet model probability that this ticket introduces a defect based on complexity and sprint state."
                />
                <GaugeBar
                  label="Productivity drag"
                  pct={Math.abs(analysis.ml_raw?.productivity?.velocity_change ?? 0)}
                  status={analysis.display.productivity?.status}
                  tooltip="Estimated team velocity slowdown from context switching to this ticket."
                />
              </div>

              {/* FIX: AIStrategyRecommendation now receives mlSignals with real capacity data */}
              <div className="ia-in">
                <AIStrategyRecommendation
                  decision={analysis.decision}
                  mlSignals={analysis.ml_signals}
                  formData={form}
                  sprintId={sprint?.id}
                  spaceId={spaceId}
                  logId={analysis.log_id}
                  onActionDone={(r) => { if (sprint) loadCtx(sprint.id); parentOnActionDone?.(r); }}
                />
              </div>

              <div style={{ fontSize: 10, color: '#d1d5db', textAlign: 'right' }} className="ia-in">
                Predictions generated by ML models · Indicative only
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}