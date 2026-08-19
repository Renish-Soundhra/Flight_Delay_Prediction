import { NavLink } from 'react-router-dom'

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <NavLink to="/" className="navbar-brand">
          <span className="mark" />
          FLIGHTBOARD
        </NavLink>
        <nav className="navbar-links">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            HOME
          </NavLink>
          <NavLink to="/predict" className={({ isActive }) => (isActive ? 'active' : '')}>
            PREDICT
          </NavLink>
          <NavLink to="/performance" className={({ isActive }) => (isActive ? 'active' : '')}>
            PERFORMANCE
          </NavLink>
          <NavLink to="/insights" className={({ isActive }) => (isActive ? 'active' : '')}>
            INSIGHTS
          </NavLink>
        </nav>
      </div>
    </header>
  )
}
