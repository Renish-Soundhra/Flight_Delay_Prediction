export default function SimulationBar({
  running,
  speed,
  asOf,
  bounds,
  onStart,
  onPause,
  onReset,
  onSpeed,
}) {
  return (
    <section className="intel-sim">
      <div>
        <div className="eyebrow">Playback</div>
        <h3>Historical Simulation</h3>
        <p>
          This is not a live operations feed. Playback walks the existing 2015 timestamps in the
          engineered dataset. There is no 2026 simulation file in this project.
        </p>
      </div>
      <div className="intel-sim-controls">
        <div className="intel-sim-clock">{asOf ? asOf.replace('T', ' ') : bounds?.min_ts || '—'}</div>
        <div className="intel-sim-buttons">
          {!running ? (
            <button type="button" className="btn btn-primary" onClick={onStart}>
              Start
            </button>
          ) : (
            <button type="button" className="btn btn-ghost" onClick={onPause}>
              Pause
            </button>
          )}
          <button type="button" className="btn btn-ghost" onClick={onReset}>
            Reset
          </button>
        </div>
        <div className="intel-sim-speeds">
          {[1, 5, 10, 50].map((value) => (
            <button
              key={value}
              type="button"
              className={speed === value ? 'btn btn-primary' : 'btn btn-ghost'}
              onClick={() => onSpeed(value)}
            >
              {value}x
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
