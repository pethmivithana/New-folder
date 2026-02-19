import { useState, useEffect } from 'react';
import api from './api';
import AIStoryPointSuggester from './AIStoryPointSuggester';

export default function BacklogModal({ space, sprints, item, onClose, onSave }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'Task',
    priority: 'Medium',
    story_points: 5,
    sprint_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [showAISuggester, setShowAISuggester] = useState(true);

  useEffect(() => {
    if (item) {
      setFormData({
        title: item.title,
        description: item.description,
        type: item.type,
        priority: item.priority,
        story_points: item.story_points,
        sprint_id: item.sprint_id || '',
      });
    }
  }, [item]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const data = {
        ...formData,
        space_id: space.id,
        sprint_id: formData.sprint_id || null,
      };

      if (item) {
        await api.updateBacklogItem(item.id, data);
      } else {
        await api.createBacklogItem(data);
      }

      await onSave();
      onClose();
    } catch (error) {
      alert('Failed to save backlog item: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAISuggestion = (suggestedPoints) => {
    setFormData({ ...formData, story_points: suggestedPoints });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-800">
              {item ? 'Edit Backlog Item' : 'Create Backlog Item'}
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title *
            </label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter item title"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              required
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Describe the item in detail. Include technical requirements, interfaces, integrations, etc."
            />
            <p className="mt-1 text-xs text-gray-500">
              💡 Tip: More detailed descriptions help AI suggest better story points
            </p>
          </div>

          {/* AI Story Point Suggester */}
          {showAISuggester && (
            <AIStoryPointSuggester
              title={formData.title}
              description={formData.description}
              onSuggestion={handleAISuggestion}
            />
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type *
              </label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="Task">Task</option>
                <option value="Subtask">Subtask</option>
                <option value="Bug">Bug</option>
                <option value="Story">Story</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority *
              </label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Story Points * (3-15)
              </label>
              <button
                type="button"
                onClick={() => setShowAISuggester(!showAISuggester)}
                className="text-sm text-purple-600 hover:text-purple-700 font-medium"
              >
                {showAISuggester ? 'Hide' : 'Show'} AI Suggester
              </button>
            </div>
            <input
              type="number"
              required
              min="3"
              max="15"
              value={formData.story_points}
              onChange={(e) => setFormData({ ...formData, story_points: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assign to Sprint (Optional)
            </label>
            <select
              value={formData.sprint_id}
              onChange={(e) => setFormData({ ...formData, sprint_id: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">No Sprint (Backlog)</option>
              {sprints.map((sprint) => (
                <option key={sprint.id} value={sprint.id}>
                  {sprint.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex gap-3 pt-4 sticky bottom-0 bg-white border-t border-gray-200 -mx-6 -mb-6 px-6 py-4 rounded-b-2xl">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:opacity-50"
            >
              {loading ? 'Saving...' : item ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}