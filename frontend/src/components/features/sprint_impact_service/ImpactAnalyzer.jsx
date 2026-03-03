/**
 * ImpactAnalyzer.jsx  — EXISTING FILE (replace fully)
 * ─────────────────────────────────────────────────────────────────────────────
 * Changes in this version:
 *   - Removed recordAnalysisHistory() call — history now comes from MongoDB
 *     via GET /api/impact/history/{spaceId} (no sessionStorage needed)
 *   - spaceId resolved from: prop → selectedSprint.space_id → ''
 *   - space_id correctly passed to createBacklogItem on every action
 *
 * Props:
 *   sprints : Sprint[]   — list of sprints for selector
 *   spaceId : string     — current space id (required for backlog item creation)
 */

import { useState, useEffect } from 'react';
import api from './api';

// ─── Action metadata ──────────────────────────────────────────────────────────
const ACTION_META = {
  ADD:    { icon: '✅', label: 'Add to Sprint',    bg: 'bg-green-600',  hover: 'hover:bg-green-700',  border: 'border-green-200',  cardBg: 'bg-green-50',  text: 'text-green-900',  badge: 'bg-green-100 text-green-800'   },
  SWAP:   { icon: '🔄', label: 'Execute Swap',     bg: 'bg-blue-600',   hover: 'hover:bg-blue-700',   border: 'border-blue-200',   cardBg: 'bg-blue-50',   text: 'text-blue-900',   badge: 'bg-blue-100 text-blue-800'    },
  DEFER:  { icon: '⏸',  label: 'Defer to Backlog', bg: 'bg-amber-500',  hover: 'hover:bg-amber-600',  border: 'border-amber-200',  cardBg: 'bg-amber-50',  text: 'text-amber-900',  badge: 'bg-amber-100 text-amber-800'  },
  SPLIT:  { icon: '✂️', label: 'Split Ticket',     bg: 'bg-purple-600', hover: 'hover:bg-purple-700', border: 'border-purple-200', cardBg: 'bg-purple-50', text: 'text-purple-900', badge: 'bg-purple-100 text-purple-800' },
  ACCEPT: { icon: '✅', label: 'Accept',           bg: 'bg-green-600',  hover: 'hover:bg-green-700',  border: 'border-green-200',  cardBg: 'bg-green-50',  text: 'text-green-900',  badge: 'bg-green-100 text-green-800'   },
};

// ─── Execute action against backlog API ───────────────────────────────────────
async function executeAction(action, recommendation, sprintId, spaceId, formData) {
  const base = {
    title:        formData.title,
    description:  formData.description,
    story_points: formData.story_points,
    priority:     formData.priority,
    type:         formData.type,
    space_id:     spaceId,   // always required
    status:       'To Do',
  };

  switch (action) {
    case 'ADD':
    case 'ACCEPT': {
      const res = await api.createBacklogItem({ ...base, sprint_id: sprintId });
      return { ok: true, message: `"${formData.title}" added to sprint.`, data: res };
    }
    case 'SWAP': {
      const target = recommendation?.target_ticket;
      if (!target?.id) throw new Error('No swap target in recommendation.');
      await api.updateBacklogItem(target.id, { sprint_id: null });
      const res = await api.createBacklogItem({ ...base, sprint_id: sprintId });
      return { ok: true, message: `Swapped: "${target.title}" → backlog. "${formData.title}" → sprint.`, data: res };
    }
    case 'DEFER': {
      const res = await api.createBacklogItem({ ...base, sprint_id: null });
      return { ok: true, message: `"${formData.title}" saved to backlog for next sprint.`, data: res };
    }
    case 'SPLIT': {
      const res = await api.createBacklogItem({ ...base, sprint_id: null });
      return {
        ok: true, requiresManual: true,
        message: `"${formData.title}" saved to backlog. Split it into sub-tickets before planning.`,
        data: res,
      };
    }
    default:
      throw new Error(`Unknown action: ${action}`);
  }
}

// ─── Send feedback to MongoDB (best-effort) ───────────────────────────────────
async function logFeedback(logId, accepted, takenAction) {
  if (!logId) return;
  try {
    await api.recordImpactFeedback(logId, {
      accepted,
      taken_action: takenAction,
    });
  } catch (_) {}
}

// ─── Recommendation Card ──────────────────────────────────────────────────────
function RecommendationCard({ recommendation, explanation, formData, sprintId, spaceId, logId, onActionDone }) {
  const [executing, setExecuting] = useState(false);
  const [done,      setDone]      = useState(false);
  const [doneMsg,   setDoneMsg]   = useState('');
  const [planOpen,  setPlanOpen]  = useState(false);

  const type = recommendation?.recommendation_type ?? 'DEFER';
  const meta = ACTION_META[type] ?? ACTION_META.DEFER;
  const alternatives = Object.keys(ACTION_META).filter(k => k !== type && k !== 'ACCEPT');

  const handleAction = async (actionType) => {
    setExecuting(true);
    try {
      const result = await executeAction(actionType, recommendation, sprintId, spaceId, formData);
      // Record what the user actually did in MongoDB
      await logFeedback(
        logId,
        true,
        actionType === type ? 'FOLLOWED_RECOMMENDATION' : 'IGNORED_RECOMMENDATION',
      );
      setDone(true);
      setDoneMsg(result.message);
      onActionDone?.(result);
    } catch (err) {
      alert('Action failed: ' + err.message);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className={`border-2 rounded-xl p-5 ${meta.cardBg} ${meta.border}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{meta.icon}</span>
          <div>
            <div className="text-xs font-bold tracking-widest text-gray-500 mb-0.5">AI RECOMMENDATION</div>
            <div className={`text-base font-extrabold ${meta.text} leading-tight`}>
              {explanation?.short_title ?? type}
            </div>
          </div>
        </div>
        <span className={`text-xs font-bold px-3 py-1 rounded-full ${meta.badge} shrink-0`}>{type}</span>
      </div>

      {/* Reasoning */}
      <p className={`text-sm mb-3 leading-relaxed ${meta.text} opacity-90`}>{recommendation?.reasoning}</p>

      {/* Detailed explanation */}
      {explanation?.detailed_explanation &&
        explanation.detailed_explanation !== recommendation?.reasoning && (
        <div className="bg-white bg-opacity-60 rounded-lg p-3 mb-3 text-sm text-gray-700 leading-relaxed">
          {explanation.detailed_explanation}
        </div>
      )}

      {/* Swap target */}
      {recommendation?.target_ticket && (
        <div className="bg-white bg-opacity-70 border border-blue-100 rounded-lg p-3 mb-3 flex items-center gap-3">
          <span className="text-xl shrink-0">🎯</span>
          <div>
            <div className="text-xs font-bold text-gray-500 tracking-widest mb-0.5">SWAP TARGET</div>
            <div className="text-sm font-bold text-gray-800">{recommendation.target_ticket.title}</div>
            <div className="text-xs text-gray-500">
              {recommendation.target_ticket.story_points} SP · {recommendation.target_ticket.priority} · {recommendation.target_ticket.status}
            </div>
          </div>
        </div>
      )}

      {/* Action plan */}
      {recommendation?.action_plan && Object.keys(recommendation.action_plan).length > 0 && (
        <div className="mb-3">
          <button onClick={() => setPlanOpen(o => !o)}
            className={`text-xs font-bold tracking-widest flex items-center gap-1 ${meta.text} opacity-70 hover:opacity-100`}>
            {planOpen ? '▼' : '▶'} ACTION PLAN
          </button>
          {planOpen && (
            <div className="mt-2 space-y-1">
              {Object.entries(recommendation.action_plan).map(([k, v]) => (
                <div key={k} className={`text-xs flex gap-2 ${meta.text}`}>
                  <span className="opacity-50">→</span><span>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Risk summary */}
      {explanation?.risk_summary && (
        <div className="text-xs text-gray-400 font-mono mb-4">{explanation.risk_summary}</div>
      )}

      {/* CTA */}
      {done ? (
        <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm font-semibold text-green-700 flex items-center gap-2">
          ✅ {doneMsg}
        </div>
      ) : (
        <>
          <button onClick={() => handleAction(type)} disabled={executing}
            className={`w-full ${meta.bg} ${meta.hover} text-white font-bold py-2.5 px-4 rounded-lg text-sm flex items-center justify-center gap-2 disabled:opacity-60 transition-opacity mb-3`}>
            {executing
              ? <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" /> Applying…</>
              : <>{meta.icon} {meta.label}</>}
          </button>
          <div>
            <div className="text-xs font-semibold text-gray-400 mb-2 tracking-widest">OR CHOOSE MANUALLY</div>
            <div className="flex flex-wrap gap-2">
              {alternatives.map(alt => {
                const m = ACTION_META[alt];
                return (
                  <button key={alt} onClick={() => handleAction(alt)} disabled={executing}
                    className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg border-2 ${m.border} ${m.cardBg} ${m.text} hover:opacity-80 disabled:opacity-40`}>
                    {m.icon} {alt}
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

// ─── Main ImpactAnalyzer ──────────────────────────────────────────────────────
export default function ImpactAnalyzer({ sprints, spaceId }) {
  const [selectedSprint, setSelectedSprint] = useState(null);
  const [formData, setFormData] = useState({
    title: '', description: '', story_points: 5, priority: 'Medium', type: 'Task',
  });
  const [analysis,      setAnalysis]      = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [sprintContext, setSprintContext]  = useState(null);
  const [actionResult,  setActionResult]  = useState(null);

  // Auto-select active sprint on load
  useEffect(() => {
    const active = sprints?.find(s => s.status === 'Active') || sprints?.[0];
    if (active && !selectedSprint) {
      setSelectedSprint(active);
      loadSprintContext(active.id);
    }
  }, [sprints]);

  const loadSprintContext = async (sprintId) => {
    try {
      const ctx = await api.getSprintContext(sprintId);
      setSprintContext(ctx);
    } catch (err) {
      console.error('Sprint context error:', err);
      setSprintContext(null);
    }
  };

  const handleSprintChange = (sprintId) => {
    const sprint = sprints.find(s => s.id === sprintId);
    setSelectedSprint(sprint);
    setAnalysis(null);
    setActionResult(null);
    if (sprint) loadSprintContext(sprint.id);
  };

  const handleAnalyze = async () => {
    if (!selectedSprint || !formData.title.trim()) {
      alert('Please select a sprint and enter a title');
      return;
    }
    setLoading(true);
    setAnalysis(null);
    setActionResult(null);
    try {
      const result = await api.analyzeImpact({
        sprint_id:    selectedSprint.id,
        title:        formData.title,
        description:  formData.description,
        story_points: formData.story_points,
        priority:     formData.priority,
        type:         formData.type,
      });
      setAnalysis(result);
      // No local storage needed — impact_routes.py now logs to MongoDB
      // and Analytics tab reads from /api/impact/history/{spaceId}
    } catch (err) {
      console.error('Analysis failed:', err);
      alert('Failed to analyze impact: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => ({
    safe:     'bg-green-50  border-green-200  text-green-800',
    warning:  'bg-yellow-50 border-yellow-200 text-yellow-800',
    critical: 'bg-red-50    border-red-200    text-red-800',
  }[status] || 'bg-gray-50 border-gray-200 text-gray-800');

  const getStatusBadge = (status) => ({
    safe: '🟢 Safe', warning: '🟡 Warning', critical: '🔴 Critical',
  }[status] || '⚪ Unknown');

  // Resolve spaceId: from prop → sprint object → fallback ''
  const resolvedSpaceId = spaceId || selectedSprint?.space_id || '';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

      {/* ════ LEFT — Form ════ */}
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Analyze New Requirement</h2>

          {/* Sprint selector */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Sprint</label>
            <select value={selectedSprint?.id || ''} onChange={e => handleSprintChange(e.target.value)}
              className="w-full bg-white text-gray-900 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none">
              <option value="">Select Sprint…</option>
              {sprints?.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.status}){s.status === 'Active' ? ' 🔥' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Sprint status */}
          {sprintContext && (
            <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">📊 Sprint Status</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {[
                  ['Load',      `${sprintContext.current_load} SP`],
                  ['Items',     sprintContext.item_count],
                  ['Days Left', sprintContext.days_remaining],
                  ['Progress',  `${sprintContext.sprint_progress}%`],
                ].map(([label, val]) => (
                  <div key={label} className="flex justify-between">
                    <span className="text-blue-700">{label}:</span>
                    <span className="font-bold text-blue-900">{val}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3">
                <div className="flex justify-between text-xs text-blue-700 mb-1">
                  <span>Sprint Capacity</span>
                  <span>{sprintContext.current_load} / {sprintContext.team_velocity} SP</span>
                </div>
                <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${
                    (sprintContext.current_load / (sprintContext.team_velocity || 1)) > 0.9 ? 'bg-red-500'
                    : (sprintContext.current_load / (sprintContext.team_velocity || 1)) > 0.7 ? 'bg-amber-400'
                    : 'bg-blue-500'}`}
                    style={{ width: `${Math.min(100, (sprintContext.current_load / (sprintContext.team_velocity || 1)) * 100)}%` }} />
                </div>
              </div>
            </div>
          )}

          {/* Title */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Title *</label>
            <input type="text" value={formData.title}
              onChange={e => setFormData({ ...formData, title: e.target.value })}
              className="w-full bg-white text-gray-900 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none placeholder-gray-400"
              placeholder="e.g., Add payment gateway integration" />
          </div>

          {/* Description */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              className="w-full bg-white text-gray-900 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none placeholder-gray-400 resize-none"
              rows={4} placeholder="Describe the requirement…" />
          </div>

          {/* Story points + Priority */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Story Points</label>
              <input type="number" min="1" max="21" value={formData.story_points}
                onChange={e => setFormData({ ...formData, story_points: parseInt(e.target.value) || 5 })}
                className="w-full bg-white text-gray-900 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
              <select value={formData.priority} onChange={e => setFormData({ ...formData, priority: e.target.value })}
                className="w-full bg-white text-gray-900 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                <option>Low</option><option>Medium</option><option>High</option><option>Critical</option>
              </select>
            </div>
          </div>

          {/* Type */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <select value={formData.type} onChange={e => setFormData({ ...formData, type: e.target.value })}
              className="w-full bg-white text-gray-900 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none">
              <option>Task</option><option>Story</option><option>Bug</option><option>Subtask</option>
            </select>
          </div>

          {/* Analyze button */}
          <button onClick={handleAnalyze} disabled={loading || !selectedSprint}
            className="w-full bg-gradient-to-r from-pink-600 to-rose-600 text-white px-6 py-3 rounded-lg hover:opacity-90 font-medium disabled:opacity-50 flex items-center justify-center gap-2">
            {loading
              ? <><div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" /> Analyzing…</>
              : (<><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg> Analyze Impact</>)}
          </button>
        </div>
      </div>

      {/* ════ RIGHT — Results ════ */}
      <div className="space-y-4">

        {/* Empty state */}
        {!analysis && !loading && (
          <div className="bg-white rounded-xl shadow-sm p-8 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">No Analysis Yet</h3>
            <p className="text-gray-600">Fill in the form and click "Analyze Impact"</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="bg-white rounded-xl shadow-sm p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4" />
            <p className="text-gray-600 font-medium">Running ML models…</p>
            <p className="text-gray-400 text-sm mt-1">Effort · Schedule · Quality · Productivity</p>
          </div>
        )}

        {/* Results */}
        {analysis?.display && (
          <>
            <h2 className="text-xl font-bold text-gray-800">Impact Analysis Results</h2>

            {[
              { key: 'effort',       icon: '⏱️', label: 'Effort Estimate'     },
              { key: 'schedule',     icon: '📅', label: 'Schedule Risk'       },
              { key: 'productivity', icon: '📉', label: 'Productivity Impact' },
              { key: 'quality',      icon: '🐛', label: 'Quality Risk'        },
            ].map(({ key, icon, label }) => {
              const m = analysis.display[key];
              if (!m) return null;
              return (
                <div key={key} className={`border-2 rounded-xl p-5 ${getStatusColor(m.status)}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="text-sm font-medium opacity-70 mb-1">{icon} {label}</div>
                      <div className="text-2xl font-bold">{m.value}</div>
                    </div>
                    <span className="px-3 py-1 rounded-full text-sm font-semibold bg-white bg-opacity-50">
                      {getStatusBadge(m.status)}
                    </span>
                  </div>
                  <div className="text-sm font-semibold mb-1">{m.label}</div>
                  <div className="text-sm opacity-80">{m.sub_text}</div>
                </div>
              );
            })}

            <div className="flex items-center gap-3 py-1">
              <div className="flex-1 h-px bg-gray-200" />
              <span className="text-xs font-bold tracking-widest text-gray-400">RECOMMENDATION</span>
              <div className="flex-1 h-px bg-gray-200" />
            </div>

            {analysis.recommendation && (
              <RecommendationCard
                recommendation={analysis.recommendation}
                explanation={analysis.explanation}
                formData={formData}
                sprintId={selectedSprint?.id}
                spaceId={resolvedSpaceId}
                logId={analysis.log_id}
                onActionDone={(result) => {
                  setActionResult(result);
                  if (selectedSprint) loadSprintContext(selectedSprint.id);
                }}
              />
            )}

            {/* Split reminder */}
            {actionResult?.requiresManual && (
              <div className="bg-purple-50 border border-purple-200 rounded-lg px-4 py-3 text-sm text-purple-800 flex items-start gap-2">
                <span>✂️</span>
                <div>
                  <div className="font-bold mb-0.5">Manual Split Required</div>
                  <div>{actionResult.message}</div>
                </div>
              </div>
            )}

            {/* Reset */}
            {actionResult && (
              <button
                onClick={() => {
                  setAnalysis(null); setActionResult(null);
                  setFormData({ title: '', description: '', story_points: 5, priority: 'Medium', type: 'Task' });
                }}
                className="w-full border-2 border-gray-200 text-gray-600 font-semibold py-2.5 rounded-lg hover:bg-gray-50 text-sm">
                ↺ Analyze Another Ticket
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}