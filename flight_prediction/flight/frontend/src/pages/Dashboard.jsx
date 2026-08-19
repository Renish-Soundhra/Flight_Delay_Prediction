import React, { useState } from 'react';
import '../components/dashboard/dashboard.css';
import { DashboardProvider } from '../components/dashboard/DashboardContext';
import DashboardFilters from '../components/dashboard/DashboardFilters';
import KPICards from '../components/dashboard/KPICards';
import FlightMap from '../components/dashboard/FlightMap';
import HighRiskTable from '../components/dashboard/HighRiskTable';
import DashboardCharts from '../components/dashboard/DashboardCharts';
import FlightDetail from '../components/dashboard/FlightDetail';
import AircraftRotation from '../components/dashboard/AircraftRotation';

export default function Dashboard() {
  const [selectedFlightId, setSelectedFlightId] = useState(null);
  const [selectedTailNumber, setSelectedTailNumber] = useState(null);

  const handleFlightClick = (id) => {
    setSelectedFlightId(id);
  };

  const handleCloseDetail = () => {
    setSelectedFlightId(null);
  };

  const handleTailClick = (tail) => {
    setSelectedTailNumber(tail);
  };

  const handleCloseRotation = () => {
    setSelectedTailNumber(null);
  };

  return (
    <DashboardProvider>
      <div className="dashboard-page">
        <header className="dashboard-header">
          <h1>Flight Delay Intelligence</h1>
          <p>Real-time operations center and predictive visualization.</p>
        </header>

        <DashboardFilters />

        <div className="dashboard-main-content">
          <KPICards />
          
          <div className="dashboard-row map-table-row">
            <FlightMap onFlightClick={handleFlightClick} />
            <HighRiskTable onFlightClick={handleFlightClick} />
          </div>

          <DashboardCharts />
        </div>

        {/* Modals/Overlays */}
        <FlightDetail 
          flightId={selectedFlightId} 
          onClose={handleCloseDetail} 
        />
        
        <AircraftRotation 
          tailNumber={selectedTailNumber} 
          onClose={handleCloseRotation} 
        />

        {/* Floating action button to demo aircraft rotation (since table doesn't click tail natively in this quick demo) */}
        <div style={{ position: 'fixed', bottom: '20px', right: '20px' }}>
          <button onClick={() => {
            const t = prompt('Enter a Tail Number to view rotation (e.g., N123AA):');
            if (t) handleTailClick(t);
          }}>
            View Aircraft Rotation
          </button>
        </div>
      </div>
    </DashboardProvider>
  );
}
