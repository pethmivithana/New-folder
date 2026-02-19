import { useState, useEffect } from 'react';
import api from './api';

export default function ImpactAnalyzer({ sprints }) {
  const [selectedSprint, setSelectedSprint] = useState(null);
  const [formData, setFormData] = useState({
    title: '', description: '', story_points: 5, priority: 'Medium',
  });
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sprintContext, setSprintContext] = useState(null);

  useEffect(() => {
    const activeSprint = sprints?.find(s => s.status === 'Active') || sprints?.[0];
    if (activeSprint) {
      setSelectedSprint(activeSprint);
      loadSprintContext(activeSprint.id);
    }
  }, [sprints]);

  const loadSprintContext = async (sprintId) => {
    try {
      const context = await api.getSprintContext(sprintId);
      setSprintContext(context);
    } catch (error) {
      console.error('Failed to load sprint context:', error);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedSprint || !formData.title.trim()) {
      alert('Please select a sprint and enter a title');
      return;
    }

    setLoading(true);
    try {
      const payload = { ...formData, sprint_id: selectedSprint.id };
      console.log('Sending analysis request:', payload);
      
      const result = await api.analyzeImpact(payload);
      console.log('Analysis result received:', result);
      
      if (!result.display) {
        console.error('No display object in result:', result);
        alert('Analysis completed but display data missing. Check console.');
      }
      
      setAnalysis(result);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Failed to analyze impact: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => ({
    safe: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    critical: 'bg-red-50 border-red-200 text-red-800',
  }[status] || 'bg-gray-50 border-gray-200 text-gray-800');

  const getStatusBadge = (status) => ({
    safe: '🟢 Safe', warning: '🟡 Warning', critical: '🔴 Critical',
  }[status] || '⚪ Unknown');

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Analyze New Requirement</h2>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Sprint</label>
            <select
              value={selectedSprint?.id || ''}
              onChange={(e) => {
                const sprint = sprints.find(s => s.id === e.target.value);
                setSelectedSprint(sprint);
                if (sprint) loadSprintContext(sprint.id);
              }}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select Sprint...</option>
              {sprints?.map(sprint => (
                <option key={sprint.id} value={sprint.id}>{sprint.name} ({sprint.status})</option>
              ))}
            </select>
          </div>

          {sprintContext && (
            <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">📊 Sprint Status</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-blue-700">Load:</span>
                  <span className="font-bold text-blue-900">{sprintContext.current_load} SP</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700">Items:</span>
                  <span className="font-bold text-blue-900">{sprintContext.item_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700">Days Left:</span>
                  <span className="font-bold text-blue-900">{sprintContext.days_remaining}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700">Progress:</span>
                  <span className="font-bold text-blue-900">{sprintContext.sprint_progress}%</span>
                </div>
              </div>
            </div>
          )}

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., Add payment gateway integration"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500"
              rows="4"
              placeholder="Describe the requirement..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Story Points</label>
              <input
                type="number"
                min="1"
                max="21"
                value={formData.story_points}
                onChange={(e) => setFormData({ ...formData, story_points: parseInt(e.target.value) || 5 })}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500"
              >
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
                <option>Critical</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={loading || !selectedSprint}
            className="w-full bg-gradient-to-r from-pink-600 to-rose-600 text-white px-6 py-3 rounded-lg hover:opacity-90 font-medium disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Analyzing...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Analyze Impact
              </>
            )}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {!analysis && !loading && (
          <div className="bg-white rounded-xl shadow-sm p-8 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">No Analysis Yet</h3>
            <p className="text-gray-600">Fill in the form and click "Analyze Impact"</p>
          </div>
        )}

        {loading && (
          <div className="bg-white rounded-xl shadow-sm p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Running ML models...</p>
          </div>
        )}

        {analysis?.display && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-800">Impact Analysis Results</h2>

            <div className={`border-2 rounded-xl p-5 ${getStatusColor(analysis.display.effort.status)}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="text-sm font-medium opacity-70 mb-1">⏱️ Effort Estimate</div>
                  <div className="text-2xl font-bold">{analysis.display.effort.value}</div>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-semibold bg-white bg-opacity-50">
                  {getStatusBadge(analysis.display.effort.status)}
                </span>
              </div>
              <div className="text-sm font-semibold mb-1">{analysis.display.effort.label}</div>
              <div className="text-sm opacity-80">{analysis.display.effort.sub_text}</div>
            </div>

            <div className={`border-2 rounded-xl p-5 ${getStatusColor(analysis.display.schedule.status)}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="text-sm font-medium opacity-70 mb-1">📅 Schedule Risk</div>
                  <div className="text-2xl font-bold">{analysis.display.schedule.value}</div>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-semibold bg-white bg-opacity-50">
                  {getStatusBadge(analysis.display.schedule.status)}
                </span>
              </div>
              <div className="text-sm font-semibold mb-1">{analysis.display.schedule.label}</div>
              <div className="text-sm opacity-80">{analysis.display.schedule.sub_text}</div>
            </div>

            <div className={`border-2 rounded-xl p-5 ${getStatusColor(analysis.display.productivity.status)}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="text-sm font-medium opacity-70 mb-1">📉 Productivity Impact</div>
                  <div className="text-2xl font-bold">{analysis.display.productivity.value}</div>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-semibold bg-white bg-opacity-50">
                  {getStatusBadge(analysis.display.productivity.status)}
                </span>
              </div>
              <div className="text-sm font-semibold mb-1">{analysis.display.productivity.label}</div>
              <div className="text-sm opacity-80">{analysis.display.productivity.sub_text}</div>
            </div>

            <div className={`border-2 rounded-xl p-5 ${getStatusColor(analysis.display.quality.status)}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="text-sm font-medium opacity-70 mb-1">🐛 Quality Risk</div>
                  <div className="text-2xl font-bold">{analysis.display.quality.value}</div>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-semibold bg-white bg-opacity-50">
                  {getStatusBadge(analysis.display.quality.status)}
                </span>
              </div>
              <div className="text-sm font-semibold mb-1">{analysis.display.quality.label}</div>
              <div className="text-sm opacity-80">{analysis.display.quality.sub_text}</div>
            </div>

            {analysis.recommendation && (
              <div className="bg-indigo-50 border-2 border-indigo-200 rounded-xl p-5">
                <h3 className="text-lg font-bold text-indigo-900 mb-2">
                  📋 Recommendation: {analysis.recommendation.recommendation_type}
                </h3>
                <p className="text-indigo-800 mb-3">{analysis.recommendation.reasoning}</p>
                {analysis.recommendation.action_plan && Object.keys(analysis.recommendation.action_plan).length > 0 && (
                  <div className="mt-3 space-y-1">
                    <div className="font-semibold text-indigo-900 text-sm">Action Plan:</div>
                    {Object.entries(analysis.recommendation.action_plan).map(([key, value]) => (
                      <div key={key} className="text-sm text-indigo-800">• {value}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}