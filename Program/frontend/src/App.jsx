import { useState, useCallback, useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import MainView from './pages/MainView'
import ScoringPage from './pages/ScoringPage'
import SettingsPage from './pages/SettingsPage'
import BottomNav from './components/BottomNav'
import { fetchRoutes } from './utils/api'

function loadDefaultWeights() {
  try {
    const stored = JSON.parse(localStorage.getItem('sgtb-settings'))
    if (stored) {
      return {
        time: stored.default_wt_time ?? 0.25,
        cost: stored.default_wt_cost ?? 0.25,
        risk: stored.default_wt_risk ?? 0.25,
        comfort: stored.default_wt_comfort ?? 0.25,
      }
    }
  } catch { /* ignore */ }
  return { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 }
}

function App() {
  const location = useLocation()
  const [results, setResults] = useState(null)
  const [query, setQuery] = useState(null)
  const [selectedRoute, setSelectedRoute] = useState(null)
  const [showGmaps, setShowGmaps] = useState(false)

  const [searchForm, setSearchForm] = useState({
    origin: '',
    destination: '',
    modes: { transit: true, driving: true },
    weights: loadDefaultWeights(),
    constraints: { max_walk_min: '', max_transfers: '', max_budget: '' },
  })

  // Reload saved default weights when navigating back to the search page
  useEffect(() => {
    if (location.pathname === '/') {
      const fresh = loadDefaultWeights()
      setSearchForm(prev => ({ ...prev, weights: fresh }))
    }
  }, [location.pathname])

  function handleResults(data, q, formState) {
    setResults(data)
    setQuery(q)
    if (formState) setSearchForm(formState)
    setSelectedRoute(data?.routes?.[0] || null)
  }

  const handleRefresh = useCallback(async () => {
    if (!query?.origin || !query?.destination) return null
    const params = {
      origin: query.origin,
      destination: query.destination,
      include_transit: searchForm.modes.transit,
      include_driving: searchForm.modes.driving,
      wt_time: searchForm.weights.time,
      wt_cost: searchForm.weights.cost,
      wt_risk: searchForm.weights.risk,
      wt_comfort: searchForm.weights.comfort,
    }
    if (searchForm.constraints.max_walk_min) params.max_walk_min = parseInt(searchForm.constraints.max_walk_min)
    if (searchForm.constraints.max_transfers) params.max_transfers = parseInt(searchForm.constraints.max_transfers)
    if (searchForm.constraints.max_budget) params.max_budget = parseFloat(searchForm.constraints.max_budget)
    const data = await fetchRoutes(params)
    setResults(data)
    setSelectedRoute(data?.routes?.[0] || null)
    return data
  }, [query, searchForm])

  // Google Maps directions URL — opens the real Google Maps frontend
  const gmapMode = selectedRoute?.category === 'Taxi' || selectedRoute?.category === 'Drive'
    ? 'driving' : 'transit'
  const gmapsUrl = query
    ? `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(query.origin + ', Singapore')}&destination=${encodeURIComponent(query.destination + ', Singapore')}&travelmode=${gmapMode}`
    : null

  function openGmaps() {
    if (gmapsUrl) window.open(gmapsUrl, 'gmaps-compare')
  }

  return (
    <div className="h-screen w-screen overflow-hidden" style={{ background: '#050810' }}>
      {/* ===== DEMO TOGGLE — fixed outside the app box ===== */}
      <button
        onClick={openGmaps}
        disabled={!gmapsUrl}
        className={`fixed top-3 right-3 z-50 px-3 py-1.5 rounded-lg text-[11px] font-mono transition-all border-2 border-dashed select-none
          ${gmapsUrl
            ? 'border-amber-500/60 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 hover:text-amber-200'
            : 'border-slate-600 bg-slate-800/60 text-slate-400 cursor-not-allowed'
          }`}
      >
        {'\u25a1'} Open Google Maps
        <span className="block text-[9px] text-slate-500 mt-0.5 text-center">for demo only</span>
      </button>

      {/* ===== APP CONTAINER ===== */}
      <div className="max-w-lg mx-auto h-full w-full flex flex-col relative overflow-hidden"
        style={{ background: '#080c18' }}
      >
        <div className="flex-1 overflow-y-auto relative">
          <Routes>
            <Route path="/" element={
              <MainView
                results={results}
                query={query}
                selectedRoute={selectedRoute}
                onSelectRoute={setSelectedRoute}
                onResults={handleResults}
                onRefresh={handleRefresh}
                initialForm={searchForm}
              />
            } />
            <Route path="/scoring" element={
              <ScoringPage results={results} query={query} />
            } />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
        <BottomNav hasResults={!!results?.routes?.length} />
      </div>
    </div>
  )
}

export default App
