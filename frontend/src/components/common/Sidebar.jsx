import React from 'react';
import {
  Home,
  Heart,
  Users,
  FileText,
  MessageSquare,
  Settings
} from 'lucide-react';

const Sidebar = ({ activeModule, setActiveModule }) => {
  const modules = [
    {
      id: 'home',
      name: 'Home',
      icon: Home,
    },
    {
      id: 'emotion-monitoring',
      name: 'Emotion Monitoring',
      icon: Heart,
      developer: 'Fonseka A.A.T.N.',
    },
    {
      id: 'expertise-recommendation',
      name: 'Expertise Recommendation',
      icon: Users,
      developer: 'Amarasinghe C.N.',
    },
    {
      id: 'requirement-tracker',
      name: 'Requirement & Sprint Tracker',
      icon: FileText,
      developer: 'Vithana P.I',
    },
    {
      id: 'inclusive-communication',
      name: 'Inclusive Communication',
      icon: MessageSquare,
      developer: 'M.B.H. De Silva',
    },
  ];

  return (
    <aside className="w-80 h-screen bg-white border-r border-gray-200 flex flex-col">
      
      {/* Logo / Header */}
      <div className="p-6 border-b">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 text-white flex items-center justify-center rounded-lg font-bold">
            AS
          </div>
          <div>
            <h1 className="text-lg font-semibold">AgileSense-AI</h1>
            <p className="text-xs text-gray-500">Emotion-Aware System</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {modules.map((module) => {
          const Icon = module.icon;
          const isActive = activeModule === module.id;

          return (
            <button
              key={module.id}
              onClick={() => setActiveModule(module.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Icon size={18} />
              <span className="text-sm font-medium">{module.name}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer / Settings */}
      <div className="p-4 border-t">
        <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-all whitespace-nowrap">
          <Settings size={18} />
          <span className="text-sm font-medium">Settings</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
