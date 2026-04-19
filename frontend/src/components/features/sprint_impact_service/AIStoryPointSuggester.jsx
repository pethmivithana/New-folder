import { useState, useEffect } from 'react';
import api from './api';

/**
 * AIStoryPointSuggester.jsx — updated to match backend improvements
 *
 * What changed and why:
 *
 * 1. CONFIDENCE THRESHOLDS REALIGNED
 *    Old: High ≥ 0.7, Medium ≥ 0.4 — but backend floor was 0.55,
 *         so Low badge was never shown even for near-empty inputs.
 *    New: High ≥ 0.65, Medium ≥ 0.35, Low < 0.35
 *         These thresholds match the new backend range (0.15–0.95).
 *
 * 2. SIGNAL QUALITY PANEL
 *    The backend now returns a `signal_quality` object explaining what
 *    drove the estimate. A collapsible "Why this estimate?" section
 *    shows the user: word count, vocabulary match, whether methods agreed,
 *    and what would improve accuracy.
 *
 * 3. 21 SP SPLIT WARNING
 *    When the backend suggests 21 SP (new top bin), a yellow banner tells
 *    the user this ticket should probably be split before sprint planning.
 *
 * 4. SP BIN DISPLAY
 *    The footer now shows the valid bins [1,2,3,5,8,13,21] so the user
 *    understands why the number jumped (e.g. from 10 → 8 or 10 → 13).
 */

export default function AIStoryPointSuggester({ title, description, onSuggestion }) {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showSignalQuality, setShowSignalQuality] = useState(false);

  useEffect(() => {
    if (title && description && title.length > 5 && description.length > 10) {
      const timer = setTimeout(() => {
        getPrediction();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [title, description]);

  const getPrediction = async () => {
    if (!title || !description) return;
    setLoading(true);
    try {
      const result = await api.predictStoryPoints({ title, description });
      setPrediction(result);
    } catch (error) {
      console.error('Prediction failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyPrediction = () => {
    if (prediction && onSuggestion) {
      onSuggestion(prediction.suggested_points);
    }
  };

  /**
   * FIX 1: Thresholds realigned to new backend output range.
   *
   * Old thresholds:    High ≥ 0.7,  Medium ≥ 0.4
   * Backend old floor: 0.55 (Low badge was unreachable)
   *
   * New thresholds:    High ≥ 0.65, Medium ≥ 0.35, Low < 0.35
   * Backend new range: 0.15–0.95  (all three badges now reachable)
   */
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.65) return 'text-green-600 bg-green-100';
    if (confidence >= 0.35) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.65) return 'High';
    if (confidence >= 0.35) return 'Medium';
    return 'Low';
  };

  // Empty state
  if (!title || !description) {
    return (
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-4 border-2 border-dashed border-purple-200">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-purple-900 mb-1">AI Story Point Suggester</h4>
            <p className="text-sm text-purple-700">
              Enter a title and description to get AI-powered story point suggestions.
              Longer, more detailed descriptions produce higher-confidence estimates.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-4 border-2 border-purple-200">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          <span className="text-purple-700 font-medium">Analyzing complexity...</span>
        </div>
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-4 border-2 border-purple-200">
        <button
          onClick={getPrediction}
          className="w-full flex items-center justify-center gap-2 text-purple-700 font-medium hover:text-purple-900 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          Get AI Suggestion
        </button>
      </div>
    );
  }

  const sq = prediction.signal_quality || {};
  const confidenceLabel = getConfidenceLabel(prediction.confidence);
  const isLargeSplit = prediction.suggested_points === 21;

  return (
    <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-5 border-2 border-purple-200">

      {/* Header row */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h4 className="font-bold text-purple-900 text-lg mb-1">AI Suggestion</h4>
            <div className="flex items-center gap-2">
              <span className="text-4xl font-bold text-purple-600">{prediction.suggested_points}</span>
              <span className="text-gray-600">story points</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          {/* FIX 1: Badge uses new thresholds — Low is now reachable */}
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getConfidenceColor(prediction.confidence)}`}>
            {confidenceLabel} Confidence ({(prediction.confidence * 100).toFixed(0)}%)
          </span>
          <button
            onClick={applyPrediction}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm"
          >
            Apply Suggestion
          </button>
        </div>
      </div>

      {/* FIX 3: 21 SP split warning */}
      {isLargeSplit && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-3 flex items-start gap-2">
          <svg className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-sm text-yellow-800">
            <span className="font-semibold">Large ticket detected.</span> 21 SP is the largest Fibonacci value — this ticket should probably be split into smaller deliverable slices before sprint planning.
          </p>
        </div>
      )}

      {/* Low confidence warning */}
      {confidenceLabel === 'Low' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3 flex items-start gap-2">
          <svg className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-red-800">
            <span className="font-semibold">Low confidence estimate.</span> Add more detail to the description to improve accuracy.
            {sq.confidence_notes && sq.confidence_notes.length > 0 && (
              <span className="block mt-1 text-red-700">{sq.confidence_notes[0]}</span>
            )}
          </p>
        </div>
      )}

      {/* Reasoning */}
      <div className="bg-white rounded-lg p-4 mb-3">
        <div className="flex items-center justify-between mb-3">
          <h5 className="font-semibold text-gray-800">Analysis</h5>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center gap-1"
          >
            {showDetails ? 'Hide' : 'Show'} Details
            <svg
              className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        <ul className="space-y-2">
          {prediction.reasoning.map((reason, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
              <svg className="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Complexity keywords (shown in details) */}
      {showDetails && Object.keys(prediction.complexity_indicators || {}).length > 0 && (
        <div className="bg-white rounded-lg p-4 mb-3">
          <h5 className="font-semibold text-gray-800 mb-3">Detected Keywords</h5>
          <div className="flex flex-wrap gap-2">
            {Object.entries(prediction.complexity_indicators).map(([keyword, count]) => (
              <span
                key={keyword}
                className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium"
              >
                {keyword} {count > 1 && `(${count}x)`}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* FIX 2: Signal quality panel — shows what drove the estimate */}
      {showDetails && sq && (
        <div className="bg-white rounded-lg p-4 mb-3">
          <button
            onClick={() => setShowSignalQuality(!showSignalQuality)}
            className="w-full flex items-center justify-between text-sm font-semibold text-gray-800 mb-2"
          >
            <span>Why this estimate?</span>
            <svg
              className={`w-4 h-4 transition-transform text-gray-500 ${showSignalQuality ? 'rotate-180' : ''}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showSignalQuality && (
            <div className="space-y-2 text-xs text-gray-600">

              {/* Blend weights */}
              <div className="flex items-center justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">Blend weights</span>
                <span className="font-mono">
                  TF-IDF {Math.round((sq.tfidf_weight_used || 0) * 100)}%
                  &nbsp;/&nbsp;
                  Keywords {Math.round((sq.keyword_weight_used || 0) * 100)}%
                </span>
              </div>

              {/* Word count */}
              <div className="flex items-center justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">Description words</span>
                <span className={`font-semibold ${sq.description_word_count < 10 ? 'text-red-600' : sq.description_word_count < 20 ? 'text-yellow-600' : 'text-green-600'}`}>
                  {sq.description_word_count}
                  {sq.description_word_count < 10 && ' — add more detail'}
                  {sq.description_word_count >= 10 && sq.description_word_count < 20 && ' — good'}
                  {sq.description_word_count >= 20 && ' — detailed'}
                </span>
              </div>

              {/* Vocab hit rate */}
              {sq.tfidf_available && (
                <div className="flex items-center justify-between py-1 border-b border-gray-100">
                  <span className="text-gray-500">Vocabulary match</span>
                  <span className={`font-semibold ${sq.vocab_hit_rate < 0.15 ? 'text-red-600' : 'text-green-600'}`}>
                    {(sq.vocab_hit_rate * 100).toFixed(0)}%
                  </span>
                </div>
              )}

              {/* Methods agreement */}
              <div className="flex items-center justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">Methods agree</span>
                <span className={`font-semibold ${sq.methods_agreed ? 'text-green-600' : 'text-yellow-600'}`}>
                  {sq.methods_agreed ? 'Yes' : 'No — estimate less certain'}
                </span>
              </div>

              {/* Confidence notes */}
              {sq.confidence_notes && sq.confidence_notes.length > 0 && (
                <div className="pt-1">
                  <span className="text-gray-500 block mb-1">Notes</span>
                  <ul className="space-y-1">
                    {sq.confidence_notes.map((note, i) => (
                      <li key={i} className="text-gray-700 flex items-start gap-1">
                        <span className="text-purple-400 mt-0.5">·</span>
                        <span>{note}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* FIX 4: Valid bins shown to user */}
              <div className="pt-2 border-t border-gray-100">
                <span className="text-gray-500 block mb-1">Valid story point values</span>
                <div className="flex gap-1 flex-wrap">
                  {[1, 2, 3, 5, 8, 13, 21].map(bin => (
                    <span
                      key={bin}
                      className={`px-2 py-0.5 rounded text-xs font-mono ${
                        bin === prediction.suggested_points
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {bin}
                    </span>
                  ))}
                </div>
                <p className="text-gray-400 mt-1">Estimates snap to the nearest Fibonacci value</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Refresh */}
      <button
        onClick={getPrediction}
        className="w-full mt-2 py-2 text-center text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center justify-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Refresh Suggestion
      </button>
    </div>
  );
}