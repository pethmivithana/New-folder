import { useState, useEffect } from 'react';
import api from './api';
import SprintModal from './SprintModal';
import BacklogModal from './BacklogModal';
import KanbanBoard from './KanbanBoard';
import FinishSprintModal from './FinishSprintModal';
import ImpactAnalyzer from './ImpactAnalyzer';
import AnalyticsDashboard from './AnalyticsDashboard';

export default function Dashboard({ space, onBack }) {
  const [sprints, setSprints] = useState([]);
  const [backlogItems, setBacklogItems] = useState([]);
  const [unassignedItems, setUnassignedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showSprintModal, setShowSprintModal] = useState(false);
  const [showBacklogModal, setShowBacklogModal] = useState(false);
  const [showFinishModal, setShowFinishModal] = useState(false);
  const [showKanban, setShowKanban] = useState(false);
  const [editingSprint, setEditingSprint] = useState(null);
  const [editingBacklog, setEditingBacklog] = useState(null);
  const [selectedSprint, setSelectedSprint] = useState(null);
  const [finishingSprint, setFinishingSprint] = useState(null);
  const [activeTab, setActiveTab] = useState('scrums');

  useEffect(() => {
    if (space?.id) {
      loadData();
    }
  }, [space?.id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sprintsData, backlogData, unassignedData] = await Promise.all([
        api.getSprintsBySpace(space.id),
        api.getBacklogItemsBySpace(space.id),
        api.getUnassignedBacklogItems(space.id),
      ]);
      setSprints(sprintsData || []);
      setBacklogItems(backlogData || []);
      setUnassignedItems(unassignedData || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSprint = async (id) => {
    if (!confirm('Delete this sprint?')) return;
    try {
      await api.deleteSprint(id);
      await loadData();
    } catch (error) {
      alert('Failed to delete sprint: ' + error.message);
    }
  };

  const handleStartSprint = async (id) => {
    try {
      await api.startSprint(id);
      await loadData();
    } catch (error) {
      alert('Failed to start sprint: ' + error.message);
    }
  };

  const handleFinishSprint = (sprint) => {
    setFinishingSprint(sprint);
    setShowFinishModal(true);
  };

  const handleDeleteBacklog = async (id) => {
    if (!confirm('Delete this item?')) return;
    try {
      await api.deleteBacklogItem(id);
      await loadData();
    } catch (error) {
      alert('Failed to delete: ' + error.message);
    }
  };

  const handleAssignToSprint = async (itemId, sprintId) => {
    if (!sprintId) return;
    try {
      await api.updateBacklogItem(itemId, { sprint_id: sprintId });
      await loadData();
    } catch (error) {
      alert('Failed to assign: ' + error.message);
    }
  };

  const handleOpenKanban = (sprint) => {
    setSelectedSprint(sprint);
    setShowKanban(true);
  };

  const getSprintItems = (sprintId) => backlogItems.filter(item => item.sprint_id === sprintId);

  const getStatusColor = (status) => {
    const colors = {
      'Planned': 'bg-gray-100 text-gray-700',
      'Active': 'bg-green-100 text-green-700',
      'Completed': 'bg-blue-100 text-blue-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'Low': 'bg-green-100 text-green-700',
      'Medium': 'bg-yellow-100 text-yellow-700',
      'High': 'bg-orange-100 text-orange-700',
      'Critical': 'bg-red-100 text-red-700',
    };
    return colors[priority] || 'bg-gray-100 text-gray-700';
  };

  const getTypeIcon = (type) => {
    const icons = { 'Task': '📋', 'Subtask': '📝', 'Bug': '🐛', 'Story': '📖' };
    return icons[type] || '📋';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={onBack} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">{space.name}</h1>
                <p className="text-sm text-gray-600">{space.description}</p>
              </div>
            </div>

            {activeTab === 'scrums' && (
              <div className="flex gap-3">
                <button
                  onClick={() => { setEditingSprint(null); setShowSprintModal(true); }}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors font-medium flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Create Sprint
                </button>
                <button
                  onClick={() => { setEditingBacklog(null); setShowBacklogModal(true); }}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add Item
                </button>
              </div>
            )}
          </div>

          <div className="flex gap-6 mt-4 border-b border-gray-200">
            {['scrums', 'impact-analyzer', 'analytics', 'settings'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-3 px-1 border-b-2 transition-colors font-medium capitalize ${
                  activeTab === tab ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-600 hover:text-gray-800'
                }`}
              >
                {tab === 'scrums' ? 'Scrums' : tab === 'impact-analyzer' ? 'Impact Analyzer' : tab === 'analytics' ? 'Analytics' : 'Settings'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        )}

        {!loading && activeTab === 'scrums' && (
          <div className="space-y-8">
            <div>
              <h2 className="text-xl font-bold text-gray-800 mb-4">Sprints ({sprints.length})</h2>
              {sprints.length === 0 ? (
                <div className="bg-white rounded-xl shadow-sm p-8 text-center border-2 border-dashed border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">No Sprints Yet</h3>
                  <button onClick={() => setShowSprintModal(true)} className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700">
                    Create Sprint
                  </button>
                </div>
              ) : (
                <div className="grid gap-4">
                  {sprints.map((sprint) => {
                    const sprintItems = getSprintItems(sprint.id);
                    const doneItems = sprintItems.filter(i => i.status === 'Done').length;
                    const progress = sprintItems.length > 0 ? Math.round((doneItems / sprintItems.length) * 100) : 0;
                    return (
                      <div key={sprint.id} className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="text-lg font-bold text-gray-800">{sprint.name}</h3>
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(sprint.status)}`}>
                                {sprint.status}
                              </span>
                            </div>
                            {sprint.goal && <p className="text-gray-600 mb-3">{sprint.goal}</p>}
                            
                            <div className="grid grid-cols-4 gap-3 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100 mb-3">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-indigo-600">{sprintItems.length}</div>
                                <div className="text-xs text-gray-600">Items</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-green-600">{sprintItems.reduce((s, i) => s + (i.story_points || 0), 0)}</div>
                                <div className="text-xs text-gray-600">Points</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{progress}%</div>
                                <div className="text-xs text-gray-600">Done</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-orange-600">
                                  {sprint.start_date && sprint.end_date ? Math.max(0, Math.ceil((new Date(sprint.end_date) - new Date()) / 86400000)) : 'N/A'}
                                </div>
                                <div className="text-xs text-gray-600">Days</div>
                              </div>
                            </div>

                            {sprintItems.length > 0 && (
                              <div className="mt-3">
                                <div className="flex justify-between text-xs text-gray-500 mb-1">
                                  <span>{doneItems}/{sprintItems.length} done</span>
                                  <span>{progress}%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div className="bg-green-500 h-2 rounded-full" style={{ width: `${progress}%` }} />
                                </div>
                              </div>
                            )}
                          </div>

                          <div className="flex gap-2 ml-4">
                            {sprint.status === 'Planned' && (
                              <button onClick={() => handleStartSprint(sprint.id)} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium">
                                Start
                              </button>
                            )}
                            {sprint.status === 'Active' && (
                              <>
                                <button onClick={() => handleOpenKanban(sprint)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium">
                                  Board
                                </button>
                                <button onClick={() => handleFinishSprint(sprint)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
                                  Finish
                                </button>
                              </>
                            )}
                            {sprint.status === 'Completed' && (
                              <button onClick={() => handleOpenKanban(sprint)} className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
                                View
                              </button>
                            )}
                            <button onClick={() => { setEditingSprint(sprint); setShowSprintModal(true); }} className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                              <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                            <button onClick={() => handleDeleteSprint(sprint.id)} className="p-2 border border-red-300 rounded-lg hover:bg-red-50">
                              <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div>
              <h2 className="text-xl font-bold text-gray-800 mb-4">Backlog ({unassignedItems.length})</h2>
              {unassignedItems.length === 0 ? (
                <div className="bg-white rounded-xl shadow-sm p-8 text-center border-2 border-dashed border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Backlog Empty</h3>
                  <button onClick={() => setShowBacklogModal(true)} className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700">
                    Add Item
                  </button>
                </div>
              ) : (
                <div className="grid gap-3">
                  {unassignedItems.map((item) => (
                    <div key={item.id} className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span>{getTypeIcon(item.type)}</span>
                            <h4 className="font-semibold text-gray-800">{item.title}</h4>
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(item.priority)}`}>{item.priority}</span>
                            <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-700 text-xs font-medium">{item.story_points} SP</span>
                          </div>
                          {item.description && <p className="text-sm text-gray-600 mb-2">{item.description}</p>}
                          <select onChange={(e) => handleAssignToSprint(item.id, e.target.value)} defaultValue="" className="text-sm border border-gray-300 rounded-lg px-3 py-1.5">
                            <option value="">Assign to Sprint...</option>
                            {sprints.filter(s => s.status !== 'Completed').map(sprint => (
                              <option key={sprint.id} value={sprint.id}>{sprint.name}</option>
                            ))}
                          </select>
                        </div>
                        <div className="flex gap-2 ml-3">
                          <button onClick={() => { setEditingBacklog(item); setShowBacklogModal(true); }} className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button onClick={() => handleDeleteBacklog(item.id)} className="p-2 border border-red-300 rounded-lg hover:bg-red-50">
                            <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {!loading && activeTab === 'impact-analyzer' && <ImpactAnalyzer sprints={sprints} />}
        {!loading && activeTab === 'analytics' && <AnalyticsDashboard space={space} />}
        {!loading && activeTab === 'settings' && (
          <div className="bg-white rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Settings</h2>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Sprint Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Default Sprint Duration</label>
                    <select defaultValue="2 Weeks" className="w-full max-w-xs border border-gray-300 rounded-lg px-4 py-2">
                      <option>1 Week</option>
                      <option>2 Weeks</option>
                      <option>3 Weeks</option>
                      <option>4 Weeks</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Working Hours/Day</label>
                    <input type="number" min="1" max="24" defaultValue="6" className="w-full max-w-xs border border-gray-300 rounded-lg px-4 py-2" />
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Impact Analysis</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">Enable ML Predictions</span>
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">Auto-analyze on Add</span>
                    <input type="checkbox" className="w-4 h-4" />
                  </div>
                </div>
              </div>
              <button className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700">Save Settings</button>
            </div>
          </div>
        )}
      </div>

      {showSprintModal && (
        <SprintModal space={space} sprint={editingSprint} onClose={() => { setShowSprintModal(false); setEditingSprint(null); }} onSave={loadData} />
      )}
      {showBacklogModal && (
        <BacklogModal space={space} sprints={sprints.filter(s => s.status !== 'Completed')} item={editingBacklog} onClose={() => { setShowBacklogModal(false); setEditingBacklog(null); }} onSave={loadData} />
      )}
      {showFinishModal && finishingSprint && (
        <FinishSprintModal sprint={finishingSprint} sprints={sprints.filter(s => s.status === 'Planned' && s.id !== finishingSprint.id)} onClose={() => { setShowFinishModal(false); setFinishingSprint(null); }} onFinish={loadData} />
      )}
      {showKanban && selectedSprint && (
        <KanbanBoard sprint={selectedSprint} onClose={() => setShowKanban(false)} onUpdate={loadData} />
      )}
    </div>
  );
}