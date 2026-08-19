import { useMemo, useState } from 'react'

const EMPTY = {
  date_from: '',
  date_to: '',
  airline: '',
  origin: '',
  destination: '',
  flight_number: '',
  tail_number: '',
  risk: '',
  prediction: '',
  prob_min: '',
  prob_max: '',
  route_search: '',
}

export default function useDashboardFilters() {
  const [filters, setFilters] = useState(EMPTY)
  const [asOf, setAsOf] = useState('')

  function update(field, value) {
    setFilters((prev) => ({ ...prev, [field]: value }))
  }

  function reset() {
    setFilters(EMPTY)
    setAsOf('')
  }

  const params = useMemo(
    () => ({
      ...filters,
      as_of: asOf || undefined,
    }),
    [filters, asOf]
  )

  return { filters, update, reset, params, asOf, setAsOf }
}
