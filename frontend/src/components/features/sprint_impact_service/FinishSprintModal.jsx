import { useState, useEffect } from 'react';
import api from './api';

export default function FinishSprintModal({ sprint, sprints, onClose, onFinish }) {
  const [moveOption, setMoveOption] = useState('backlog');
  const [targetSprintId, setTargetSprintId] = useState('');
  const [incompleteItems, setIncompleteItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadIncompleteItems();
  }, [sprint.id]);

  const loadIncompleteItems = async () => {
    try {
      const items = await api.getBacklogItemsBySprint(sprint.id);
      const incomplete = items.filter(item => item.status !== 'Done');
      setIncompleteItems(incomplete);
    } catch (error) {
      console.error('Failed to load items:', error);
    }
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      const data = {
        sprint_id: sprint.id,
        move_incomplete_to: moveOption === 'sprint' ? targetSprintId : 'backlog',
      };

      await api.finishSprint(sprint.id, data);
      await onFinish();
      onClose();
    } catch (error) {
      alert('Failed to finish sprint: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Finish Sprint: {sprint.name}
        </h2>

        {incompleteItems.length > 0 ? (
          <div className="space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <h3 className="font-semibold text-yellow-800 mb-1">
                    {incompleteItems.length} Incomplete Item{incompleteItems.length !== 1 ? 's' : ''}
                  </h3>
                  <p className="text-sm text-yellow-700">
                    These items are not marked as "Done". Where would you like to move them?
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <label className="flex items-start gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="moveOption"
                  value="backlog"
                  checked={moveOption === 'backlog'}
                  onChange={(e) => setMoveOption(e.target.value)}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium text-gray-800">Move to Backlog</div>
                  <div className="text-sm text-gray-600">Items will return to the backlog</div>
                </div>
              </label>

              {sprints.length > 0 && (
                <label className="flex items-start gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="moveOption"
                    value="sprint"
                    checked={moveOption === 'sprint'}
                    onChange={(e) => setMoveOption(e.target.value)}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-800 mb-2">Move to Another Sprint</div>
                    {moveOption === 'sprint' && (
                      <select
                        value={targetSprintId}
                        onChange={(e) => setTargetSprintId(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                      >
                        <option value="">Select Sprint...</option>
                        {sprints.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </label>
              )}
            </div>

            <div className="bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Incomplete Items:</h4>
              <ul className="space-y-1">
                {incompleteItems.map((item) => (
                  <li key={item.id} className="text-sm text-gray-600 flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      item.status === 'To Do' ? 'bg-gray-200 text-gray-700' :
                      item.status === 'In Progress' ? 'bg-blue-200 text-blue-700' :
                      'bg-purple-200 text-purple-700'
                    }`}>
                      {item.status}
                    </span>
                    {item.title}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="font-semibold text-green-800">All Items Completed!</h3>
                <p className="text-sm text-green-700">Great job! All items are marked as "Done".</p>
              </div>
            </div>
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
            onClick={handleFinish}
            disabled={loading || (moveOption === 'sprint' && !targetSprintId)}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
          >
            {loading ? 'Finishing...' : 'Finish Sprint'}
          </button>
        </div>
      </div>
    </div>
  );
}
