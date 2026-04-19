import { useState, useEffect } from 'react';
import api from './api';

/**
 * SprintModal.jsx — updated
 *
 * What changed:
 *  1. ASSIGNEE COUNT FIELD (new)
 *     A numeric input lets the user set how many developers are assigned at
 *     sprint planning time. This drives the capacity math in developer exit
 *     replanning (original_devs). Constraints:
 *       - Min: 2 (hard floor from spec)
 *       - Max: space.max_assignees (fetched from the space prop)
 *     The input shows a live capacity preview: "4 devs × 10 days × 6h = 240h"
 *     so planners can see the impact immediately.
 *
 *  2. VALIDATION MESSAGE
 *     If the user tries to submit with a count outside [2, space.max_assignees],
 *     an inline error appears rather than a toast/alert.
 *
 *  3. EDIT MODE
 *     When editing an existing sprint, the assignee_count field is shown and
 *     pre-filled. Sprint duration cannot be changed (existing behaviour kept).
 */
export default function SprintModal({ space, sprint, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name:           '',
    goal:           '',
    duration_type:  '2 Weeks',
    start_date:     '',
    end_date:       '',
    assignee_count: 2,
  });
  const [loading,      setLoading]      = useState(false);
  const [assigneeError, setAssigneeError] = useState('');

  // space.max_assignees is the upper bound — never let a sprint exceed it
  const maxAssignees = space?.max_assignees ?? 10;

  useEffect(() => {
    if (sprint) {
      setFormData({
        name:           sprint.name,
        goal:           sprint.goal,
        duration_type:  sprint.duration_type,
        start_date:     sprint.start_date || '',
        end_date:       sprint.end_date   || '',
        assignee_count: sprint.assignee_count ?? 2,
      });
    }
  }, [sprint]);

  const validateAssigneeCount = (count) => {
    const n = parseInt(count, 10);
    if (isNaN(n) || n < 2) {
      return 'Minimum 2 developers required per sprint.';
    }
    if (n > maxAssignees) {
      return `Cannot exceed ${maxAssignees} developers (space limit).`;
    }
    return '';
  };

  const handleAssigneeChange = (value) => {
    setFormData({ ...formData, assignee_count: parseInt(value, 10) || 2 });
    setAssigneeError(validateAssigneeCount(value));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const err = validateAssigneeCount(formData.assignee_count);
    if (err) {
      setAssigneeError(err);
      return;
    }

    setLoading(true);
    try {
      const data = {
        ...formData,
        space_id:       space.id,
        assignee_count: formData.assignee_count,
      };

      if (formData.duration_type !== 'Custom') {
        delete data.start_date;
        delete data.end_date;
      }

      if (sprint) {
        await api.updateSprint(sprint.id, {
          name:           formData.name,
          goal:           formData.goal,
          assignee_count: formData.assignee_count,
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

  // Live capacity preview shown beneath the assignee count input
  const capacityPreview = () => {
    const devs = formData.assignee_count || 2;
    const durationDays = {
      '1 Week':  5,
      '2 Weeks': 10,
      '3 Weeks': 15,
      '4 Weeks': 20,
      'Custom':  null,
    }[formData.duration_type];

    if (!durationDays) return null;
    const focusHours    = space?.focus_hours_per_day ?? 6;
    const totalHours    = devs * durationDays * focusHours;
    const bufferHours   = Math.round(totalHours * 0.2);
    const plannedHours  = totalHours - bufferHours;

    return (
      <div className="mt-2 p-3 bg-indigo-50 rounded-lg border border-indigo-100 text-xs text-indigo-700 space-y-1">
        <div className="flex justify-between">
          <span>Raw capacity</span>
          <span className="font-semibold">{devs} devs × {durationDays} days × {focusHours}h = <strong>{totalHours}h</strong></span>
        </div>
        <div className="flex justify-between text-indigo-500">
          <span>Stability buffer (20%)</span>
          <span>−{bufferHours}h reserved</span>
        </div>
        <div className="flex justify-between font-semibold border-t border-indigo-200 pt-1">
          <span>Plannable capacity</span>
          <span>{plannedHours}h</span>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">
          {sprint ? 'Edit Sprint' : 'Create New Sprint'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sprint Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Sprint 1"
            />
          </div>

          {/* Goal */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sprint Goal *</label>
            <textarea
              required
              value={formData.goal}
              onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="What do you want to achieve in this sprint?"
            />
          </div>

          {/* Duration — only on creation */}
          {!sprint && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Duration *</label>
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
                    <label className="block text-sm font-medium text-gray-700 mb-2">Start Date *</label>
                    <input
                      type="date"
                      required
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">End Date *</label>
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
              <p className="text-sm text-yellow-800">Sprint duration cannot be changed after creation.</p>
            </div>
          )}

          {/* NEW: Assignee count */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Developers Assigned *
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Min 2 · Max {maxAssignees} (space limit from "{space?.name}")
            </p>
            <div className="flex items-center gap-3">
              {/* Decrement */}
              <button
                type="button"
                onClick={() => handleAssigneeChange(Math.max(2, formData.assignee_count - 1))}
                disabled={formData.assignee_count <= 2}
                className="w-9 h-9 flex items-center justify-center rounded-lg border border-gray-300 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 font-bold text-lg"
              >
                −
              </button>

              <input
                type="number"
                required
                min={2}
                max={maxAssignees}
                value={formData.assignee_count}
                onChange={(e) => handleAssigneeChange(e.target.value)}
                className={`w-20 text-center px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-lg font-semibold ${
                  assigneeError ? 'border-red-400 bg-red-50' : 'border-gray-300'
                }`}
              />

              {/* Increment */}
              <button
                type="button"
                onClick={() => handleAssigneeChange(Math.min(maxAssignees, formData.assignee_count + 1))}
                disabled={formData.assignee_count >= maxAssignees}
                className="w-9 h-9 flex items-center justify-center rounded-lg border border-gray-300 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 font-bold text-lg"
              >
                +
              </button>

              <span className="text-sm text-gray-500">developers</span>
            </div>

            {assigneeError && (
              <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
                <svg className="w-3 h-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {assigneeError}
              </p>
            )}

            {/* Live capacity preview */}
            {!assigneeError && capacityPreview()}
          </div>

          {/* Actions */}
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
              disabled={loading || !!assigneeError}
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