import React, { useState } from "react";
import Sidebar from "./components/common/SideBar";
import Header from "./components/common/Header";
import HomePage from "./components/common/HomePage";
import ModulePage from "./components/common/ModulePage";
import { Home, Heart, Users, FileText, MessageSquare } from "lucide-react";

const App = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeModule, setActiveModule] = useState("home");

  const modules = {
    home: { id: "home", name: "Home", icon: Home },
    "emotion-monitoring": { id: "emotion-monitoring", name: "Emotion Monitoring", icon: Heart },
    "expertise-recommendation": { id: "expertise-recommendation", name: "Expertise Recommendation", icon: Users },
    "requirement-tracker": { id: "requirement-tracker", name: "Requirement & Sprint Tracker", icon: FileText },
    "inclusive-communication": { id: "inclusive-communication", name: "Inclusive Communication", icon: MessageSquare },
  };

  const currentModule = modules[activeModule];

  return (
    <div className="flex h-screen bg-gray-50">
      {sidebarOpen && (
        <Sidebar activeModule={activeModule} setActiveModule={setActiveModule} />
      )}

      <div className="flex-1 flex flex-col">
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <main className="flex-1 overflow-y-auto">
          {activeModule === "home" ? (
            <HomePage setActiveModule={setActiveModule} />
          ) : (
            <ModulePage module={currentModule} />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
