import FlightForm from '../components/FlightForm.jsx'
import PredictionResult from '../components/PredictionResult.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import usePrediction from '../hooks/usePrediction.js'

export default function Prediction() {
  const { result, loading, error, predict } = usePrediction()

  return (
    <main className="section">
      <div className="container">
        <div className="section-head">
          <div className="eyebrow">Departure Terminal</div>
          <h1 className="section-title">Flight Prediction</h1>
          <p className="section-sub">
            Enter the flight's route and schedule below. The model checks it against
            patterns learned from historical departures and returns a delay probability.
          </p>
        </div>

        <div className={`predict-layout${result || loading || error ? ' has-result' : ''}`}>
          <FlightForm onSubmit={predict} submitting={loading} />

          {(loading || error || result) && (
            <div>
              {loading && <Loading label="Checking the board" />}
              {!loading && error && <ErrorMessage message={error} />}
              {!loading && !error && result && <PredictionResult result={result} />}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}