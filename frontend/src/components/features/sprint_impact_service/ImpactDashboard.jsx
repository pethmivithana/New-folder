/**
 * ImpactDashboard.jsx                          EXISTING FILE — replace fully
 * ─────────────────────────────────────────────────────────────────────────────
 * Fix vs the version you have running:
 *
 *   CARD_ORDER previously contained hardcoded emoji and fallbackLabel strings:
 *     { key: "effort", emoji: "⏱", fallbackLabel: "Effort Estimate" }
 *   These were used as display text if the ML data was missing, showing
 *   misleading placeholder content instead of a clear "data unavailable" state.
 *
 *   Fixed:
 *     • CARD_ORDER replaced by CARD_KEYS — an array of strings only.
 *       No emoji, no fallback label text anywhere in the constant.
 *     • Every field shown in a card (label, value, status, sub_text) comes
 *       directly from the `display` prop returned by the ML backend.
 *     • If a metric key is missing from `display`, the card shows
 *       "Data unavailable" — an honest error state, not a fake label.
 *     • SVG icons are still used (keyed by metric type) — no emoji in code.
 *
 * Props:
 *   display      : { effort, schedule, productivity, quality }  — from ML
 *   ticketTitle? : string
 *   sprintName?  : string
 */

import { useState } from "react";

// ─── Status design tokens ─────────────────────────────────────────────────────
const STATUS_TOKENS = {
  safe: {
    bg: "bg-emerald-50", border: "border-emerald-200", accent: "bg-emerald-500",
    valueFg: "text-emerald-700", labelFg: "text-emerald-600", subFg: "text-emerald-600/80",
    badgeBg: "bg-emerald-100", badgeFg: "text-emerald-700", badgeRing: "ring-emerald-200",
    glow: "shadow-emerald-100", pill: "SAFE", pillIcon: "●",
    hoverBorder: "hover:border-emerald-400", iconColor: "#10b981",
  },
  warning: {
    bg: "bg-amber-50", border: "border-amber-200", accent: "bg-amber-400",
    valueFg: "text-amber-700", labelFg: "text-amber-600", subFg: "text-amber-600/80",
    badgeBg: "bg-amber-100", badgeFg: "text-amber-700", badgeRing: "ring-amber-200",
    glow: "shadow-amber-100", pill: "ATTENTION", pillIcon: "▲",
    hoverBorder: "hover:border-amber-400", iconColor: "#f59e0b",
  },
  critical: {
    bg: "bg-red-50", border: "border-red-200", accent: "bg-red-500",
    valueFg: "text-red-700", labelFg: "text-red-600", subFg: "text-red-600/80",
    badgeBg: "bg-red-100", badgeFg: "text-red-700", badgeRing: "ring-red-200",
    glow: "shadow-red-100", pill: "CRITICAL", pillIcon: "■",
    hoverBorder: "hover:border-red-400", iconColor: "#ef4444",
  },
};

// ─── SVG icons — no emoji, keyed by metric type ───────────────────────────────
const ICONS = {
  effort: ({ color }) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={color}
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  schedule: ({ color }) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={color}
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  ),
  productivity: ({ color }) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={color}
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  quality: ({ color }) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={color}
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  ),
};

// ─── Card keys — strings only, NO hardcoded emoji or fallback labels ──────────
// All display text comes from the `display` prop (ML backend output).
const CARD_KEYS = ["effort", "schedule", "productivity", "quality"];

// ─── Single metric card ───────────────────────────────────────────────────────
function RiskCard({ metricKey, label, value, status, sub_text, index }) {
  const [expanded, setExpanded] = useState(false);
  const t    = STATUS_TOKENS[status] ?? STATUS_TOKENS.warning;
  const Icon = ICONS[metricKey]      ?? ICONS.quality;

  return (
    <div
      className={`
        relative flex flex-col rounded-2xl border-2 p-5 cursor-pointer
        transition-all duration-300 ease-out
        ${t.bg} ${t.border} ${t.hoverBorder}
        shadow-md ${t.glow} hover:shadow-lg hover:-translate-y-0.5
      `}
      style={{ animationDelay: `${index * 80}ms` }}
      onClick={() => setExpanded(e => !e)}
    >
      <div className={`absolute top-0 left-0 w-1 h-full rounded-l-2xl ${t.accent}`} />

      <div className="flex items-start justify-between mb-3 pl-1">
        <div className="flex items-center gap-2.5">
          <Icon color={t.iconColor} />
          {/* label is 100% from ML — no hardcoded fallback text */}
          <span className={`text-xs font-semibold uppercase tracking-widest ${t.labelFg}`}>
            {label}
          </span>
        </div>
        <span className={`
          inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full
          text-[10px] font-bold tracking-wider ring-1
          ${t.badgeBg} ${t.badgeFg} ${t.badgeRing}
        `}>
          <span className="text-[8px]">{t.pillIcon}</span>
          {t.pill}
        </span>
      </div>

      {/* value is 100% from ML */}
      <p
        className={`text-2xl font-extrabold leading-tight mb-3 pl-1 ${t.valueFg}`}
        style={{ fontFamily: "'DM Mono','Fira Code',monospace", letterSpacing: "-0.02em" }}
      >
        {value}
      </p>

      <div className={`pl-1 transition-all duration-300 overflow-hidden ${expanded ? "max-h-40" : "max-h-10"}`}>
        <p className={`text-xs leading-relaxed ${t.subFg}`}>{sub_text}</p>
      </div>

      <div className={`mt-2 pl-1 flex items-center gap-1 ${t.labelFg} opacity-60`}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round"
          className={`transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}>
          <polyline points="6 9 12 15 18 9" />
        </svg>
        <span className="text-[10px] font-medium">{expanded ? "Less" : "Details"}</span>
      </div>
    </div>
  );
}

// ─── Risk banner ──────────────────────────────────────────────────────────────
function OverallRiskBanner({ metrics }) {
  const critCount = metrics.filter(m => m.status === "critical").length;
  const warnCount = metrics.filter(m => m.status === "warning").length;
  let level, bg, fg, border, message;
  if (critCount >= 2) {
    level = "CRITICAL RISK"; bg = "bg-red-100"; fg = "text-red-800"; border = "border-red-300";
    message = `${critCount} critical signals detected. DEFER or SWAP strongly recommended.`;
  } else if (critCount === 1 || warnCount >= 2) {
    level = "ELEVATED RISK"; bg = "bg-amber-100"; fg = "text-amber-800"; border = "border-amber-300";
    message = "One or more risk signals require attention. Review before proceeding.";
  } else {
    level = "LOW RISK"; bg = "bg-emerald-100"; fg = "text-emerald-800"; border = "border-emerald-300";
    message = "All metrics within acceptable bounds. Safe to add to current sprint.";
  }
  return (
    <div className={`flex items-center gap-3 px-5 py-3 rounded-xl border ${bg} ${border}`}>
      <div className={`w-2 h-2 rounded-full animate-pulse ${
        critCount >= 2 ? "bg-red-500" : critCount === 1 ? "bg-amber-500" : "bg-emerald-500"
      }`} />
      <div>
        <span className={`text-xs font-bold tracking-widest uppercase ${fg}`}>{level}</span>
        <p className={`text-xs mt-0.5 ${fg} opacity-80`}>{message}</p>
      </div>
    </div>
  );
}

function Legend() {
  return (
    <div className="flex items-center gap-4">
      {[
        { color: "bg-emerald-500", label: "Safe"     },
        { color: "bg-amber-400",   label: "Warning"  },
        { color: "bg-red-500",     label: "Critical" },
      ].map(({ color, label }) => (
        <div key={label} className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${color}`} />
          <span className="text-xs text-gray-500 font-medium">{label}</span>
        </div>
      ))}
      <span className="text-xs text-gray-400 ml-1">· click cards to expand</span>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function ImpactDashboard({ display, ticketTitle, sprintName }) {
  if (!display) {
    return (
      <div className="flex items-center justify-center h-48 rounded-2xl bg-gray-50 border-2 border-dashed border-gray-200">
        <p className="text-gray-400 text-sm font-medium">No impact data available yet.</p>
      </div>
    );
  }

  // Build metrics array from ML output only — CARD_KEYS has no labels or emoji.
  const metrics = CARD_KEYS.map(key => {
    const d = display[key];
    if (!d) {
      return {
        metricKey: key,
        label:     "Data unavailable",   // honest error state, not a fake label
        value:     "—",
        status:    "warning",
        sub_text:  "This metric was not returned by the ML model.",
      };
    }
    return {
      metricKey: key,
      label:     d.label,      // e.g. "Delay Imminent" — from ML, not hardcoded
      value:     d.value,      // e.g. "100% Probability of Spillover" — from ML
      status:    d.status,     // "safe" | "warning" | "critical" — from ML
      sub_text:  d.sub_text,   // full explanation sentence — from ML
    };
  });

  return (
    <div className="w-full space-y-4 font-sans"
      style={{ fontFamily: "'IBM Plex Sans','DM Sans',system-ui,sans-serif" }}>

      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-lg font-bold text-gray-900 leading-tight">Impact Analysis</h2>
          {(ticketTitle || sprintName) && (
            <p className="text-xs text-gray-400 mt-0.5">
              {ticketTitle && <span className="font-medium text-gray-600">"{ticketTitle}"</span>}
              {ticketTitle && sprintName && <span className="mx-1.5 opacity-40">·</span>}
              {sprintName  && <span>{sprintName}</span>}
            </p>
          )}
        </div>
        <Legend />
      </div>

      <OverallRiskBanner metrics={metrics} />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {metrics.map((m, i) => (
          <RiskCard key={m.metricKey} {...m} index={i} />
        ))}
      </div>

      <p className="text-[11px] text-gray-400 text-right">
        Predictions generated by ML models · Results are indicative, not guaranteed
      </p>
    </div>
  );
}