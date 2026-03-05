
import { useState, useEffect } from 'react';
import api from './api';
import { ChevronLeft } from 'lucide-react';

export default function KanbanBoard({ sprint, onClose, onUpdate }) {
  const [items, setItems] = useState([]);
  const [draggedItem, setDraggedItem] = useState(null);
  const [openDropdown, setOpenDropdown] = useState(null);

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

    await updateItemStatus(draggedItem.id, newStatus);
    setDraggedItem(null);
  };

  const updateItemStatus = async (itemId, newStatus) => {
    try {
      await api.updateItemStatus(itemId, newStatus);
      await loadItems();
      await onUpdate();
      setOpenDropdown(null);
    } catch (error) {
      alert('Failed to update status: ' + error.message);
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
    <div className="h-full bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Back to Dashboard"
              >
                <ChevronLeft className="w-6 h-6 text-gray-600" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-800">{sprint.name}</h1>
                <p className="text-gray-600 text-sm mt-1">{sprint.goal}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="flex-1 p-6 bg-gray-50 overflow-hidden">
        <div className="grid grid-cols-4 gap-4 h-full">
            {columns.map((column) => (
              <div
                key={column.id}
                className="flex flex-col min-h-0"
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

                <div className="flex-1 space-y-3 overflow-y-auto pr-2 min-h-0">
                  {getItemsByStatus(column.id).map((item) => (
                    <div
                      key={item.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, item)}
                      className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-all border-l-4 ${getPriorityColor(item.priority)} p-4 group relative`}
                    >
                      <div className="flex items-start gap-2 mb-2">
                        <span className="text-lg">{getTypeIcon(item.type)}</span>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-800 mb-1 break-words">{item.title}</h4>
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
                        <div className="relative">
                          <button
                            onClick={() => setOpenDropdown(openDropdown === item.id ? null : item.id)}
                            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                              item.priority === 'Critical' ? 'bg-red-100 text-red-700 hover:bg-red-200' :
                              item.priority === 'High' ? 'bg-orange-100 text-orange-700 hover:bg-orange-200' :
                              item.priority === 'Medium' ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' :
                              'bg-green-100 text-green-700 hover:bg-green-200'
                            }`}>
                            {item.priority}
                          </button>
                        </div>
                      </div>

                      {/* Status Dropdown */}
                      {openDropdown === item.id && (
                        <div className="absolute top-full right-0 mt-2 bg-white rounded-lg shadow-lg border border-gray-200 z-20 min-w-[150px]">
                          {columns.map((col) => (
                            <button
                              key={col.id}
                              onClick={() => updateItemStatus(item.id, col.id)}
                              className={`w-full text-left px-4 py-2 text-sm transition-colors first:rounded-t-lg last:rounded-b-lg ${
                                item.status === col.id
                                  ? 'bg-indigo-100 text-indigo-700 font-medium'
                                  : 'text-gray-700 hover:bg-gray-100'
                              }`}
                            >
                              {col.title}
                              {item.status === col.id && <span className="ml-2">✓</span>}
                            </button>
                          ))}
                        </div>
                      )}
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
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex gap-6">
            <span className="font-medium"><strong>{items.length}</strong> Total Items</span>
            <span className="text-gray-300">•</span>
            <span className="font-medium"><strong>{getItemsByStatus('Done').length}</strong> Done</span>
            <span className="text-gray-300">•</span>
            <span className="font-medium"><strong>{getItemsByStatus('In Progress').length + getItemsByStatus('In Review').length}</strong> In Progress</span>
          </div>
          <div className="text-gray-500 text-xs">
            💡 Drag cards or click priority badge to change status
          </div>
        </div>
      </div>
    </div>
  );
}
