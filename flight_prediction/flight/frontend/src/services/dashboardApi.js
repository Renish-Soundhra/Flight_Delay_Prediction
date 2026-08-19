const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`)
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const message = data?.detail || data?.message || `Request failed (${response.status})`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return data
}

export function toQuery(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  })
  const suffix = search.toString()
  return suffix ? `?${suffix}` : ''
}

export function getDashboardStatus() {
  return request('/api/dashboard/status')
}

export function getDashboardFilters() {
  return request('/api/dashboard/filters')
}

export function getDashboardSummary(params) {
  return request(`/api/dashboard/summary${toQuery(params)}`)
}

export function getDashboardTrends(params) {
  return request(`/api/dashboard/trends${toQuery(params)}`)
}

export function getDashboardAirports(params) {
  return request(`/api/dashboard/airports${toQuery(params)}`)
}

export function getDashboardAirlines(params) {
  return request(`/api/dashboard/airlines${toQuery(params)}`)
}

export function getDashboardRoutes(params) {
  return request(`/api/dashboard/routes${toQuery(params)}`)
}

export function getHighRiskFlights(params) {
  return request(`/api/dashboard/high-risk-flights${toQuery(params)}`)
}

export function getDashboardMap(params) {
  return request(`/api/dashboard/map${toQuery(params)}`)
}

export function getDashboardFlight(id) {
  return request(`/api/dashboard/flights/${id}`)
}

export function getAircraftRotation(tailNumber, params) {
  return request(`/api/dashboard/aircraft/${encodeURIComponent(tailNumber)}${toQuery(params)}`)
}

export function getDelayDistribution(params) {
  return request(`/api/dashboard/delay-distribution${toQuery(params)}`)
}

export function getProbabilityDistribution(params) {
  return request(`/api/dashboard/probability-distribution${toQuery(params)}`)
}

export function getDashboardTimeline() {
  return request('/api/dashboard/timeline')
}

export function getModelAnalytics() {
  return request('/api/dashboard/model-analytics')
}
