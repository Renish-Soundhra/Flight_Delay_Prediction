import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Home from './pages/Home.jsx'
import Prediction from './pages/Prediction.jsx'
import ModelPerformance from './pages/ModelPerformance.jsx'
import ModelInsights from './pages/ModelInsights.jsx'

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/predict" element={<Prediction />} />
        <Route path="/performance" element={<ModelPerformance />} />
        <Route path="/insights" element={<ModelInsights />} />
      </Routes>
      <footer className="footer">
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
          <span>FLIGHT DELAY PREDICTION</span>
          <span>HISTGRADIENT BOOSTING</span>
        </div>
      </footer>
    </div>
  )
}
