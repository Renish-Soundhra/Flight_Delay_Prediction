import { useState } from 'react'

const AIRLINES = [
  { code: 'AA', name: 'American Airlines' },
  { code: 'DL', name: 'Delta Air Lines' },
  { code: 'UA', name: 'United Airlines' },
  { code: 'WN', name: 'Southwest Airlines' },
  { code: 'B6', name: 'JetBlue Airways' },
  { code: 'AS', name: 'Alaska Airlines' },
  { code: 'NK', name: 'Spirit Airlines' },
  { code: 'F9', name: 'Frontier Airlines' }
]

const DAYS_OF_WEEK = [
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
  { value: 7, label: 'Sunday' }
]

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

function timeStringToInt(value) {
  if (!value) return 0
  const [hours, minutes] = value.split(':')
  return parseInt(`${hours}${minutes}`, 10)
}

function intToTimeString(value) {
  const padded = String(value).padStart(4, '0')
  return `${padded.slice(0, 2)}:${padded.slice(2)}`
}

const initialState = {
  airline: 'DL',
  origin: 'JFK',
  destination: 'ATL',
  flight_number: 154,
  month: 1,
  day_of_month: 15,
  day_of_week: 3,
  scheduled_dep_time: intToTimeString(1800),
  scheduled_arrival_time: intToTimeString(2100),
  distance: 850
}

export default function FlightForm({ onSubmit, submitting }) {
  const [form, setForm] = useState(initialState)

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function handleTextField(field, maxLength) {
    return (event) => {
      const value = event.target.value.toUpperCase().slice(0, maxLength)
      updateField(field, value)
    }
  }

  function handleNumberField(field) {
    return (event) => {
      const value = event.target.value === '' ? '' : Number(event.target.value)
      updateField(field, value)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()

    const payload = {
      month: Number(form.month),
      day_of_month: Number(form.day_of_month),
      day_of_week: Number(form.day_of_week),
      scheduled_dep_time: timeStringToInt(form.scheduled_dep_time),
      scheduled_arrival_time: timeStringToInt(form.scheduled_arrival_time),
      flight_number: Number(form.flight_number),
      distance: Number(form.distance),
      origin: form.origin,
      destination: form.destination,
      airline: form.airline
    }

    onSubmit(payload)
  }

  return (
    <form className="terminal" onSubmit={handleSubmit}>
      <div className="terminal-header">
        <span className="terminal-dot" />
        <span>Flight Details</span>
      </div>

      <div className="form-grid">
        <div className="field">
          <label htmlFor="airline">Airline</label>
          <select
            id="airline"
            value={form.airline}
            onChange={(event) => updateField('airline', event.target.value)}
          >
            {AIRLINES.map((airline) => (
              <option key={airline.code} value={airline.code}>
                {airline.code} — {airline.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="flight_number">Flight Number</label>
          <input
            id="flight_number"
            type="number"
            min="1"
            value={form.flight_number}
            onChange={handleNumberField('flight_number')}
            required
          />
        </div>

        <div className="field">
          <label htmlFor="origin">Origin Airport</label>
          <input
            id="origin"
            type="text"
            value={form.origin}
            onChange={handleTextField('origin', 3)}
            placeholder="JFK"
            required
          />
        </div>

        <div className="field">
          <label htmlFor="destination">Destination Airport</label>
          <input
            id="destination"
            type="text"
            value={form.destination}
            onChange={handleTextField('destination', 3)}
            placeholder="ATL"
            required
          />
        </div>

        <div className="field">
          <label htmlFor="month">Month</label>
          <select
            id="month"
            value={form.month}
            onChange={(event) => updateField('month', event.target.value)}
          >
            {MONTHS.map((name, index) => (
              <option key={name} value={index + 1}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="day_of_month">Day</label>
          <input
            id="day_of_month"
            type="number"
            min="1"
            max="31"
            value={form.day_of_month}
            onChange={handleNumberField('day_of_month')}
            required
          />
        </div>

        <div className="field">
          <label htmlFor="day_of_week">Day of Week</label>
          <select
            id="day_of_week"
            value={form.day_of_week}
            onChange={(event) => updateField('day_of_week', event.target.value)}
          >
            {DAYS_OF_WEEK.map((day) => (
              <option key={day.value} value={day.value}>
                {day.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="distance">Distance (miles)</label>
          <input
            id="distance"
            type="number"
            min="1"
            value={form.distance}
            onChange={handleNumberField('distance')}
            required
          />
        </div>

        <div className="field">
          <label htmlFor="scheduled_dep_time">Scheduled Departure</label>
          <input
            id="scheduled_dep_time"
            type="time"
            value={form.scheduled_dep_time}
            onChange={(event) =>
              updateField('scheduled_dep_time', event.target.value)
            }
            required
          />
        </div>

        <div className="field">
          <label htmlFor="scheduled_arrival_time">Scheduled Arrival</label>
          <input
            id="scheduled_arrival_time"
            type="time"
            value={form.scheduled_arrival_time}
            onChange={(event) =>
              updateField('scheduled_arrival_time', event.target.value)
            }
            required
          />
        </div>
      </div>

      <div className="form-footer">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting}
        >
          {submitting ? 'Predicting…' : 'Predict Delay →'}
        </button>
      </div>
    </form>
  )
}