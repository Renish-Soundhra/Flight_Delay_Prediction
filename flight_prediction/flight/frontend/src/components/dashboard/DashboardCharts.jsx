import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  LineChart, Line
} from 'recharts';
import { useDashboardContext } from './DashboardContext';
import { 
  getDashboardTrends, 
  getDashboardAirports, 
  getDashboardAirlines, 
  getDelayDistribution,
  getProbabilityDistribution
} from '../../services/dashboardApi';

export default function DashboardCharts() {
  const { apiParams } = useDashboardContext();
  
  const [trends, setTrends] = useState([]);
  const [airports, setAirports] = useState([]);
  const [airlines, setAirlines] = useState([]);
  const [delayDist, setDelayDist] = useState([]);
  const [probDist, setProbDist] = useState([]);

  useEffect(() => {
    // Fetch all chart data concurrently
    Promise.all([
      getDashboardTrends({ ...apiParams, aggregation: 'daily' }),
      getDashboardAirports(apiParams),
      getDashboardAirlines(apiParams),
      getDelayDistribution(apiParams),
      getProbabilityDistribution(apiParams)
    ]).then(([trendsRes, airportsRes, airlinesRes, delayDistRes, probDistRes]) => {
      setTrends(trendsRes.points || []);
      setAirports(airportsRes.slice(0, 10)); // Top 10 airports
      setAirlines(airlinesRes);
      setDelayDist(delayDistRes.buckets || []);
      setProbDist(probDistRes.buckets || []);
    }).catch(console.error);
  }, [apiParams]);

  return (
    <div className="dashboard-charts-grid">
      
      {/* Delay Trend */}
      <div className="chart-card card">
        <h3>Delay Trend (Daily)</h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <LineChart data={trends} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="bucket" />
              <YAxis yAxisId="left" tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} />
              <YAxis yAxisId="right" orientation="right" />
              <RechartsTooltip formatter={(value, name) => [name.includes('rate') ? `${(value * 100).toFixed(1)}%` : value, name]} />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="actual_delay_rate" name="Actual Delay Rate" stroke="#f59e0b" activeDot={{ r: 8 }} />
              <Line yAxisId="left" type="monotone" dataKey="predicted_delay_rate" name="Predicted Delay Rate" stroke="#3b82f6" />
              <Line yAxisId="right" type="monotone" dataKey="total_flights" name="Total Flights" stroke="#6b7280" strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Airport Analytics */}
      <div className="chart-card card">
        <h3>Top 10 Airports by Delay Rate</h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={airports} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="airport" />
              <YAxis tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} />
              <RechartsTooltip formatter={(value, name) => [name === 'delay_rate' ? `${(value * 100).toFixed(1)}%` : value, name]} />
              <Legend />
              <Bar dataKey="delay_rate" name="Delay Rate" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Airline Analytics */}
      <div className="chart-card card">
        <h3>Airlines by Delay Rate</h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={airlines} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="airline" />
              <YAxis tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} />
              <RechartsTooltip formatter={(value, name) => [name === 'delay_rate' ? `${(value * 100).toFixed(1)}%` : value, name]} />
              <Legend />
              <Bar dataKey="delay_rate" name="Delay Rate" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Delay Distribution */}
      <div className="chart-card card">
        <h3>Departure Delay Distribution</h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={delayDist} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="label" />
              <YAxis />
              <RechartsTooltip />
              <Bar dataKey="count" name="Flight Count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Prediction Probability Distribution */}
      <div className="chart-card card">
        <h3>Model Probability Distribution</h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={probDist} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="label" />
              <YAxis />
              <RechartsTooltip />
              <Bar dataKey="count" name="Flight Count" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
}
