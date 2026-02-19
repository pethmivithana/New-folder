import { useState, useEffect } from 'react';
import api from './api';

export default function AIStoryPointSuggester({ title, description, onSuggestion }) {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Auto-predict when title and description have sufficient content
    if (title && description && title.length > 5 && description.length > 10) {
      const timer = setTimeout(() => {
        getPrediction();
      }, 1000); // Debounce
      
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

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.7) return 'text-green-600 bg-green-100';
    if (confidence >= 0.4) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.7) return 'High';
    if (confidence >= 0.4) return 'Medium';
    return 'Low';
  };

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
              Enter a title and description to get AI-powered story point suggestions based on complexity analysis.
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

  return (
    <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-5 border-2 border-purple-200">
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
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getConfidenceColor(prediction.confidence)}`}>
            {getConfidenceLabel(prediction.confidence)} Confidence ({(prediction.confidence * 100).toFixed(0)}%)
          </span>
          <button
            onClick={applyPrediction}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm"
          >
            Apply Suggestion
          </button>
        </div>
      </div>

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
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
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

      {/* Complexity Indicators */}
      {showDetails && Object.keys(prediction.complexity_indicators).length > 0 && (
        <div className="bg-white rounded-lg p-4">
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

      {/* Refresh Button */}
      <button
        onClick={getPrediction}
        className="w-full mt-3 py-2 text-center text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center justify-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Refresh Suggestion
      </button>
    </div>
  );
}