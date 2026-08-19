const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const message = data?.detail || data?.message || `Request failed (${response.status})`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }

  return data
}

export function getHealth() {
  return request('/health')
}

export function getPrediction(payload) {
  return request('/api/prediction', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function getModelMetrics() {
  return request('/api/model/metrics')
}

export function getFeatureImportance() {
  return request('/api/model/feature-importance')
}

/** @deprecated Use getModelMetrics instead */
export function getComparison() {
  return getModelMetrics()
}

export function getModels() {
  return request('/api/models')
}

export default {
  getHealth,
  getPrediction,
  getModelMetrics,
  getFeatureImportance,
  getComparison,
  getModels
}
