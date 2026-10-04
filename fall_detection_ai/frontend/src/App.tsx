import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import AlertBanner from './components/AlertBanner'
import Dashboard from './pages/Dashboard'
import Realtime from './pages/Realtime'
import VideoAnalysis from './pages/VideoAnalysis'
import Dataset from './pages/Dataset'
import Training from './pages/Training'
import Evaluation from './pages/Evaluation'
import FallEvents from './pages/FallEvents'
import Architecture from './pages/Architecture'
import Settings from './pages/Settings'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <AlertBanner />
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/realtime" element={<Realtime />} />
            <Route path="/video" element={<VideoAnalysis />} />
            <Route path="/dataset" element={<Dataset />} />
            <Route path="/training" element={<Training />} />
            <Route path="/evaluation" element={<Evaluation />} />
            <Route path="/events" element={<FallEvents />} />
            <Route path="/architecture" element={<Architecture />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}