/**
 * ImpactAnalyzer.jsx — updated
 *
 * What changed:
 *
 * 1. SINGLE "AI STRATEGY RECOMMENDATION" PANEL
 *    Old: two panels shown — one from RecommendationCard (classical engine)
 *    and one from DecisionEngineCard (new engine), with confusing dual labels.
 *    New: one panel labelled "AI Strategy Recommendation" that always uses
 *    the unified decision engine result from analysis.decision.
 *
 *
 * 3. VOLATILE PRODUCTIVITY DISPLAY
 *    When display.productivity.value === "VOLATILE", a red "VOLATILE" badge
 *    replaces the percentage, with explanation text.
 *
 * 4. MODULE 3 SP→Hours and MODULE 4 alignment unchanged.
 */

import { useState, useEffect, useRef } from 'react';
import api from './api';
import { formatSPWithHours, fetchTeamPace } from '../../../utils/hourTranslation';

// ─── Constants ─────────────────────────────────────────────────────────────

const ACTION_META = {
  ADD:    { icon: '✅', label: 'Add to Sprint',    color: '#059669', bg: '#ecfdf5', border: '#6ee7b7', text: '#065f46' },
  SWAP:   { icon: '🔄', label: 'Execute Swap',     color: '#2563eb', bg: '#eff6ff', border: '#93c5fd', text: '#1e3a8a' },
  DEFER:  { icon: '⏸',  label: 'Defer to Backlog', color: '#d97706', bg: '#fffbeb', border: '#fcd34d', text: '#78350f' },
  SPLIT:  { icon: '✂️', label: 'Split Ticket',     color: '#7c3aed', bg: '#f5f3ff', border: '#c4b5fd', text: '#3b0764' },
  ABSORB: { icon: '🛡',  label: 'Buffer Absorbs',  color: '#059669', bg: '#ecfdf5', border: '#6ee7b7', text: '#065f46' },
  SWARM:  { icon: '🐝',  label: 'Team Swarm',      color: '#7c3aed', bg: '#f5f3ff', border: '#c4b5fd', text: '#3b0764' },
};

const STATUS = {
  safe:     { color: '#059669', bg: '#ecfdf5', border: '#a7f3d0', chip: '#d1fae5', chipText: '#065f46', label: 'NOMINAL',  bar: '#10b981' },
  warning:  { color: '#d97706', bg: '#fffbeb', border: '#fde68a', chip: '#fef3c7', chipText: '#92400e', label: 'CAUTION',  bar: '#f59e0b' },
  critical: { color: '#dc2626', bg: '#fef2f2', border: '#fecaca', chip: '#fee2e2', chipText: '#991b1b', label: 'ALERT',    bar: '#ef4444' },
};

// ─── Shared sub-components (unchanged from original) ───────────────────────

function CapacityBar({ used, total, hoursPerSP = 8.0 }) {
  const pct  = total > 0 ? Math.min(100, (used / total) * 100) : 0;
  const bufferThreshold = 80; // 80% utilization = entering stability buffer
  
  // Determine which segment the used capacity falls into
  const usedInSafeZone = Math.min(used, (total * bufferThreshold) / 100);
  const usedInBuffer = Math.max(0, used - usedInSafeZone);
  
  const safeZonePct = (usedInSafeZone / total) * 100;
  const bufferPct = (usedInBuffer / total) * 100;
  
  const free = Math.max(0, total - used);
  const usedHours  = Math.round(used  * hoursPerSP * 10) / 10;
  const totalHours = Math.round(total * hoursPerSP * 10) / 10;
  const freeHours  = Math.round(free  * hoursPerSP * 10) / 10;
  
  const isInBuffer = pct > bufferThreshold;
  const isOverCapacity = pct > 100;
  
  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', marginBottom:6 }}>
        <span style={{ fontSize:12, color:'#374151', fontWeight:600 }}>Sprint Capacity</span>
        <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:2 }}>
          <span style={{ fontSize:12, fontWeight:800, color:'#111827' }}>{used} / {total} SP</span>
          <span style={{ fontSize:10, color:'#9ca3af', fontStyle:'italic' }}>({usedHours} / {totalHours} hrs)</span>
        </div>
      </div>
      {/* NEW: Stacked progress bar showing safe zone (0-80%) and buffer zone (80-100%) */}
      <div style={{ display:'flex', alignItems:'center', gap:3, marginBottom:8 }}>
        <div style={{ height:10, flex:1, background:'#e5e7eb', borderRadius:6, overflow:'hidden', display:'flex' }}>
          {/* Green safe zone (0-80%) */}
          <div style={{
            height:'100%',
            width: `${Math.min(safeZonePct, 100)}%`,
            background:'#10b981',
            transition:'width 0.3s ease'
          }} />
          {/* Yellow buffer zone (80-100%) */}
          {bufferPct > 0 && (
            <div style={{
              height:'100%',
              width: `${Math.min(bufferPct, 20)}%`,
              background:'#f59e0b',
              transition:'width 0.3s ease'
            }} />
          )}
          {/* Red overflow (>100%) */}
          {isOverCapacity && (
            <div style={{
              height:'100%',
              width:`${Math.min(pct - 100, 100)}%`,
              background:'#dc2626',
              transition:'width 0.3s ease'
            }} />
          )}
        </div>
        {isInBuffer && (
          <div style={{
            padding:'3px 8px',
            background:'#fef3c7',
            border:'1px solid #fcd34d',
            borderRadius:4,
            fontSize:10,
            fontWeight:700,
            color:'#92400e',
            whiteSpace:'nowrap'
          }}>
            Entering Buffer
          </div>
        )}
      </div>
      <div style={{ display:'flex', justifyContent:'space-between', marginTop:5 }}>
        <span style={{ fontSize:11, color:'#9ca3af' }}>{Math.round(pct)}% used</span>
        <span style={{ fontSize:11, color:free < 5 ? '#dc2626' : '#059669', fontWeight:600 }}>{free} SP ({freeHours} hrs) remaining</span>
      </div>
    </div>
  );
}

function StatPill({ label, value, accent }) {
  return (
    <div style={{ textAlign:'center', padding:'10px 6px', background: accent ? '#eff6ff' : '#f9fafb', borderRadius:8, border: accent ? '1px solid #bfdbfe' : '1px solid #e5e7eb' }}>
      <div style={{ fontSize:17, fontWeight:800, color: accent ? '#1d4ed8' : '#111827' }}>{value}</div>
      <div style={{ fontSize:10, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.07em', fontWeight:600, marginTop:2 }}>{label}</div>
    </div>
  );
}

function RiskCard({ label, value, status, sub_text, index, saturation_status }) {
  const [open, setOpen] = useState(false);
  const s = STATUS[status] || STATUS.warning;
  const RISK_ICONS = {
    0: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,
    1: <><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></>,
    2: <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>,
    3: <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>,
  };

  // NEW: VOLATILE display for saturated productivity model
  const isVolatile = saturation_status === 'CRITICAL_VOLATILITY' || value === 'VOLATILE';

  return (
    <div onClick={() => setOpen(o => !o)} style={{ background:'#fff', border:`1px solid ${open ? s.color : '#e5e7eb'}`, borderLeft:`4px solid ${isVolatile ? '#dc2626' : s.color}`, borderRadius:10, padding:'14px 16px', cursor:'pointer', transition:'all .2s', boxShadow: open ? `0 4px 14px ${s.color}22` : '0 1px 3px rgba(0,0,0,.05)' }}>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:8 }}>
        <div style={{ display:'flex', alignItems:'center', gap:10, minWidth:0, flex:1 }}>
          <div style={{ width:32, height:32, borderRadius:8, background:s.bg, border:`1px solid ${s.border}`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={s.color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              {RISK_ICONS[index] || RISK_ICONS[0]}
            </svg>
          </div>
          <div style={{ minWidth:0 }}>
            <div style={{ fontSize:10, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:700, marginBottom:2 }}>{label}</div>
            {isVolatile ? (
              <div style={{ fontSize:13, fontWeight:800, color:'#dc2626', display:'flex', alignItems:'center', gap:6 }}>
                <span style={{ background:'#fee2e2', color:'#991b1b', border:'1px solid #fecaca', borderRadius:4, padding:'2px 8px', fontSize:11, fontWeight:800, letterSpacing:'0.08em' }}>VOLATILE</span>
                <span style={{ fontSize:11, color:'#6b7280', fontWeight:400 }}>Model limit exceeded</span>
              </div>
            ) : (
              <div style={{ fontSize:13, fontWeight:800, color:'#111827', lineHeight:1.2 }}>{value}</div>
            )}
          </div>
        </div>
        <span style={{ fontSize:9, fontWeight:800, padding:'3px 7px', borderRadius:4, background:s.chip, color:s.chipText, border:`1px solid ${s.border}`, whiteSpace:'nowrap', letterSpacing:'0.07em', flexShrink:0 }}>
          {s.label}
        </span>
      </div>
      {open && (
        <div style={{ marginTop:10, paddingTop:10, borderTop:`1px dashed ${s.border}`, fontSize:12, color:'#4b5563', lineHeight:1.65 }}>
          {isVolatile
            ? "Workload exceeds model prediction limits. The situation is severe enough that a percentage is no longer meaningful. Immediate sprint replanning is recommended."
            : sub_text}
        </div>
      )}
      <div style={{ marginTop:6, fontSize:10, color:s.color, fontWeight:700 }}>{open ? '▲ collapse' : '▼ details'}</div>
    </div>
  );
}

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

function RiskBanner({ status }) {
  const C = {
    safe:     { bg:'#ecfdf5', border:'#a7f3d0', dot:'#10b981', title:'All Signals Nominal',    sub:'Safe to add to sprint' },
    warning:  { bg:'#fffbeb', border:'#fde68a', dot:'#f59e0b', title:'Elevated Risk Detected', sub:'Review caution items before proceeding' },
    critical: { bg:'#fef2f2', border:'#fecaca', dot:'#ef4444', title:'Critical Risk Detected', sub:'Follow recommendation before adding to sprint' },
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

// ══════════════════════════════════════════════════════════════════════════════
// NEW: Single "AI Strategy Recommendation" card
// Replaces both RecommendationCard and DecisionEngineCard
// ══════════════════════════════════════════════════════════════════════════════

async function executeDecisionAction(action, sprintId, spaceId, formData) {
  const base = {
    title: formData.title, description: formData.description,
    story_points: formData.story_points, priority: formData.priority,
    type: formData.type, space_id: spaceId, status: 'To Do',
  };
  if (action === 'ADD') {
    const r = await api.createBacklogItem({ ...base, sprint_id: sprintId });
    return { ok: true, message: `"${formData.title}" added to sprint.`, data: r };
  }
  if (action === 'DEFER') {
    const r = await api.createBacklogItem({ ...base, sprint_id: null });
    return { ok: true, message: `"${formData.title}" saved to backlog.`, data: r };
  }
  if (action === 'SPLIT') {
    const r = await api.createBacklogItem({ ...base, sprint_id: null });
    return { ok: true, requiresManual: true, message: 'Saved to backlog. Split manually before sprint planning.', data: r };
  }
  if (action === 'SWAP') {
    const r = await api.createBacklogItem({ ...base, sprint_id: null });
    return { ok: true, requiresManual: true, message: 'Swapped — new item needs manual placement.', data: r };
  }
  throw new Error('Unknown action: ' + action);
}

function AIStrategyRecommendation({ decision, explanation, formData, sprintId, spaceId, logId, onActionDone }) {
  const [doing,   setDoing]   = useState(false);
  const [done,    setDone]    = useState(false);
  const [doneMsg, setDoneMsg] = useState('');
  const [override, setOverride] = useState(null);

  if (!decision?.action) return null;

  const activeAction = override ?? decision.action;
  const meta = ACTION_META[activeAction] ?? ACTION_META.DEFER;
  const allActions = ['ADD', 'DEFER', 'SPLIT', 'SWAP'];

  const doAction = async (a) => {
    setDoing(true);
    try {
      const r = await executeDecisionAction(a, sprintId, spaceId, formData);
      if (logId) {
        try {
          await api.recordImpactFeedback(logId, {
            accepted:     true,
            taken_action: a === decision.action ? 'FOLLOWED_RECOMMENDATION' : 'OVERRIDDEN',
          });
        } catch (_) {}
      }
      setDone(true); setDoneMsg(r.message); onActionDone?.(r);
    } catch (e) { alert('Action failed: ' + e.message); }
    finally { setDoing(false); }
  };

  return (
    <div style={{ background:meta.bg, border:`1.5px solid ${meta.border}`, borderRadius:14, padding:20 }}>
      {/* Header */}
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:12, marginBottom:14 }}>
        <div style={{ display:'flex', alignItems:'center', gap:12 }}>
          <div style={{ width:46, height:46, borderRadius:12, background:'#fff', border:`1px solid ${meta.border}`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:22, flexShrink:0 }}>
            {meta.icon}
          </div>
          <div>
            {/* CHANGE: single label "AI Strategy Recommendation" — no more dual engine confusion */}
            <div style={{ fontSize:10, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.1em', fontWeight:700, marginBottom:2 }}>AI Strategy Recommendation</div>
            <div style={{ fontSize:16, fontWeight:800, color:meta.color }}>{explanation?.short_title ?? decision.action}</div>
          </div>
        </div>
        <span style={{ fontSize:10, fontWeight:800, padding:'4px 10px', borderRadius:6, background:'#fff', color:meta.color, border:`1px solid ${meta.border}`, letterSpacing:'0.1em', whiteSpace:'nowrap' }}>
          {activeAction}
        </span>
      </div>

      {/* Rule that triggered */}
      <div style={{ fontSize:10, color:'#6b7280', background:'#f3f4f6', border:'1px solid #e5e7eb', borderRadius:6, padding:'4px 10px', display:'inline-block', marginBottom:12 }}>
        ⚙️ {decision.rule_triggered}
      </div>

      {/* Reasoning */}
      <p style={{ fontSize:13, color:'#374151', lineHeight:1.7, marginBottom:14 }}>{decision.reasoning}</p>

      {/* Detailed explanation */}
      {explanation?.detailed_explanation && (
        <div style={{ background:'#fff', border:`1px solid ${meta.border}`, borderRadius:8, padding:'10px 14px', marginBottom:14, fontSize:12, color:'#4b5563', lineHeight:1.65 }}>
          {explanation.detailed_explanation}
        </div>
      )}

      {/* CTA */}
      {done ? (
        <div style={{ background:'#ecfdf5', border:'1px solid #a7f3d0', borderRadius:8, padding:'10px 14px', fontSize:13, fontWeight:600, color:'#065f46', display:'flex', alignItems:'center', gap:8 }}>
          ✅ {doneMsg}
        </div>
      ) : (
        <>
          <button onClick={() => doAction(activeAction)} disabled={doing}
            style={{ width:'100%', padding:'12px 16px', background:meta.color, border:'none', color:'#fff', borderRadius:9, cursor:'pointer', fontSize:13, fontWeight:800, display:'flex', alignItems:'center', justifyContent:'center', gap:8, marginBottom:14, opacity:doing?0.7:1, transition:'all .2s', boxShadow:`0 3px 10px ${meta.color}44` }}
          >
            {doing
              ? <><div style={{ width:14, height:14, border:'2px solid rgba(255,255,255,.35)', borderTopColor:'#fff', borderRadius:'50%', animation:'ia-spin .7s linear infinite' }} /> Applying…</>
              : <>{meta.icon} {meta.label}</>}
          </button>

          <div>
            <div style={{ fontSize:10, color:'#9ca3af', fontWeight:700, marginBottom:8, textTransform:'uppercase', letterSpacing:'0.08em' }}>📋 Product Owner Override</div>
            <div style={{ display:'flex', gap:6, flexWrap:'wrap' }}>
              {allActions.map(a => {
                const m = ACTION_META[a];
                const isSelected = a === activeAction;
                return (
                  <button key={a} onClick={() => setOverride(a === decision.action ? null : a)} disabled={doing}
                    style={{ fontSize:11, fontWeight:700, padding:'6px 14px', background: isSelected ? m.color : m.bg, border:`1.5px solid ${isSelected ? m.color : m.border}`, color: isSelected ? '#fff' : m.color, borderRadius:7, cursor:'pointer', opacity:doing?0.5:1 }}
                  >
                    {m.icon} {a}
                  </button>
                );
              })}
            </div>
            {override && override !== decision.action && (
              <div style={{ marginTop:8, fontSize:11, color:'#d97706', fontStyle:'italic' }}>
                ⚠️ Overriding AI recommendation ({decision.action} → {override})
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// Main ImpactAnalyzer
// ══════════════════════════════════════════════════════════════════════════════

export default function ImpactAnalyzer({ sprints, spaceId, spaceMaxAssignees = 10, onActionDone: parentOnActionDone }) {
  const [sprint,    setSprint]    = useState(null);
  const [form,      setForm]      = useState({ title:'', description:'', story_points:5, priority:'Medium', type:'Task' });
  const [analysis,  setAnalysis]  = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [ctx,       setCtx]       = useState(null);
  const [suggesting, setSuggesting] = useState(false);
  const [stAlignment, setStAlignment] = useState(null);
  const [stAligning,  setStAligning]  = useState(false);

  const [hoursPerSP, setHoursPerSP] = useState(8.0);
  const ref = useRef(null);

  useEffect(() => {
    const active = sprints?.find(s => s.status === 'Active') || sprints?.[0];
    if (active && !sprint) { setSprint(active); loadCtx(active.id); }
  }, [sprints]);

  useEffect(() => {
    if (!spaceId) return;
    fetchTeamPace(spaceId)
      .then(data => setHoursPerSP(data.hours_per_sp || 8.0))
      .catch(() => setHoursPerSP(8.0));
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
    try {
      const r = await api.predictStoryPoints({ title: form.title, description: form.description });
      setForm({ ...form, story_points: r.suggested_points || 5 });
    } catch (e) { alert('Could not suggest: ' + e.message); }
    finally { setSuggesting(false); }
  };

  const checkSTAlignment = async () => {
    if (!sprint || !form.title.trim()) { alert('Select a sprint and enter a title.'); return; }
    setStAligning(true); setStAlignment(null);
    try {
      const r = await api.checkSprintAlignment({
        sprint_goal:        sprint.goal || '',
        ticket_title:       form.title,
        ticket_description: form.description,
        priority:           form.priority,
      });
      setStAlignment(r);
    } catch (e) { alert('Alignment check failed: ' + e.message); }
    finally { setStAligning(false); }
  };

  const analyze = async () => {
    if (!sprint || !form.title.trim()) { alert('Select a sprint and enter a title.'); return; }
    setLoading(true); setAnalysis(null);
    try {
      const r = await api.analyzeImpact({
        sprint_id:    sprint.id,
        title:        form.title,
        description:  form.description,
        story_points: form.story_points,
        priority:     form.priority,
        type:         form.type,
      });
      setAnalysis(r);
      setTimeout(() => ref.current?.scrollIntoView({ behavior:'smooth', block:'start' }), 100);
    } catch (e) { alert('Analysis failed: ' + e.message); }
    finally { setLoading(false); }
  };

  const used  = ctx?.current_load  || 0;
  const total = ctx?.team_velocity || Math.max(used, 30);

  const METRICS = [
    { key:'effort',       label:'Effort Estimate',    idx:3 },
    { key:'schedule',     label:'Schedule Risk',       idx:1 },
    { key:'productivity', label:'Productivity Impact', idx:2 },
    { key:'quality',      label:'Quality Risk',        idx:0 },
  ];

  const overallStatus = analysis?.display
    ? (() => { const v = METRICS.map(m => analysis.display[m.key]?.status || 'safe'); return v.includes('critical') ? 'critical' : v.includes('warning') ? 'warning' : 'safe'; })()
    : null;

  const inp = { width:'100%', padding:'9px 12px', border:'1px solid #d1d5db', borderRadius:8, fontSize:13, color:'#111827', background:'#fff', outline:'none', boxSizing:'border-box' };
  const lbl = { display:'block', fontSize:11, fontWeight:700, color:'#6b7280', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:6 };
  const sel = { ...inp, appearance:'none', cursor:'pointer', backgroundImage:"url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")", backgroundRepeat:'no-repeat', backgroundPosition:'right 12px center', paddingRight:36 };
  const focus = e => { e.target.style.borderColor='#6366f1'; e.target.style.boxShadow='0 0 0 3px rgba(99,102,241,.12)'; };
  const blur  = e => { e.target.style.borderColor='#d1d5db'; e.target.style.boxShadow='none'; };

  return (
    <>
      <style>{`@keyframes ia-spin{to{transform:rotate(360deg)}}.ia-in{animation:ia-in .3s ease forwards}@keyframes ia-in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}`}</style>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20, alignItems:'start' }}>

        {/* ═══ LEFT — Form ═══ */}
        <div style={{ display:'flex', flexDirection:'column', gap:14 }}>

          {/* Header */}
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
              {sprints?.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.status}){s.status === 'Active' ? ' 🔥' : ''} — {s.assignee_count ?? 2} devs
                </option>
              ))}
            </select>
            {ctx && (
              <>
                <div style={{ marginTop:14 }}><CapacityBar used={used} total={total} hoursPerSP={hoursPerSP} /></div>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginTop:12 }}>
                  <StatPill label="Items"     value={ctx.item_count} />
                  <StatPill label="Progress"  value={`${ctx.sprint_progress}%`} />
                  <StatPill label="Days left" value={ctx.days_remaining} accent />
                  <StatPill label="Devs"      value={ctx.assignee_count ?? '—'} />
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
              <textarea value={form.description} onChange={e => setForm({...form, description:e.target.value})} style={{...inp, resize:'vertical'}} rows={3} placeholder="Technical details, affected systems…" onFocus={focus} onBlur={blur} />
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
              <div>
                <label style={lbl}>Story Points</label>
                <div style={{ display:'flex', gap:8, marginBottom:4 }}>
                  <input type="number" min="1" max="21" value={form.story_points} onChange={e => setForm({...form, story_points:parseInt(e.target.value)||5})} style={{...inp, flex:1}} onFocus={focus} onBlur={blur} />
                  <button onClick={suggestPoints} disabled={suggesting}
                    style={{ padding:'8px 10px', background:'#eff6ff', border:'1px solid #bfdbfe', color:'#2563eb', borderRadius:8, cursor:'pointer', fontSize:11, fontWeight:700, whiteSpace:'nowrap' }}
                  >
                    {suggesting ? '…' : '✨ AI'}
                  </button>
                </div>
                <div style={{ fontSize:11, color:'#9ca3af', fontStyle:'italic' }}>
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

          {/* Sprint alignment check */}
          <button onClick={checkSTAlignment} disabled={stAligning || !sprint}
            style={{ padding:'10px 16px', background:'#fff', border:'1.5px solid #06b6d4', color:'#0891b2', borderRadius:10, cursor:'pointer', fontSize:12, fontWeight:700, display:'flex', alignItems:'center', justifyContent:'center', gap:8, opacity:(stAligning||!sprint)?0.5:1 }}
          >
            {stAligning ? '⏳ Checking alignment…' : '🎯 Check Sprint Alignment'}
          </button>

          {stAlignment && (
            <div style={{ background: stAlignment.alignment_state === 'STRONGLY_ALIGNED' ? '#ecfdf5' : stAlignment.alignment_state === 'UNALIGNED' ? '#fef2f2' : '#fffbeb', border:'1px solid #e5e7eb', borderRadius:10, padding:'12px 16px' }}>
              <div style={{ fontSize:14, fontWeight:800, color:'#111827', marginBottom:4 }}>{stAlignment.alignment_label}</div>
              <div style={{ fontSize:12, color:'#4b5563' }}>{stAlignment.semantic_reasoning}</div>
              <div style={{ fontSize:11, color:'#9ca3af', marginTop:4 }}>Score: {stAlignment.semantic_score_pct}% · {stAlignment.model_name}</div>
            </div>
          )}

          {/* Main analysis button */}
          <button onClick={analyze} disabled={loading || !sprint}
            style={{ padding:'13px 16px', background:'linear-gradient(135deg,#6366f1,#8b5cf6)', border:'none', color:'#fff', borderRadius:10, cursor:'pointer', fontSize:14, fontWeight:800, display:'flex', alignItems:'center', justifyContent:'center', gap:8, opacity:(loading||!sprint)?0.6:1, boxShadow:(!loading&&sprint)?'0 4px 16px rgba(99,102,241,.35)':'none' }}
          >
            {loading ? <><div style={{ width:16, height:16, border:'2px solid rgba(255,255,255,.35)', borderTopColor:'#fff', borderRadius:'50%', animation:'ia-spin .9s linear infinite' }} /> Running ML Analysis…</> : '⚡ Analyze Impact'}
          </button>

        </div>

        {/* ═══ RIGHT — Results ═══ */}
        <div ref={ref} style={{ display:'flex', flexDirection:'column', gap:14 }}>

          {!analysis && !loading && (
            <div style={{ background:'#fff', border:'2px dashed #e5e7eb', borderRadius:14, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', minHeight:340, gap:12, padding:32, textAlign:'center' }}>
              <div style={{ fontSize:28 }}>⚡</div>
              <div style={{ fontSize:16, fontWeight:700, color:'#374151' }}>No Analysis Yet</div>
              <div style={{ fontSize:13, color:'#9ca3af', maxWidth:240, lineHeight:1.65 }}>Fill in the form and click Analyze Impact to run ML models against the sprint.</div>
            </div>
          )}

          {loading && (
            <div style={{ background:'#fff', border:'1px solid #e5e7eb', borderRadius:14, padding:36, display:'flex', flexDirection:'column', alignItems:'center', gap:18 }}>
              <div style={{ position:'relative', width:52, height:52 }}>
                <div style={{ position:'absolute', inset:0, borderRadius:'50%', border:'3px solid #e5e7eb', borderTopColor:'#6366f1', animation:'ia-spin .9s linear infinite' }} />
                <div style={{ position:'absolute', inset:8, borderRadius:'50%', border:'3px solid #e5e7eb', borderTopColor:'#8b5cf6', animation:'ia-spin 1.4s linear infinite reverse' }} />
              </div>
              <div style={{ fontSize:14, fontWeight:700, color:'#374151' }}>Running ML Models…</div>
            </div>
          )}

          {analysis?.display && (
            <>
              <div className="ia-in"><RiskBanner status={overallStatus} /></div>

              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }} className="ia-in">
                {METRICS.map(({ key, label, idx }) => {
                  const m = analysis.display[key];
                  if (!m) return null;
                  return <RiskCard key={key} label={label} value={m.value} status={m.status} sub_text={m.sub_text} index={idx} saturation_status={m.saturation_status} />;
                })}
              </div>

              <div style={{ background:'#fff', border:'1px solid #e5e7eb', borderRadius:12, padding:'16px 18px' }} className="ia-in">
                <div style={{ fontSize:10, fontWeight:700, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.12em', marginBottom:14 }}>Risk Overview</div>
                <GaugeBar label="Schedule spillover" pct={analysis.ml_raw?.schedule_risk?.probability ?? 0} status={analysis.display.schedule?.status} />
                <GaugeBar label="Defect probability"  pct={analysis.ml_raw?.quality_risk?.probability  ?? 0} status={analysis.display.quality?.status}   />
                <GaugeBar label="Productivity drag"   pct={Math.abs(analysis.ml_raw?.productivity?.velocity_change ?? 0)} status={analysis.display.productivity?.status} />
              </div>

              {/* CHANGE: Single AI Strategy Recommendation panel */}
              <div className="ia-in">
                <AIStrategyRecommendation
                  decision={analysis.decision}
                  explanation={analysis.explanation}
                  formData={form}
                  sprintId={sprint?.id}
                  spaceId={spaceId}
                  logId={analysis.log_id}
                  onActionDone={(r) => { if (sprint) loadCtx(sprint.id); parentOnActionDone?.(r); }}
                />
              </div>

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
