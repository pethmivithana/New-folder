import React, { useState, useEffect } from 'react';
import api from '../api';
import Dashboard from '../Dashboard';

export default function RequirementTrackerHomePage({ module }) {
  const [spaces, setSpaces] = useState([]);
  const [selectedSpace, setSelectedSpace] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSpaces();
  }, []);

  const loadSpaces = async () => {
    setLoading(true);
    try {
      const data = await api.getSpaces();
      setSpaces(data || []);
    } catch (error) {
      console.error('Failed to load spaces:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSpace = async (name, description, maxAssignees) => {
    try {
      await api.createSpace({
        name,
        description,
        max_assignees: maxAssignees,
      });
      await loadSpaces();
    } catch (error) {
      alert('Failed to create space: ' + error.message);
    }
  };

  if (selectedSpace) {
    return (
      <Dashboard 
        space={selectedSpace} 
        onBack={() => setSelectedSpace(null)} 
      />
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Requirement Tracker</h1>
      
      {loading ? (
        <div className="text-center py-12">Loading spaces...</div>
      ) : (
        <>
          <button
            onClick={() => {
              const name = prompt('Space name:');
              if (name) {
                const description = prompt('Description:');
                const maxAssignees = parseInt(prompt('Max assignees:', '5'));
                handleCreateSpace(name, description, maxAssignees);
              }
            }}
            className="mb-6 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Create Space
          </button>

          {spaces.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No spaces yet. Create one to get started.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {spaces.map((space) => (
                <div
                  key={space.id}
                  onClick={() => setSelectedSpace(space)}
                  className="p-4 border border-gray-200 rounded-lg hover:shadow-lg cursor-pointer transition-shadow"
                >
                  <h2 className="text-xl font-semibold mb-2">{space.name}</h2>
                  <p className="text-gray-600 mb-2">{space.description}</p>
                  <p className="text-sm text-gray-500">
                    Max assignees: {space.max_assignees}
                  </p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
