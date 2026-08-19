import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { getDashboardTimeline } from '../../services/dashboardApi';

const DashboardContext = createContext();

export const useDashboardContext = () => useContext(DashboardContext);

export const DashboardProvider = ({ children }) => {
  const [filters, setFilters] = useState({
    date_from: null,
    date_to: null,
    airline: '',
    origin: '',
    destination: '',
    flight_number: '',
    tail_number: '',
    risk: '',
    prediction: '',
  });

  const [simulationMode, setSimulationMode] = useState(false);
  const [simulationTime, setSimulationTime] = useState(null);
  const [simulationSpeed, setSimulationSpeed] = useState(1); // 1x, 5x, 10x, 50x
  const [isPlaying, setIsPlaying] = useState(false);
  
  const [timelineBounds, setTimelineBounds] = useState({ min_ts: null, max_ts: null });
  const [timelineLoading, setTimelineLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState(null);

  useEffect(() => {
    setTimelineLoading(true);
    setDashboardError(null);
    getDashboardTimeline()
      .then((data) => {
        setTimelineBounds({
          min_ts: data.min_ts,
          max_ts: data.max_ts,
        });
        setSimulationTime(data.min_ts);
      })
      .catch((err) => {
        console.error("Dashboard Timeline Error:", err);
        setDashboardError(err.message || 'Failed to load dashboard data');
      })
      .finally(() => setTimelineLoading(false));
  }, []);

  const updateFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      date_from: null,
      date_to: null,
      airline: '',
      origin: '',
      destination: '',
      flight_number: '',
      tail_number: '',
      risk: '',
      prediction: '',
    });
  }, []);

  // Simulation loop
  useEffect(() => {
    let intervalId;
    if (isPlaying && simulationMode && simulationTime) {
      intervalId = setInterval(() => {
        setSimulationTime((prevTime) => {
          if (!prevTime || !timelineBounds.max_ts) return prevTime;
          
          const currentTimestamp = new Date(prevTime).getTime();
          const maxTimestamp = new Date(timelineBounds.max_ts).getTime();
          
          // Increment based on speed. Let's say 1x is 1 minute per 1 second of real time.
          // 1 minute = 60000 ms
          const increment = 60000 * simulationSpeed;
          const nextTimestamp = currentTimestamp + increment;
          
          if (nextTimestamp >= maxTimestamp) {
            setIsPlaying(false);
            return timelineBounds.max_ts;
          }
          
          return new Date(nextTimestamp).toISOString().replace('T', ' ').substring(0, 19); // SQLite format YYYY-MM-DD HH:MM:SS
        });
      }, 1000);
    }
    
    return () => clearInterval(intervalId);
  }, [isPlaying, simulationMode, simulationSpeed, simulationTime, timelineBounds.max_ts]);

  const togglePlay = () => setIsPlaying(!isPlaying);
  const resetSimulation = () => {
    setIsPlaying(false);
    setSimulationTime(timelineBounds.min_ts);
  };

  const contextValue = useMemo(() => ({
    filters,
    updateFilter,
    resetFilters,
    simulationMode,
    setSimulationMode,
    simulationTime,
    setSimulationTime,
    simulationSpeed,
    setSimulationSpeed,
    isPlaying,
    togglePlay,
    resetSimulation,
    timelineBounds,
    timelineLoading,
    dashboardError,
    // The query params to pass to API calls
    apiParams: {
      ...filters,
      as_of: simulationMode ? simulationTime : undefined,
    }
  }), [
    filters, updateFilter, resetFilters, 
    simulationMode, simulationTime, simulationSpeed, 
    isPlaying, timelineBounds, timelineLoading, dashboardError
  ]);

  return (
    <DashboardContext.Provider value={contextValue}>
      {children}
    </DashboardContext.Provider>
  );
};
