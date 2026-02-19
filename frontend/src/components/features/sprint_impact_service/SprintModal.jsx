import { useState, useEffect } from 'react';
import api from './api';

export default function SprintModal({ space, sprint, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    goal: '',
    duration_type: '2 Weeks',
    start_date: '',
    end_date: '',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (sprint) {
      setFormData({
        name: sprint.name,
        goal: sprint.goal,
        duration_type: sprint.duration_type,
        start_date: sprint.start_date || '',
        end_date: sprint.end_date || '',
      });
    }
  }, [sprint]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const data = {
        ...formData,
        space_id: space.id,
      };

      // Only include dates for custom duration
      if (formData.duration_type !== 'Custom') {
        delete data.start_date;
        delete data.end_date;
      }

      if (sprint) {
        // Only update name and goal for existing sprints
        await api.updateSprint(sprint.id, {
          name: formData.name,
          goal: formData.goal,
        });
      } else {
        await api.createSprint(data);
      }

      await onSave();
      onClose();
    } catch (error) {
      alert('Failed to save sprint: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">
          {sprint ? 'Edit Sprint' : 'Create New Sprint'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sprint Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Sprint 1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sprint Goal *
            </label>
            <textarea
              required
              value={formData.goal}
              onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="What do you want to achieve in this sprint?"
            />
          </div>

          {!sprint && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Duration *
                </label>
                <select
                  value={formData.duration_type}
                  onChange={(e) => setFormData({ ...formData, duration_type: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  <option value="1 Week">1 Week</option>
                  <option value="2 Weeks">2 Weeks</option>
                  <option value="3 Weeks">3 Weeks</option>
                  <option value="4 Weeks">4 Weeks</option>
                  <option value="Custom">Custom</option>
                </select>
              </div>

              {formData.duration_type === 'Custom' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Start Date *
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      End Date *
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                </div>
              )}
            </>
          )}

          {sprint && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                Note: Sprint duration cannot be changed after creation
              </p>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50"
            >
              {loading ? 'Saving...' : sprint ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
