/**
 * ImpactAnalyzer.jsx — Light theme, fully legible, matches AgileSense-AI design language
 * 
 * MODULE 3 & 4 Integration:
 * - MODULE 3: Displays story points with hours translation (formatSPWithHours)
 * - MODULE 4: Checks sprint goal alignment and flags scope creep
 */

import { useState, useEffect, useRef } from 'react';
import api from './api';
import { formatSPWithHours, fetchTeamPace } from '../../../utils/hourTranslation';
import { checkSprintAlignment, isScopeCreep, getAlignmentColors, getScopeCreepWarning } from '../../../utils/sprintAlignment';

// ─── Constants ────────────────────────────────────────────────────────────────
const ACTION_META = {
  ADD:    { icon: '✅', label: 'Add to Sprint',    color: '#059669', bg: '#ecfdf5', border: '#6ee7b7', text: '#065f46' },
  SWAP:   { icon: '🔄', label: 'Execute Swap',     color: '#2563eb', bg: '#eff6ff', border: '#93c5fd', text: '#1e3a8a' },
  DEFER:  { icon: '⏸',  label: 'Defer to Backlog', color: '#d97706', bg: '#fffbeb', border: '#fcd34d', text: '#78350f' },
  SPLIT:  { icon: '✂️', label: 'Split Ticket',     color: '#7c3aed', bg: '#f5f3ff', border: '#c4b5fd', text: '#3b0764' },
  ACCEPT: { icon: '✅', label: 'Accept',           color: '#059669', bg: '#ecfdf5', border: '#6ee7b7', text: '#065f46' },
};

const STATUS = {
  safe:     { color: '#059669', bg: '#ecfdf5', border: '#a7f3d0', chip: '#d1fae5', chipText: '#065f46', label: 'NOMINAL',  bar: '#10b981' },
  warning:  { color: '#d97706', bg: '#fffbeb', border: '#fde68a', chip: '#fef3c7', chipText: '#92400e', label: 'CAUTION',  bar: '#f59e0b' },
  critical: { color: '#dc2626', bg: '#fef2f2', border: '#fecaca', chip: '#fee2e2', chipText: '#991b1b', label: 'ALERT',    bar: '#ef4444' },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
async function executeAction(action, recommendation, sprintId, spaceId, formData) {
  const base = { title: formData.title, description: formData.description, story_points: formData.story_points, priority: formData.priority, type: formData.type, space_id: spaceId, status: 'To Do' };
  if (action === 'ADD' || action === 'ACCEPT') {
    const r = await api.createBacklogItem({ ...base, sprint_id: sprintId });
    return { ok: true, message: `"${formData.title}" added to sprint.`, data: r };
  }
  if (action === 'SWAP') {
    const t = recommendation?.target_ticket;
    if (!t?.id) throw new Error('No swap target in recommendation.');
    await api.updateBacklogItem(t.id, { sprint_id: null });
    const r = await api.createBacklogItem({ ...base, sprint_id: sprintId });
    return { ok: true, message: `Swapped out "${t.title}". "${formData.title}" added to sprint.`, data: r };
  }
  if (action === 'DEFER') {
    const r = await api.createBacklogItem({ ...base, sprint_id: null });
    return { ok: true, message: `"${formData.title}" saved to backlog.`, data: r };
  }
  if (action === 'SPLIT') {
    const r = await api.createBacklogItem({ ...base, sprint_id: null });
    return { ok: true, requiresManual: true, message: `Saved to backlog. Split manually before sprint planning.`, data: r };
  }
  throw new Error('Unknown action: ' + action);
}

async function logFeedback(logId, accepted, takenAction) {
  if (!logId) return;
  try { await api.recordImpactFeedback(logId, { accepted, taken_action: takenAction }); } catch (_) {}
}

// ─── CapacityBar ──────────────────────────────────────────────────────────────
// MODULE 3: Now displays both SP and Hours translation
function CapacityBar({ used, total, hoursPerSP = 8.0 }) {
  const pct  = total > 0 ? Math.min(100, (used / total) * 100) : 0;
  const col  = pct > 90 ? '#dc2626' : pct > 70 ? '#d97706' : '#059669';
  const free = Math.max(0, total - used);
  
  // Calculate hours (MODULE 3)
  const usedHours = Math.round(used * hoursPerSP * 10) / 10;
  const totalHours = Math.round(total * hoursPerSP * 10) / 10;
  const freeHours = Math.round(free * hoursPerSP * 10) / 10;
  
  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', marginBottom:6 }}>
        <span style={{ fontSize:12, color:'#374151', fontWeight:600 }}>Sprint Capacity</span>
        <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:2 }}>
          <span style={{ fontSize:12, fontWeight:800, color:'#111827' }}>{used} / {total} SP</span>
          <span style={{ fontSize:10, color:'#9ca3af', fontStyle:'italic' }}>({usedHours} / {totalHours} hrs)</span>
        </div>
      </div>
      <div style={{ height:8, background:'#e5e7eb', borderRadius:6, overflow:'hidden' }}>
        <div style={{ height:'100%', width:`${pct}%`, background:col, borderRadius:6, transition:'width 0.9s cubic-bezier(.16,1,.3,1)' }} />
      </div>
      <div style={{ display:'flex', justifyContent:'space-between', marginTop:5 }}>
        <span style={{ fontSize:11, color:'#9ca3af' }}>{Math.round(pct)}% used</span>
        <span style={{ fontSize:11, color:free < 5 ? '#dc2626' : '#059669', fontWeight:600 }}>{free} SP ({freeHours} hrs) remaining</span>
      </div>
    </div>
  );
}

// ─── StatPill ─────────────────────────────────────────────────────────────────
function StatPill({ label, value, accent }) {
  return (
    <div style={{ textAlign:'center', padding:'10px 6px', background: accent ? '#eff6ff' : '#f9fafb', borderRadius:8, border: accent ? '1px solid #bfdbfe' : '1px solid #e5e7eb' }}>
      <div style={{ fontSize:17, fontWeight:800, color: accent ? '#1d4ed8' : '#111827' }}>{value}</div>
      <div style={{ fontSize:10, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.07em', fontWeight:600, marginTop:2 }}>{label}</div>
    </div>
  );
}

// ─── RiskCard ─────────────────────────────────────────────────────────────────
const RISK_ICONS = {
  0: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,                                          // quality
  1: <><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></>,  // schedule
  2: <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>,                                                // productivity
  3: <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>,                          // effort
};

function RiskCard({ label, value, status, sub_text, index }) {
  const [open, setOpen] = useState(false);
  const s = STATUS[status] || STATUS.warning;
  return (
    <div
      onClick={() => setOpen(o => !o)}
      style={{ background:'#fff', border:`1px solid ${open ? s.color : '#e5e7eb'}`, borderLeft:`4px solid ${s.color}`, borderRadius:10, padding:'14px 16px', cursor:'pointer', transition:'all .2s', boxShadow: open ? `0 4px 14px ${s.color}22` : '0 1px 3px rgba(0,0,0,.05)' }}
    >
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:8 }}>
        <div style={{ display:'flex', alignItems:'center', gap:10, minWidth:0, flex:1 }}>
          <div style={{ width:32, height:32, borderRadius:8, background:s.bg, border:`1px solid ${s.border}`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={s.color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              {RISK_ICONS[index] || RISK_ICONS[0]}
            </svg>
          </div>
          <div style={{ minWidth:0 }}>
            <div style={{ fontSize:10, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:700, marginBottom:2 }}>{label}</div>
            <div style={{ fontSize:13, fontWeight:800, color:'#111827', lineHeight:1.2 }}>{value}</div>
          </div>
        </div>
        <span style={{ fontSize:9, fontWeight:800, padding:'3px 7px', borderRadius:4, background:s.chip, color:s.chipText, border:`1px solid ${s.border}`, whiteSpace:'nowrap', letterSpacing:'0.07em', flexShrink:0 }}>
          {s.label}
        </span>
      </div>
      {open && (
        <div style={{ marginTop:10, paddingTop:10, borderTop:`1px dashed ${s.border}`, fontSize:12, color:'#4b5563', lineHeight:1.65 }}>
          {sub_text}
        </div>
      )}
      <div style={{ marginTop:6, fontSize:10, color:s.color, fontWeight:700 }}>{open ? '▲ collapse' : '▼ details'}</div>
    </div>
  );
}

// ─── GaugeBar ─────────────────────────────────────────────────────────────────
function GaugeBar({ label, pct, status }) {
  const s = STATUS[status] || STATUS.warning;
  return (
    <div style={{ marginBottom:12 }}>
      <div style={{ display:'flex', justifyContent:'space-between', marginBottom:5 }}>
        <span style={{ fontSize:12, color:'#374151', fontWeight:500 }}>{label}</span>
        <span style={{ fontSize:12, fontWeight:700, color:s.color }}>{Math.round(pct)}%</span>
      </div>
      <div style={{ height:7, background:'#f3f4f6', borderRadius:4, overflow:'hidden' }}>
        <div style={{ height:'100%', width:`${Math.min(100,pct)}%`, background:s.bar, borderRadius:4, transition:'width .9s cubic-bezier(.16,1,.3,1)' }} />
      </div>
    </div>
  );
}

// ─── RecommendationCard ───────────────────────────────────────────────────────
function RecommendationCard({ recommendation, explanation, formData, sprintId, spaceId, logId, onActionDone }) {
  const [doing,     setDoing]     = useState(false);
  const [done,      setDone]      = useState(false);
  const [doneMsg,   setDoneMsg]   = useState('');
  const [planOpen,  setPlanOpen]  = useState(false);

  const type = recommendation?.recommendation_type ?? 'DEFER';
  const meta = ACTION_META[type] ?? ACTION_META.DEFER;
  const alts = Object.keys(ACTION_META).filter(k => k !== type && k !== 'ACCEPT');

  const doAction = async (a) => {
    setDoing(true);
    try {
      const r = await executeAction(a, recommendation, sprintId, spaceId, formData);
      await logFeedback(logId, true, a === type ? 'FOLLOWED_RECOMMENDATION' : 'IGNORED_RECOMMENDATION');
      setDone(true); setDoneMsg(r.message); onActionDone?.(r);
    } catch (e) { alert('Action failed: ' + e.message); }
    finally { setDoing(false); }
  };

  return (
    <div style={{ background:meta.bg, border:`1.5px solid ${meta.border}`, borderRadius:14, padding:20 }}>
      {/* header */}
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:12, marginBottom:14 }}>
        <div style={{ display:'flex', alignItems:'center', gap:12 }}>
          <div style={{ width:46, height:46, borderRadius:12, background:'#fff', border:`1px solid ${meta.border}`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:22, flexShrink:0, boxShadow:'0 1px 4px rgba(0,0,0,.07)' }}>
            {meta.icon}
          </div>
          <div>
            <div style={{ fontSize:10, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.1em', fontWeight:700, marginBottom:2 }}>AI Recommendation</div>
            <div style={{ fontSize:16, fontWeight:800, color:meta.color }}>{explanation?.short_title ?? type}</div>
          </div>
        </div>
        <span style={{ fontSize:10, fontWeight:800, padding:'4px 10px', borderRadius:6, background:'#fff', color:meta.color, border:`1px solid ${meta.border}`, letterSpacing:'0.1em', whiteSpace:'nowrap' }}>
          {type}
        </span>
      </div>

      {/* reasoning */}
      <p style={{ fontSize:13, color:'#374151', lineHeight:1.7, marginBottom:14 }}>{recommendation?.reasoning}</p>

      {/* detailed explanation */}
      {explanation?.detailed_explanation && explanation.detailed_explanation !== recommendation?.reasoning && (
        <div style={{ background:'#fff', border:`1px solid ${meta.border}`, borderRadius:8, padding:'10px 14px', marginBottom:14, fontSize:12, color:'#4b5563', lineHeight:1.65 }}>
          {explanation.detailed_explanation}
        </div>
      )}

      {/* swap target */}
      {recommendation?.target_ticket && (
        <div style={{ background:'#eff6ff', border:'1px solid #bfdbfe', borderRadius:8, padding:'10px 14px', marginBottom:14, display:'flex', alignItems:'center', gap:10 }}>
          <span style={{ fontSize:18 }}>🎯</span>
          <div>
            <div style={{ fontSize:10, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.1em', fontWeight:700 }}>Swap Target</div>
            <div style={{ fontSize:13, fontWeight:700, color:'#1e3a8a' }}>{recommendation.target_ticket.title}</div>
            <div style={{ fontSize:11, color:'#6b7280', marginTop:2 }}>{recommendation.target_ticket.story_points} SP · {recommendation.target_ticket.priority} · {recommendation.target_ticket.status}</div>
          </div>
        </div>
      )}

      {/* action plan */}
      {recommendation?.action_plan && Object.keys(recommendation.action_plan).length > 0 && (
        <div style={{ marginBottom:14 }}>
          <button onClick={() => setPlanOpen(o => !o)} style={{ background:'none', border:'none', cursor:'pointer', fontSize:11, fontWeight:700, color:meta.color, display:'flex', alignItems:'center', gap:5, padding:0, letterSpacing:'0.05em' }}>
            <span style={{ transition:'transform .2s', transform:planOpen?'rotate(90deg)':'none', display:'inline-block' }}>▶</span> Action Plan
          </button>
          {planOpen && (
            <div style={{ marginTop:8, paddingLeft:14, borderLeft:`3px solid ${meta.border}` }}>
              {Object.entries(recommendation.action_plan).map(([k, v]) => (
                <div key={k} style={{ fontSize:12, color:'#374151', marginBottom:5, display:'flex', gap:8, lineHeight:1.6 }}>
                  <span style={{ color:meta.color, fontWeight:700, flexShrink:0 }}>→</span>{v}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* risk summary */}
      {explanation?.risk_summary && (
        <div style={{ fontSize:11, color:'#9ca3af', marginBottom:16, fontFamily:'monospace' }}>{explanation.risk_summary}</div>
      )}

      {/* CTA */}
      {done ? (
        <div style={{ background:'#ecfdf5', border:'1px solid #a7f3d0', borderRadius:8, padding:'10px 14px', fontSize:13, fontWeight:600, color:'#065f46', display:'flex', alignItems:'center', gap:8 }}>
          ✅ {doneMsg}
        </div>
      ) : (
        <>
          <button onClick={() => doAction(type)} disabled={doing}
            style={{ width:'100%', padding:'12px 16px', background:meta.color, border:'none', color:'#fff', borderRadius:9, cursor:'pointer', fontSize:13, fontWeight:800, display:'flex', alignItems:'center', justifyContent:'center', gap:8, marginBottom:10, opacity:doing?.7:1, transition:'all .2s', boxShadow:`0 3px 10px ${meta.color}44`, letterSpacing:'0.03em' }}
          >
            {doing
              ? <><div style={{ width:14, height:14, border:'2px solid rgba(255,255,255,.35)', borderTopColor:'#fff', borderRadius:'50%', animation:'ia-spin .7s linear infinite' }} /> Applying…</>
              : <>{meta.icon} {meta.label}</>}
          </button>
          <div>
            <div style={{ fontSize:10, color:'#9ca3af', fontWeight:700, marginBottom:8, textTransform:'uppercase', letterSpacing:'0.08em' }}>Or choose manually</div>
            <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
              {alts.map(a => {
                const m = ACTION_META[a];
                return (
                  <button key={a} onClick={() => doAction(a)} disabled={doing}
                    style={{ fontSize:11, fontWeight:700, padding:'5px 12px', background:m.bg, border:`1px solid ${m.border}`, color:m.color, borderRadius:6, cursor:'pointer', opacity:doing?.5:1, transition:'all .15s' }}
                  >
                    {m.icon} {a}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ─── GoalAlignmentStrip ───────────────────────────────────────────────────────
function GoalAlignmentStrip({ goalAlignment, onClear }) {
  if (!goalAlignment) return null;
  const S = {
    ACCEPT:   { color:'#059669', bg:'#ecfdf5', border:'#a7f3d0', icon:'✅' },
    CONSIDER: { color:'#2563eb', bg:'#eff6ff', border:'#bfdbfe', icon:'🔍' },
    EVALUATE: { color:'#d97706', bg:'#fffbeb', border:'#fde68a', icon:'⚡' },
    DEFER:    { color:'#dc2626', bg:'#fef2f2', border:'#fecaca', icon:'⏸' },
  }[goalAlignment.final_recommendation] || { color:'#6b7280', bg:'#f9fafb', border:'#e5e7eb', icon:'📋' };
  return (
    <div style={{ background:S.bg, border:`1.5px solid ${S.border}`, borderRadius:12, padding:'14px 16px' }}>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:12, marginBottom:8 }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <span style={{ fontSize:20 }}>{S.icon}</span>
          <div>
            <div style={{ fontSize:10, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.1em', fontWeight:700 }}>Goal Alignment</div>
            <div style={{ fontSize:14, fontWeight:800, color:S.color }}>{goalAlignment.final_recommendation}</div>
          </div>
        </div>
        <button onClick={onClear} style={{ background:'none', border:'none', cursor:'pointer', color:'#9ca3af', fontSize:16, padding:4, lineHeight:1 }}>✕</button>
      </div>
      <p style={{ fontSize:12, color:'#374151', lineHeight:1.6, marginBottom:8 }}>{goalAlignment.recommendation_reason}</p>
      <div style={{ fontSize:11, color:'#4b5563', borderTop:`1px dashed ${S.border}`, paddingTop:8 }}>
        <strong>Next: </strong>{goalAlignment.next_steps}
      </div>
    </div>
  );
}

// ─── RiskBanner ───────────────────────────────────────────────────────────────
function RiskBanner({ status }) {
  const C = {
    safe:     { bg:'#ecfdf5', border:'#a7f3d0', dot:'#10b981', title:'All Signals Nominal',       sub:'Safe to add to sprint' },
    warning:  { bg:'#fffbeb', border:'#fde68a', dot:'#f59e0b', title:'Elevated Risk Detected',    sub:'Review caution items before proceeding' },
    critical: { bg:'#fef2f2', border:'#fecaca', dot:'#ef4444', title:'Critical Risk Detected',    sub:'Follow recommendation before adding to sprint' },
  }[status] || {};
  return (
    <div style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:10, padding:'12px 16px', display:'flex', alignItems:'center', gap:12 }}>
      <div style={{ width:10, height:10, borderRadius:'50%', background:C.dot, flexShrink:0, boxShadow: status!=='safe' ? `0 0 0 4px ${C.dot}33` : 'none' }} />
      <div>
        <div style={{ fontSize:13, fontWeight:700, color:'#111827' }}>{C.title}</div>
        <div style={{ fontSize:11, color:'#6b7280', marginTop:1 }}>{C.sub}</div>
      </div>
    </div>
  );
}

// ─── ScopeCreepWarning (MODULE 4 — Alignment check) ─────────────────────────
function ScopeCreepWarning({ alignmentScore, taskTitle, onDismiss }) {
  if (!isScopeCreep(alignmentScore, 0.4)) return null;
  
  const colors = getAlignmentColors('UNALIGNED');
  const warning = getScopeCreepWarning(alignmentScore, taskTitle);
  
  return (
    <div style={{ background:colors.bg, border:`1.5px solid ${colors.border}`, borderRadius:12, padding:'14px 16px', marginBottom:16, display:'flex', alignItems:'flex-start', gap:12 }}>
      <div style={{ width:32, height:32, borderRadius:8, background:'#fff', border:`1px solid ${colors.border}`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:18, flexShrink:0 }}>
        ⚠️
      </div>
      <div style={{ flex:1, minWidth:0 }}>
        <div style={{ fontSize:13, fontWeight:700, color:colors.accent, marginBottom:4 }}>Potential Scope Creep</div>
        <div style={{ fontSize:12, color:colors.text, lineHeight:1.5 }}>{warning}</div>
        <div style={{ fontSize:11, color:'#9ca3af', marginTop:6 }}>
          Alignment Score: <strong style={{ color:colors.accent }}>{Math.round(alignmentScore * 100)}%</strong> (threshold: 40%)
        </div>
      </div>
      {onDismiss && (
        <button 
          onClick={onDismiss}
          style={{ background:'none', border:'none', cursor:'pointer', color:colors.border, fontSize:18, padding:0, lineHeight:1, flexShrink:0 }}
        >
          ✕
        </button>
      )}
    </div>
  );
}

// ─── STAlignmentCard (Phase 1 — alignment state only, no action verbs) ───────
function STAlignmentCard({ result, onClear }) {
  const [expanded, setExpanded] = useState(false);

  const PALETTE = {
    CRITICAL_BLOCKER: { accent: '#dc2626', light: '#fef2f2', border: '#fecaca', chipBg: '#fee2e2', chipText: '#991b1b' },
    STRONGLY_ALIGNED: { accent: '#059669', light: '#ecfdf5', border: '#a7f3d0', chipBg: '#d1fae5', chipText: '#065f46' },
    PARTIALLY_ALIGNED:{ accent: '#2563eb', light: '#eff6ff', border: '#bfdbfe', chipBg: '#dbeafe', chipText: '#1e3a8a' },
    WEAKLY_ALIGNED:   { accent: '#d97706', light: '#fffbeb', border: '#fde68a', chipBg: '#fef3c7', chipText: '#92400e' },
    UNALIGNED:        { accent: '#6b7280', light: '#f9fafb', border: '#e5e7eb', chipBg: '#f3f4f6', chipText: '#374151' },
  };

  const OVERLAP_LABEL = { high: 'High', medium: 'Medium', low: 'Low', none: 'None' };

  if (!result?.alignment_state) return null;

  const p   = PALETTE[result.alignment_state] ?? PALETTE.UNALIGNED;
  const pct = result.semantic_score_pct ?? 0;
  const barColor = pct >= 55 ? '#059669' : pct >= 35 ? '#d97706' : '#dc2626';

  return (
    <div style={{ background: p.light, border: `1.5px solid ${p.border}`, borderRadius: 12, padding: '14px 16px', position: 'relative' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 38, height: 38, borderRadius: 10, background: '#fff', border: `1px solid ${p.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>
            🎯
          </div>
          <div>
            <div style={{ fontSize: 10, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, marginBottom: 2 }}>
              Phase 1 · Sprint Alignment · <span style={{ color: '#6b7280', fontStyle: 'italic', textTransform: 'none', letterSpacing: 0 }}>{result.model_name}</span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 800, color: p.accent }}>{result.alignment_label ?? result.alignment_state}</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ textAlign: 'center', background: '#fff', border: `1px solid ${p.border}`, borderRadius: 8, padding: '4px 10px', minWidth: 52 }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: barColor, lineHeight: 1 }}>{pct}%</div>
            <div style={{ fontSize: 9, color: '#9ca3af', fontWeight: 700, letterSpacing: '0.06em', marginTop: 1 }}>MATCH</div>
          </div>
          <button onClick={onClear} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9ca3af', fontSize: 15, padding: 4 }}>✕</button>
        </div>
      </div>

      {/* Score bar */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: '#6b7280', fontWeight: 600 }}>Semantic similarity score</span>
          <span style={{ fontSize: 11, fontWeight: 700, color: barColor }}>{pct} / 100</span>
        </div>
        <div style={{ height: 7, background: '#e5e7eb', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${pct}%`, background: barColor, borderRadius: 4, transition: 'width .9s cubic-bezier(.16,1,.3,1)' }} />
        </div>
        <div style={{ position: 'relative', height: 14 }}>
          {[{ v: 35, label: '35%' }, { v: 55, label: '55%' }].map(({ v, label }) => (
            <div key={v} style={{ position: 'absolute', left: `${v}%`, top: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', transform: 'translateX(-50%)' }}>
              <div style={{ width: 1, height: 5, background: '#d1d5db' }} />
              <span style={{ fontSize: 9, color: '#9ca3af' }}>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
        {result.is_critical_blocker && (
          <span style={{ fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 5, background: '#fee2e2', color: '#991b1b', border: '1px solid #fecaca' }}>🚨 BLOCKER</span>
        )}
        <span style={{ fontSize: 10, fontWeight: 600, padding: '3px 8px', borderRadius: 5, background: result.epic_aligned ? '#d1fae5' : '#f3f4f6', color: result.epic_aligned ? '#065f46' : '#6b7280', border: `1px solid ${result.epic_aligned ? '#a7f3d0' : '#e5e7eb'}` }}>
          Epic {result.epic_aligned ? '✓ aligned' : '✗ mismatch'}
        </span>
        <span style={{ fontSize: 10, fontWeight: 600, padding: '3px 8px', borderRadius: 5, background: result.component_overlap === 'none' ? '#f3f4f6' : '#dbeafe', color: result.component_overlap === 'none' ? '#6b7280' : '#1e3a8a', border: `1px solid ${result.component_overlap === 'none' ? '#e5e7eb' : '#bfdbfe'}` }}>
          Components: {OVERLAP_LABEL[result.component_overlap] ?? result.component_overlap}
        </span>
      </div>

      {/* Expandable */}
      <button onClick={() => setExpanded(x => !x)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 11, fontWeight: 700, color: p.accent, display: 'flex', alignItems: 'center', gap: 4, padding: 0 }}>
        <span style={{ display: 'inline-block', transition: 'transform .2s', transform: expanded ? 'rotate(90deg)' : 'none' }}>▶</span>
        {expanded ? 'Hide detail' : 'Show layer analysis'}
      </button>

      {expanded && (
        <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ background: '#fff', border: `1px solid ${p.border}`, borderRadius: 8, padding: '10px 12px' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>L1 · Blocker Detection</div>
            <p style={{ fontSize: 12, color: '#374151', lineHeight: 1.6, margin: 0 }}>{result.blocker_reason}</p>
          </div>
          <div style={{ background: '#fff', border: `1px solid ${p.border}`, borderRadius: 8, padding: '10px 12px' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>L2 · Semantic Similarity</div>
            <p style={{ fontSize: 12, color: '#374151', lineHeight: 1.6, margin: 0 }}>{result.semantic_reasoning}</p>
          </div>
          <div style={{ background: '#fff', border: `1px solid ${p.border}`, borderRadius: 8, padding: '10px 12px' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>L3 · Metadata Traceability</div>
            <p style={{ fontSize: 12, color: '#374151', lineHeight: 1.6, margin: 0 }}>{result.metadata_details}</p>
            {result.matched_components?.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                {result.matched_components.map(c => (
                  <span key={c} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: '#dbeafe', color: '#1e3a8a', border: '1px solid #bfdbfe', fontWeight: 600 }}>{c}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── DecisionEngineCard (Phase 3 — AI recommendation + manual override) ───────
function DecisionEngineCard({ decision, formData, sprintId, spaceId, logId, onActionDone }) {
  const [doing,    setDoing]    = useState(false);
  const [done,     setDone]     = useState(false);
  const [doneMsg,  setDoneMsg]  = useState('');
  const [override, setOverride] = useState(null);  // user's manual choice

  if (!decision?.action) return null;

  const activeAction = override ?? decision.action;
  const meta = ACTION_META[activeAction] ?? ACTION_META.DEFER;
  const allActions = ['ADD', 'DEFER', 'SPLIT', 'SWAP'];

  const doAction = async (a) => {
    setDoing(true);
    try {
      const r = await executeAction(a, null, sprintId, spaceId, formData);
      await logFeedback(logId, true, a === decision.action ? 'FOLLOWED_RECOMMENDATION' : 'OVERRIDDEN');
      setDone(true); setDoneMsg(r.message); onActionDone?.(r);
    } catch (e) { alert('Action failed: ' + e.message); }
    finally { setDoing(false); }
  };

  return (
    <div style={{ background: meta.bg, border: `1.5px solid ${meta.border}`, borderRadius: 14, padding: 20 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 46, height: 46, borderRadius: 12, background: '#fff', border: `1px solid ${meta.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, flexShrink: 0 }}>
            {meta.icon}
          </div>
          <div>
            <div style={{ fontSize: 10, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, marginBottom: 2 }}>Phase 3 · Decision Engine</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: meta.color }}>🤖 AI Recommends: {decision.action}</div>
          </div>
        </div>
        <span style={{ fontSize: 10, fontWeight: 800, padding: '4px 10px', borderRadius: 6, background: '#fff', color: meta.color, border: `1px solid ${meta.border}`, letterSpacing: '0.1em', whiteSpace: 'nowrap' }}>
          {decision.action}
        </span>
      </div>

      {/* Short title */}
      <div style={{ fontSize: 13, fontWeight: 700, color: meta.color, marginBottom: 8 }}>{decision.short_title}</div>

      {/* Reasoning */}
      <p style={{ fontSize: 12, color: '#374151', lineHeight: 1.7, marginBottom: 10 }}>{decision.reasoning}</p>

      {/* Rule triggered chip */}
      <div style={{ fontSize: 10, color: '#6b7280', background: '#f3f4f6', border: '1px solid #e5e7eb', borderRadius: 6, padding: '4px 10px', display: 'inline-block', marginBottom: 14 }}>
        ⚙️ {decision.rule_triggered}
      </div>

      {done ? (
        <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 8, padding: '10px 14px', fontSize: 13, fontWeight: 600, color: '#065f46', display: 'flex', alignItems: 'center', gap: 8 }}>
          ✅ {doneMsg}
        </div>
      ) : (
        <>
          {/* Primary CTA — active action (AI recommendation or override) */}
          <button onClick={() => doAction(activeAction)} disabled={doing}
            style={{ width: '100%', padding: '12px 16px', background: meta.color, border: 'none', color: '#fff', borderRadius: 9, cursor: 'pointer', fontSize: 13, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 14, opacity: doing ? 0.7 : 1, transition: 'all .2s', boxShadow: `0 3px 10px ${meta.color}44` }}
          >
            {doing
              ? <><div style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,.35)', borderTopColor: '#fff', borderRadius: '50%', animation: 'ia-spin .7s linear infinite' }} /> Applying…</>
              : <>{meta.icon} {meta.label}</>}
          </button>

          {/* Manual override section */}
          <div style={{ borderTop: `1px dashed ${meta.border}`, paddingTop: 12 }}>
            <div style={{ fontSize: 10, color: '#9ca3af', fontWeight: 700, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              📋 Product Owner Override
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {allActions.map(a => {
                const m = ACTION_META[a];
                const isSelected = a === activeAction;
                return (
                  <button key={a} onClick={() => setOverride(a === decision.action ? null : a)} disabled={doing}
                    style={{ fontSize: 11, fontWeight: 700, padding: '6px 14px', background: isSelected ? m.color : m.bg, border: `1.5px solid ${isSelected ? m.color : m.border}`, color: isSelected ? '#fff' : m.color, borderRadius: 7, cursor: 'pointer', opacity: doing ? 0.5 : 1, transition: 'all .15s' }}
                  >
                    {m.icon} {a}
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
  );
}

// ─── ImpactAnalyzer (main) ────────────────────────���───────────────────────────
export default function ImpactAnalyzer({ sprints, spaceId }) {
  const [sprint,    setSprint]    = useState(null);
  const [form,      setForm]      = useState({ title:'', description:'', story_points:5, priority:'Medium', type:'Task' });
  const [analysis,  setAnalysis]  = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [ctx,       setCtx]       = useState(null);
  const [result,    setResult]    = useState(null);
  const [suggesting,  setSuggesting]  = useState(false);
  const [alignment,   setAlignment]   = useState(null);
  const [aligning,    setAligning]    = useState(false);
  const [stAlignment, setStAlignment] = useState(null);   // Phase 1 result
  const [stAligning,  setStAligning]  = useState(false);
  const [decision,    setDecision]    = useState(null);   // Phase 3 result
  
  // MODULE 3: SP to Hours Translation
  const [hoursPerSP,     setHoursPerSP]     = useState(8.0);
  const [loadingPace,    setLoadingPace]    = useState(true);
  
  // MODULE 4: Sprint Goal Alignment
  const [simpleAlignment, setSimpleAlignment] = useState(null);
  const [checkingAlignment, setCheckingAlignment] = useState(false);
  
  const ref = useRef(null);

  useEffect(() => {
  const active = sprints?.find(s => s.status === 'Active') || sprints?.[0];
  if (active && !sprint) { setSprint(active); loadCtx(active.id); }
  }, [sprints]);
  
  // MODULE 3: Load team pace on mount
  useEffect(() => {
    if (!spaceId) return;
    setLoadingPace(true);
    fetchTeamPace(spaceId)
      .then(data => setHoursPerSP(data.hours_per_sp || 8.0))
      .catch(err => {
        console.error('Failed to load team pace:', err);
        setHoursPerSP(8.0);
      })
      .finally(() => setLoadingPace(false));
  }, [spaceId]);

  const loadCtx = async (id) => { try { setCtx(await api.getSprintContext(id)); } catch { setCtx(null); } };

  const pickSprint = (id) => {
    const s = sprints.find(x => x.id === id);
    setSprint(s); setAnalysis(null); setResult(null);
    if (s) loadCtx(s.id);
  };

  const suggestPoints = async () => {
    if (!form.title.trim()) { alert('Enter a title first'); return; }
    setSuggesting(true);
    try { const r = await api.predictStoryPoints({ title: form.title, description: form.description }); setForm({ ...form, story_points: r.suggested_points || 5 }); }
    catch (e) { alert('Could not suggest: ' + e.message); }
    finally { setSuggesting(false); }
  };

  // Legacy classical alignment (kept, not surfaced in main UI)
  const checkAlignment = async () => {
    if (!sprint || !form.title.trim()) { alert('Select a sprint and enter a title'); return; }
    setAligning(true);
    try {
      const r = await api.analyzeSprintGoalAlignment({ sprint_goal: sprint.goal || 'No goal', requirement_title: form.title, requirement_description: form.description, requirement_priority: form.priority, requirement_epic: null, sprint_epic: null, requirement_components: [], sprint_components: [] });
      setAlignment(r);
    } catch (e) { alert('Alignment check failed: ' + e.message); }
    finally { setAligning(false); }
  };

  // MODULE 4: Simple TF-IDF sprint goal alignment (quick scope creep check)
  const checkSimpleAlignment = async () => {
    if (!sprint || !form.title.trim()) { alert('Select a sprint and enter a title'); return; }
    setCheckingAlignment(true);
    setSimpleAlignment(null);
    try {
      const taskDescription = `${form.title} ${form.description}`.trim();
      const r = await checkSprintAlignment(sprint.goal || '', taskDescription);
      setSimpleAlignment(r);
    } catch (e) {
      console.error('Simple alignment check failed:', e);
      alert('Could not check alignment: ' + e.message);
    } finally {
      setCheckingAlignment(false);
    }
  };

  // NEW: Sentence-Transformer alignment — deterministic, zero-latency
  const checkSTAlignment = async () => {
    if (!sprint || !form.title.trim()) { alert('Select a sprint and enter a title first.'); return; }
    setStAligning(true);
    setStAlignment(null);
    try {
      const r = await api.checkSprintAlignment({
        sprint_goal:        sprint.goal || '',
        ticket_title:       form.title,
        ticket_description: form.description,
        priority:           form.priority,
        ticket_epic:        null,
        sprint_epic:        null,
        ticket_components:  [],
        sprint_components:  [],
      });
      setStAlignment(r);
    } catch (e) { alert('Alignment check failed: ' + e.message); }
    finally { setStAligning(false); }
  };

  const analyze = async () => {
    if (!sprint || !form.title.trim()) { alert('Select a sprint and enter a title'); return; }
    setLoading(true); setAnalysis(null); setResult(null); setDecision(null);
    try {
      const r = await api.analyzeImpact({ sprint_id: sprint.id, title: form.title, description: form.description, story_points: form.story_points, priority: form.priority, type: form.type });
      setAnalysis(r);

      // Phase 3 — call Decision Engine with Phase 1 alignment_state + Phase 2 outputs
      const effortSp = r.ml_raw?.effort?.median_sp ?? form.story_points;
      const freeCapacity = Math.max(0, (ctx?.team_velocity || 30) - (ctx?.current_load || 0));
      const scheduleProb = r.ml_raw?.schedule_risk?.probability ?? 0;
      const riskLevel = scheduleProb > 0.65 ? 'HIGH' : scheduleProb > 0.40 ? 'MEDIUM' : 'LOW';
      const alignState = stAlignment?.alignment_state ?? 'STRONGLY_ALIGNED';

      try {
        const d = await api.getDecision({
          alignment_state: alignState,
          effort_sp:       effortSp,
          free_capacity:   freeCapacity,
          priority:        form.priority,
          risk_level:      riskLevel,
        });
        setDecision(d);
      } catch (_) { /* decision engine optional — fall back to existing recommendation */ }

      setTimeout(() => ref.current?.scrollIntoView({ behavior:'smooth', block:'start' }), 100);
    } catch (e) { alert('Analysis failed: ' + e.message); }
    finally { setLoading(false); }
  };

  const used  = ctx?.current_load   || 0;
  const total = ctx?.team_velocity  || Math.max(used, 30);
  const resolvedSpaceId = spaceId || sprint?.space_id || '';

  const METRICS = [
    { key:'effort',       label:'Effort Estimate',     idx:3 },
    { key:'schedule',     label:'Schedule Risk',        idx:1 },
    { key:'productivity', label:'Productivity Impact',  idx:2 },
    { key:'quality',      label:'Quality Risk',         idx:0 },
  ];

  const overallStatus = analysis?.display
    ? (() => { const v = METRICS.map(m => analysis.display[m.key]?.status || 'safe'); return v.includes('critical') ? 'critical' : v.includes('warning') ? 'warning' : 'safe'; })()
    : null;

  // Shared input styles
  const inp = { width:'100%', padding:'9px 12px', border:'1px solid #d1d5db', borderRadius:8, fontSize:13, color:'#111827', background:'#fff', outline:'none', boxSizing:'border-box', transition:'border-color .15s, box-shadow .15s' };
  const lbl = { display:'block', fontSize:11, fontWeight:700, color:'#6b7280', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:6 };
  const sel = { ...inp, appearance:'none', cursor:'pointer', backgroundImage:"url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")", backgroundRepeat:'no-repeat', backgroundPosition:'right 12px center', paddingRight:36 };
  const focus = e => { e.target.style.borderColor='#6366f1'; e.target.style.boxShadow='0 0 0 3px rgba(99,102,241,.12)'; };
  const blur  = e => { e.target.style.borderColor='#d1d5db'; e.target.style.boxShadow='none'; };

  return (
    <>
      <style>{`@keyframes ia-spin{to{transform:rotate(360deg)}}@keyframes ia-in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}.ia-in{animation:ia-in .3s ease forwards}`}</style>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20, alignItems:'start' }}>

        {/* ═══ LEFT — Form ═══ */}
        <div style={{ display:'flex', flexDirection:'column', gap:14 }}>

          {/* Header card */}
          <div style={{ background:'linear-gradient(135deg,#6366f1,#8b5cf6)', borderRadius:14, padding:'16px 20px', display:'flex', alignItems:'center', gap:14 }}>
            <div style={{ width:44, height:44, borderRadius:11, background:'rgba(255,255,255,.2)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:20 }}>⚡</div>
            <div>
              <div style={{ fontSize:16, fontWeight:800, color:'#fff' }}>Analyze New Requirement</div>
              <div style={{ fontSize:12, color:'rgba(255,255,255,.75)', marginTop:2 }}>Run ML impact models against active sprint</div>
            </div>
          </div>

          {/* Sprint selector */}
          <div style={{ background:'#fff', border:'1px solid #e5e7eb', borderRadius:12, padding:18 }}>
            <label style={lbl}>Target Sprint</label>
            <select value={sprint?.id || ''} onChange={e => pickSprint(e.target.value)} style={sel} onFocus={focus} onBlur={blur}>
              <option value="">Select sprint…</option>
              {sprints?.map(s => <option key={s.id} value={s.id}>{s.name} ({s.status}){s.status === 'Active' ? ' 🔥' : ''}</option>)}
            </select>
            {ctx && (
              <>
                <div style={{ marginTop:14 }}><CapacityBar used={used} total={total} /></div>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginTop:12 }}>
                  <StatPill label="Items"    value={ctx.item_count} />
                  <StatPill label="Progress" value={`${ctx.sprint_progress}%`} />
                  <StatPill label="Days left" value={ctx.days_remaining} accent />
                  <StatPill label="Free SP"  value={Math.max(0, total - used)} />
                </div>
              </>
            )}
          </div>

          {/* Fields */}
          <div style={{ background:'#fff', border:'1px solid #e5e7eb', borderRadius:12, padding:18, display:'flex', flexDirection:'column', gap:14 }}>
            <div>
              <label style={lbl}>Title *</label>
              <input type="text" value={form.title} onChange={e => setForm({...form, title:e.target.value})} style={inp} placeholder="e.g., Add payment gateway integration" onFocus={focus} onBlur={blur} />
            </div>
            <div>
              <label style={lbl}>Description</label>
              <textarea value={form.description} onChange={e => setForm({...form, description:e.target.value})} style={{...inp, resize:'vertical'}} rows={3} placeholder="Technical details, affected systems, integrations…" onFocus={focus} onBlur={blur} />
              <p style={{ fontSize:11, color:'#9ca3af', marginTop:4 }}>💡 Richer detail improves story point accuracy</p>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
  <div>
  <label style={lbl}>Story Points {loadingPace ? '(loading pace...)' : ''}</label>
  <div style={{ display:'flex', gap:8, marginBottom:4 }}>
  <input type="number" min="1" max="21" value={form.story_points} onChange={e => setForm({...form, story_points:parseInt(e.target.value)||5})} style={{...inp, flex:1}} onFocus={focus} onBlur={blur} />
  <button onClick={suggestPoints} disabled={suggesting}
  style={{ padding:'8px 10px', background:'#eff6ff', border:'1px solid #bfdbfe', color:'#2563eb', borderRadius:8, cursor:'pointer', fontSize:11, fontWeight:700, whiteSpace:'nowrap', display:'flex', alignItems:'center', gap:4, opacity:suggesting?.6:1 }}
  >
  {suggesting ? <div style={{ width:12, height:12, border:'2px solid #bfdbfe', borderTopColor:'#2563eb', borderRadius:'50%', animation:'ia-spin .7s linear infinite' }} /> : '✨'} AI
  </button>
  </div>
  {/* MODULE 3: Hours Translation Display */}
  <div style={{ fontSize:11, color:'#9ca3af', fontStyle:'italic', padding:'4px 0' }}>
    {formatSPWithHours(form.story_points, hoursPerSP)}
  </div>
  </div>
              <div>
                <label style={lbl}>Priority</label>
                <select value={form.priority} onChange={e => setForm({...form, priority:e.target.value})} style={sel} onFocus={focus} onBlur={blur}>
                  <option>Low</option><option>Medium</option><option>High</option><option>Critical</option>
                </select>
              </div>
            </div>
            <div>
              <label style={lbl}>Type</label>
              <select value={form.type} onChange={e => setForm({...form, type:e.target.value})} style={sel} onFocus={focus} onBlur={blur}>
                <option>Task</option><option>Story</option><option>Bug</option><option>Subtask</option>
              </select>
            </div>
          </div>

          {/* ── Action buttons ── */}

          {/* NEW: Sentence-Transformer alignment check */}
          <button onClick={checkSTAlignment} disabled={stAligning || !sprint}
            style={{ padding:'10px 16px', background:'#fff', border:'1.5px solid #06b6d4', color:'#0891b2', borderRadius:10, cursor:'pointer', fontSize:12, fontWeight:700, display:'flex', alignItems:'center', justifyContent:'center', gap:8, opacity:(stAligning||!sprint)?0.5:1, transition:'all .2s', boxShadow: stAligning ? 'none' : '0 1px 4px rgba(6,182,212,.15)' }}
          >
            {stAligning
              ? <><div style={{ width:13, height:13, border:'2px solid #a5f3fc', borderTopColor:'#0891b2', borderRadius:'50%', animation:'ia-spin .7s linear infinite' }} /> Checking alignment…</>
              : <>🎯 Check Sprint Alignment</>}
          </button>

          {/* ST result card — shown inline, dismissible */}
          {stAlignment && (
            <STAlignmentCard
              result={stAlignment}
              onClear={() => setStAlignment(null)}
            />
          )}

          {/* Heavy ML impact analysis */}
  {/* MODULE 4: Quick Scope Creep Check Button */}
  <button onClick={checkSimpleAlignment} disabled={checkingAlignment || !sprint}
  style={{ padding:'10px 14px', background:'#fffbeb', border:'1px solid #fcd34d', color:'#d97706', borderRadius:8, cursor:'pointer', fontSize:12, fontWeight:700, display:'flex', alignItems:'center', justifyContent:'center', gap:6, opacity:(checkingAlignment||!sprint)?0.6:1, transition:'all .2s', letterSpacing:'0.02em', width:'100%', marginBottom:10 }}
  >
  {checkingAlignment ? <><div style={{ width:12, height:12, border:'2px solid #fcd34d', borderTopColor:'#d97706', borderRadius:'50%', animation:'ia-spin .7s linear infinite' }} /> Checking alignment…</> : <>⚠️ Check Scope Creep</>}
  </button>
  
  <button onClick={analyze} disabled={loading || !sprint}
  style={{ padding:'13px 16px', background:'linear-gradient(135deg,#6366f1,#8b5cf6)', border:'none', color:'#fff', borderRadius:10, cursor:'pointer', fontSize:14, fontWeight:800, display:'flex', alignItems:'center', justifyContent:'center', gap:8, opacity:(loading||!sprint)?0.6:1, transition:'all .2s', boxShadow:(!loading&&sprint)?'0 4px 16px rgba(99,102,241,.35)':'none', letterSpacing:'0.03em' }}
  >
  {loading ? <><div style={{ width:16, height:16, border:'2px solid rgba(255,255,255,.35)', borderTopColor:'#fff', borderRadius:'50%', animation:'ia-spin .9s linear infinite' }} /> Running ML Analysis…</> : <>⚡ Analyze Impact</>}
  </button>
        </div>

  {/* ═══ RIGHT — Results ═══ */}
  <div ref={ref} style={{ display:'flex', flexDirection:'column', gap:14 }}>
  
  {/* MODULE 4: Scope Creep Warning */}
  {simpleAlignment && (
    <ScopeCreepWarning 
      alignmentScore={simpleAlignment.alignment_score}
      taskTitle={form.title}
      onDismiss={() => setSimpleAlignment(null)}
    />
  )}
  
  {/* MODULE 3: CapacityBar now shows hours */}
  {ctx && sprint && (
    <div style={{ background:'#fff', border:'1px solid #e5e7eb', borderRadius:12, padding:'16px', }}>
      <CapacityBar used={ctx.used_points} total={ctx.total_capacity} hoursPerSP={hoursPerSP} />
    </div>
  )}
  
  {/* Empty state */}
  {!analysis && !loading && (
            <div style={{ background:'#fff', border:'2px dashed #e5e7eb', borderRadius:14, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', minHeight:340, gap:12, padding:32, textAlign:'center' }}>
              <div style={{ width:64, height:64, borderRadius:16, background:'linear-gradient(135deg,#f5f3ff,#eff6ff)', border:'1px solid #e0e7ff', display:'flex', alignItems:'center', justifyContent:'center', fontSize:28 }}>⚡</div>
              <div style={{ fontSize:16, fontWeight:700, color:'#374151' }}>No Analysis Yet</div>
              <div style={{ fontSize:13, color:'#9ca3af', maxWidth:240, lineHeight:1.65 }}>Fill in the form on the left and click "Analyze Impact" to run ML models against the sprint</div>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div style={{ background:'#fff', border:'1px solid #e5e7eb', borderRadius:14, padding:36, display:'flex', flexDirection:'column', alignItems:'center', gap:18 }}>
              <div style={{ position:'relative', width:52, height:52 }}>
                <div style={{ position:'absolute', inset:0, borderRadius:'50%', border:'3px solid #e5e7eb', borderTopColor:'#6366f1', animation:'ia-spin .9s linear infinite' }} />
                <div style={{ position:'absolute', inset:8, borderRadius:'50%', border:'3px solid #e5e7eb', borderTopColor:'#8b5cf6', animation:'ia-spin 1.4s linear infinite reverse' }} />
              </div>
              <div style={{ fontSize:14, fontWeight:700, color:'#374151' }}>Running ML Models…</div>
              <div style={{ display:'flex', flexDirection:'column', gap:7 }}>
                {['Effort estimation','Schedule risk','Productivity impact','Quality risk'].map((m, i) => (
                  <div key={m} style={{ display:'flex', alignItems:'center', gap:10, fontSize:12, color:'#6b7280' }}>
                    <div style={{ width:7, height:7, borderRadius:'50%', background:'#6366f1', opacity:.4 + i * .15 }} />{m}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Results */}
          {analysis?.display && (
            <>
              <div className="ia-in"><RiskBanner status={overallStatus} /></div>

              <div style={{ display:'flex', alignItems:'center', gap:10 }} className="ia-in">
                <span style={{ fontSize:10, fontWeight:700, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.12em', whiteSpace:'nowrap' }}>Risk Signals</span>
                <div style={{ flex:1, height:1, background:'#e5e7eb' }} />
              </div>

              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }} className="ia-in">
                {METRICS.map(({ key, label, idx }) => {
                  const m = analysis.display[key];
                  if (!m) return null;
                  return <RiskCard key={key} label={label} value={m.value} status={m.status} sub_text={m.sub_text} index={idx} />;
                })}
              </div>

              <div style={{ background:'#fff', border:'1px solid #e5e7eb', borderRadius:12, padding:'16px 18px' }} className="ia-in">
                <div style={{ fontSize:10, fontWeight:700, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.12em', marginBottom:14 }}>Risk Overview</div>
                <GaugeBar label="Schedule spillover" pct={analysis.ml_raw?.schedule_risk?.probability ?? 0} status={analysis.display.schedule?.status} />
                <GaugeBar label="Defect probability"  pct={analysis.ml_raw?.quality_risk?.probability  ?? 0} status={analysis.display.quality?.status}   />
                <GaugeBar label="Productivity drag"   pct={Math.abs(analysis.ml_raw?.productivity?.velocity_change ?? 0)} status={analysis.display.productivity?.status} />
              </div>

              <div style={{ display:'flex', alignItems:'center', gap:10 }} className="ia-in">
                <div style={{ flex:1, height:1, background:'#e5e7eb' }} />
                <span style={{ fontSize:10, fontWeight:700, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.12em', whiteSpace:'nowrap' }}>Recommendation</span>
                <div style={{ flex:1, height:1, background:'#e5e7eb' }} />
              </div>

              {/* Phase 3 Decision Engine card (preferred) */}
              {decision && (
                <div className="ia-in">
                  <DecisionEngineCard
                    decision={decision}
                    formData={form}
                    sprintId={sprint?.id}
                    spaceId={resolvedSpaceId}
                    logId={analysis.log_id}
                    onActionDone={(r) => { setResult(r); if (sprint) loadCtx(sprint.id); }}
                  />
                </div>
              )}

              {/* Fallback: existing RecommendationCard if decision engine not available */}
              {!decision && analysis.recommendation && (
                <div className="ia-in">
                  <RecommendationCard
                    recommendation={analysis.recommendation}
                    explanation={analysis.explanation}
                    formData={form}
                    sprintId={sprint?.id}
                    spaceId={resolvedSpaceId}
                    logId={analysis.log_id}
                    onActionDone={(r) => { setResult(r); if (sprint) loadCtx(sprint.id); }}
                  />
                </div>
              )}

              {result?.requiresManual && (
                <div style={{ background:'#f5f3ff', border:'1px solid #ddd6fe', borderRadius:10, padding:'12px 16px', display:'flex', alignItems:'flex-start', gap:10 }} className="ia-in">
                  <span style={{ fontSize:16 }}>✂️</span>
                  <div>
                    <div style={{ fontSize:13, fontWeight:700, color:'#5b21b6', marginBottom:3 }}>Manual Split Required</div>
                    <div style={{ fontSize:12, color:'#6b7280' }}>{result.message}</div>
                  </div>
                </div>
              )}

              {result && (
                <button onClick={() => { setAnalysis(null); setResult(null); setDecision(null); setForm({ title:'', description:'', story_points:5, priority:'Medium', type:'Task' }); }}
                  style={{ width:'100%', padding:'10px 16px', background:'#f9fafb', border:'1px solid #e5e7eb', color:'#6b7280', borderRadius:10, cursor:'pointer', fontSize:12, fontWeight:700, transition:'all .2s' }}
                  onMouseEnter={e => { e.currentTarget.style.background='#f3f4f6'; e.currentTarget.style.color='#374151'; }}
                  onMouseLeave={e => { e.currentTarget.style.background='#f9fafb'; e.currentTarget.style.color='#6b7280'; }}
                  className="ia-in"
                >
                  ↺ Analyze Another Ticket
                </button>
              )}

              <div style={{ fontSize:10, color:'#d1d5db', textAlign:'right' }} className="ia-in">
                Predictions generated by ML models · Indicative only
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
