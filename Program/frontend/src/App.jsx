import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import BottomNav from './components/BottomNav'
import SearchPage from './pages/SearchPage'
import ResultsPage from './pages/ResultsPage'
import MapPage from './pages/MapPage'
import ScoringPage from './pages/ScoringPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  const [results, setResults] = useState(null)
  const [query, setQuery] = useState(null)
  const [selectedRoute, setSelectedRoute] = useState(null)

  function handleResults(data, q) {
    setResults(data)
    setQuery(q)
    const routes = data?.routes || []
    setSelectedRoute(routes[0] || null)
  }

  return (
    <div className="max-w-lg mx-auto h-screen flex flex-col bg-slate-50 relative overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<SearchPage onResults={handleResults} />} />
          <Route
            path="/results"
            element={
              <ResultsPage
                results={results}
                query={query}
                selectedRoute={selectedRoute}
                onSelectRoute={setSelectedRoute}
              />
            }
          />
          <Route
            path="/map"
            element={
              <MapPage
                results={results}
                query={query}
                selectedRoute={selectedRoute}
                onSelectRoute={setSelectedRoute}
              />
            }
          />
          <Route
            path="/scoring"
            element={
              <ScoringPage
                results={results}
                query={query}
              />
            }
          />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
      <BottomNav />
    </div>
  )
}

export default App
