import { useState } from 'react';
import SpaceManagement from './SpaceManagement';
import Dashboard from './Dashboard';

export default function AgileManagement() {
  const [selectedSpace, setSelectedSpace] = useState(null);

  return (
    <div className="min-h-screen">
      {!selectedSpace ? (
        <SpaceManagement onSelectSpace={setSelectedSpace} />
      ) : (
        <Dashboard 
          space={selectedSpace} 
          onBack={() => setSelectedSpace(null)} 
        />
      )}
    </div>
  );
}
