export default function ErrorMessage({ message }) {
  if (!message) return null
  return (
    <div className="error-box">
      <span>⚠</span>
      <span>{message}</span>
    </div>
  )
}