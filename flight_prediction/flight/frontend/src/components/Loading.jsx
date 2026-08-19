export default function Loading({ label = 'Loading' }) {
  return (
    <div className="loading-wrap">
      <div className="spinner" />
      <span>{label}</span>
    </div>
  )
}