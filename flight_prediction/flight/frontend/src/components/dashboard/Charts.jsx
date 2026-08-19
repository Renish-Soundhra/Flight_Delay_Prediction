import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const tooltipStyle = {
  background: '#121a2c',
  border: '1px solid #232f49',
  color: '#edf1f9',
}

export function EmptyChart({ label }) {
  return <div className="empty-block">{label}</div>
}

export function TrendChart({ data, loading }) {
  if (loading) return <EmptyChart label="Loading delay trend" />
  const points = data?.points || []
  if (!points.length) return <EmptyChart label="No trend points in this window." />
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={points}>
        <CartesianGrid stroke="#232f49" strokeDasharray="3 3" />
        <XAxis dataKey="bucket" stroke="#8f9cb8" hide={points.length > 40} />
        <YAxis stroke="#8f9cb8" tickFormatter={(value) => `${Math.round(value * 100)}%`} />
        <Tooltip contentStyle={tooltipStyle} formatter={(value) => `${(value * 100).toFixed(1)}%`} />
        <Legend />
        <Line type="monotone" dataKey="actual_delay_rate" name="Actual delay rate" stroke="#f5b301" dot={false} />
        <Line type="monotone" dataKey="predicted_delay_rate" name="Predicted delay rate" stroke="#5b8dff" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function AirportRankChart({ rows, loading }) {
  if (loading) return <EmptyChart label="Loading airports" />
  const data = (rows || []).slice(0, 12).map((row) => ({
    name: row.airport,
    delay_rate: Number(row.delay_rate || 0),
  }))
  if (!data.length) return <EmptyChart label="No airport rows." />
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 16 }}>
        <CartesianGrid stroke="#232f49" />
        <XAxis type="number" stroke="#8f9cb8" tickFormatter={(value) => `${Math.round(value * 100)}%`} />
        <YAxis type="category" dataKey="name" stroke="#8f9cb8" width={50} />
        <Tooltip contentStyle={tooltipStyle} formatter={(value) => `${(value * 100).toFixed(1)}%`} />
        <Bar dataKey="delay_rate" name="Actual delay rate" fill="#f5b301" />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function AirlineCharts({ rows, loading }) {
  if (loading) return <EmptyChart label="Loading airlines" />
  const data = (rows || []).map((row) => ({
    name: row.airline,
    delay_rate: Number(row.delay_rate || 0),
    flights: row.total_flights,
  }))
  if (!data.length) return <EmptyChart label="No airline rows." />
  return (
    <div className="charts-grid">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data}>
          <CartesianGrid stroke="#232f49" />
          <XAxis dataKey="name" stroke="#8f9cb8" />
          <YAxis stroke="#8f9cb8" tickFormatter={(value) => `${Math.round(value * 100)}%`} />
          <Tooltip contentStyle={tooltipStyle} formatter={(value) => `${(value * 100).toFixed(1)}%`} />
          <Bar dataKey="delay_rate" name="Delay rate" fill="#ff5c4d" />
        </BarChart>
      </ResponsiveContainer>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data}>
          <CartesianGrid stroke="#232f49" />
          <XAxis dataKey="name" stroke="#8f9cb8" />
          <YAxis stroke="#8f9cb8" />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="flights" name="Flight volume" fill="#5b8dff" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function BucketChart({ buckets, loading, labelKey = 'label', valueKey = 'count', title }) {
  if (loading) return <EmptyChart label={`Loading ${title}`} />
  const data = buckets || []
  if (!data.length) return <EmptyChart label={`No ${title} data.`} />
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <CartesianGrid stroke="#232f49" />
        <XAxis dataKey={labelKey} stroke="#8f9cb8" interval={0} angle={-20} height={60} textAnchor="end" />
        <YAxis stroke="#8f9cb8" />
        <Tooltip contentStyle={tooltipStyle} />
        <Bar dataKey={valueKey} name={title}>
          {data.map((entry, index) => (
            <Cell key={index} fill={index >= data.length / 2 ? '#ff5c4d' : '#5b8dff'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function CurveChart({ points, xKey = 'x', yKey = 'y', color, xName, yName }) {
  if (!points?.length) return <EmptyChart label="Curve not available from saved evaluation sample." />
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={points}>
        <CartesianGrid stroke="#232f49" />
        <XAxis dataKey={xKey} stroke="#8f9cb8" type="number" domain={[0, 1]} />
        <YAxis dataKey={yKey} stroke="#8f9cb8" type="number" domain={[0, 1]} />
        <Tooltip contentStyle={tooltipStyle} />
        <Line type="monotone" dataKey={yKey} name={`${yName} vs ${xName}`} stroke={color} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
