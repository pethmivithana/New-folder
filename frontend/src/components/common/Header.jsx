import React from 'react';
import { Menu, X, Bell } from 'lucide-react';

const Header = ({ sidebarOpen, setSidebarOpen }) => {
  return (
    <header className="w-full h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      
      {/* Left section */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <span className="text-sm text-gray-600 font-medium">
          Project ID: 25-26J-525
        </span>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-4">
        <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <Bell size={20} />
        </button>
      </div>
    </header>
  );
};

export default Header;
