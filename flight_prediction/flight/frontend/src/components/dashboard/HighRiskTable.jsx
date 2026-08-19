import React, { useEffect, useState } from 'react';
import { useDashboardContext } from './DashboardContext';
import { getHighRiskFlights } from '../../services/dashboardApi';

export default function HighRiskTable({ onFlightClick }) {
  const { apiParams } = useDashboardContext();
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 10 });
  const [loading, setLoading] = useState(true);
  
  // Table-specific state
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState('probability');
  const [order, setOrder] = useState('desc');

  useEffect(() => {
    // Reset page on filter change
    setPage(1);
  }, [apiParams]);

  useEffect(() => {
    setLoading(true);
    getHighRiskFlights({
      ...apiParams,
      page,
      page_size: 10,
      sort,
      order
    })
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [apiParams, page, sort, order]);

  const handleSort = (column) => {
    if (sort === column) {
      setOrder(order === 'desc' ? 'asc' : 'desc');
    } else {
      setSort(column);
      setOrder('desc');
    }
  };

  const renderSortIcon = (column) => {
    if (sort !== column) return <span className="sort-icon">↕</span>;
    return <span className="sort-icon">{order === 'desc' ? '↓' : '↑'}</span>;
  };

  return (
    <div className="high-risk-table-container card" style={{ padding: '24px' }}>
      <h3>High Risk Flights ({data.total})</h3>
      <div className="table-responsive">
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('flight_number')}>Flight {renderSortIcon('flight_number')}</th>
              <th onClick={() => handleSort('airline')}>Airline {renderSortIcon('airline')}</th>
              <th onClick={() => handleSort('origin')}>Origin {renderSortIcon('origin')}</th>
              <th onClick={() => handleSort('destination')}>Dest {renderSortIcon('destination')}</th>
              <th onClick={() => handleSort('scheduled_ts')}>Departure {renderSortIcon('scheduled_ts')}</th>
              <th onClick={() => handleSort('probability')}>Prob {renderSortIcon('probability')}</th>
              <th>Risk</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="7" className="text-center">Loading...</td></tr>
            ) : data.items.length === 0 ? (
              <tr><td colSpan="7" className="text-center">No high risk flights found</td></tr>
            ) : (
              data.items.map((flight) => (
                <tr key={flight.id} onClick={() => onFlightClick(flight.id)} className="clickable-row">
                  <td>{flight.airline} {flight.flight_number}</td>
                  <td>{flight.airline_name || flight.airline}</td>
                  <td>{flight.origin}</td>
                  <td>{flight.destination}</td>
                  <td>{flight.scheduled_departure}</td>
                  <td>{(flight.probability * 100).toFixed(1)}%</td>
                  <td>
                    <span className={`risk-badge risk-${flight.risk?.toLowerCase()}`}>
                      {flight.risk}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      <div className="pagination">
        <button 
          disabled={page === 1} 
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Previous
        </button>
        <span>Page {page} of {Math.ceil(data.total / 10) || 1}</span>
        <button 
          disabled={page >= Math.ceil(data.total / 10)} 
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
