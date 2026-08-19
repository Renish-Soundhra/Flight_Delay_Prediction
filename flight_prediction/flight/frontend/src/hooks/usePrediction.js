import { useState, useCallback } from 'react'
import { getPrediction } from '../services/api.js'

export default function usePrediction() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const predict = useCallback(async (payload) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getPrediction(payload)
      setResult(data)
      return data
    } catch (err) {
      setError(err.message || 'Something went wrong while predicting this flight.')
      setResult(null)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  return { result, loading, error, predict, reset }
}