
import { useState, useEffect } from 'react';
import api from './api';

export default function KanbanBoard({ sprint, onClose, onUpdate }) {
  const [items, setItems] = useState([]);
  const [draggedItem, setDraggedItem] = useState(null);

  const columns = [
    { id: 'To Do', title: 'To Do', color: 'bg-gray-100' },
    { id: 'In Progress', title: 'In Progress', color: 'bg-blue-100' },
    { id: 'In Review', title: 'In Review', color: 'bg-purple-100' },
    { id: 'Done', title: 'Done', color: 'bg-green-100' },
  ];

  useEffect(() => {
    loadItems();
  }, [sprint.id]);

  const loadItems = async () => {
    try {
      const data = await api.getBacklogItemsBySprint(sprint.id);
      setItems(data);
    } catch (error) {
      alert('Failed to load items: ' + error.message);
    }
  };

  const handleDragStart = (e, item) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e, newStatus) => {
    e.preventDefault();
    
    if (!draggedItem || draggedItem.status === newStatus) {
      setDraggedItem(null);
      return;
    }

    try {
      await api.updateItemStatus(draggedItem.id, newStatus);
      await loadItems();
      await onUpdate();
      setDraggedItem(null);
    } catch (error) {
      alert('Failed to update status: ' + error.message);
      setDraggedItem(null);
    }
  };

  const getItemsByStatus = (status) => {
    return items.filter(item => item.status === status);
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'Low': 'border-green-400',
      'Medium': 'border-yellow-400',
      'High': 'border-orange-400',
      'Critical': 'border-red-400',
    };
    return colors[priority] || 'border-gray-400';
  };

  const getTypeIcon = (type) => {
    const icons = {
      'Task': '📋',
      'Subtask': '📝',
      'Bug': '🐛',
      'Story': '📖',
    };
    return icons[type] || '📋';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-800">{sprint.name} - Board</h2>
              <p className="text-gray-600">{sprint.goal}</p>
            </div>
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

        {/* Kanban Board */}
        <div className="flex-1 overflow-x-auto p-6">
          <div className="grid grid-cols-4 gap-4 h-full min-w-max">
            {columns.map((column) => (
              <div
                key={column.id}
                className="flex flex-col min-w-[280px]"
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, column.id)}
              >
                <div className={`${column.color} rounded-lg px-4 py-3 mb-3`}>
                  <h3 className="font-bold text-gray-800 flex items-center justify-between">
                    <span>{column.title}</span>
                    <span className="bg-white px-2 py-1 rounded text-sm">
                      {getItemsByStatus(column.id).length}
                    </span>
                  </h3>
                </div>

                <div className="flex-1 space-y-3 overflow-y-auto pr-2">
                  {getItemsByStatus(column.id).map((item) => (
                    <div
                      key={item.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, item)}
                      className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-all cursor-move border-l-4 ${getPriorityColor(item.priority)} p-4`}
                    >
                      <div className="flex items-start gap-2 mb-2">
                        <span className="text-lg">{getTypeIcon(item.type)}</span>
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-800 mb-1">{item.title}</h4>
                          <p className="text-sm text-gray-600 line-clamp-2">{item.description}</p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                        <div className="flex gap-2">
                          <span className="px-2 py-1 rounded bg-gray-100 text-gray-700 text-xs font-medium">
                            {item.type}
                          </span>
                          <span className="px-2 py-1 rounded bg-indigo-100 text-indigo-700 text-xs font-medium">
                            {item.story_points} pts
                          </span>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          item.priority === 'Critical' ? 'bg-red-100 text-red-700' :
                          item.priority === 'High' ? 'bg-orange-100 text-orange-700' :
                          item.priority === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-green-100 text-green-700'
                        }`}>
                          {item.priority}
                        </span>
                      </div>
                    </div>
                  ))}

                  {getItemsByStatus(column.id).length === 0 && (
                    <div className="text-center text-gray-400 py-8">
                      <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                      </svg>
                      <p className="text-sm">No items</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex gap-4">
              <span>Total Items: {items.length}</span>
              <span>•</span>
              <span>Done: {getItemsByStatus('Done').length}</span>
              <span>•</span>
              <span>In Progress: {getItemsByStatus('In Progress').length + getItemsByStatus('In Review').length}</span>
            </div>
            <div className="text-gray-500">
              Drag and drop items to change their status
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}