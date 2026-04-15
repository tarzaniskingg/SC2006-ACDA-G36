import { useState, useCallback, useEffect, useRef } from 'react'
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
  const [showDemoPanel, setShowDemoPanel] = useState(false)
  const tapTimesRef = useRef([])

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

  // Demo comparison URLs — opens real Google Maps / CityMapper frontends
  const gmapMode = selectedRoute?.category === 'Taxi' || selectedRoute?.category === 'Drive'
    ? 'driving' : 'transit'
  const gmapsUrl = query
    ? `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(query.origin + ', Singapore')}&destination=${encodeURIComponent(query.destination + ', Singapore')}&travelmode=${gmapMode}`
    : null
  const originCoords = results?.origin_latlng
  const destCoords = results?.dest_latlng
  const citymapperUrl = query && originCoords && destCoords
    ? `https://citymapper.com/directions?startcoord=${originCoords[0]},${originCoords[1]}&startname=${encodeURIComponent(query.origin)}&endcoord=${destCoords[0]},${destCoords[1]}&endname=${encodeURIComponent(query.destination)}`
    : null

  // Triple-tap the dark background outside the phone to reveal demo buttons
  function handleBackgroundTap(e) {
    if (e.target !== e.currentTarget) return
    const now = Date.now()
    tapTimesRef.current = [...tapTimesRef.current.slice(-2), now]
    if (tapTimesRef.current.length === 3 && now - tapTimesRef.current[0] < 1500) {
      setShowDemoPanel(p => !p)
      tapTimesRef.current = []
    }
  }

  const demoBtnBase = 'w-full px-3 py-1.5 rounded-lg text-[11px] font-mono transition-all border-2 border-dashed select-none text-left'
  const demoBtnActive = 'border-amber-500/60 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 hover:text-amber-200'
  const demoBtnDisabled = 'border-slate-600 bg-slate-800/60 text-slate-400 cursor-not-allowed'

  return (
    <div className="h-screen w-screen overflow-hidden" style={{ background: '#050810' }}
      onClick={handleBackgroundTap}>

      {/* ===== DEMO BUTTONS — revealed by triple-tapping background ===== */}
      {showDemoPanel && (
        <div className="fixed top-3 right-3 z-50 flex flex-col gap-2 anim-fade-in">
          <button onClick={() => gmapsUrl && window.open(gmapsUrl, 'gmaps-compare')}
            disabled={!gmapsUrl}
            className={`${demoBtnBase} ${gmapsUrl ? demoBtnActive : demoBtnDisabled}`}>
            {'\u25a1'} Open Google Maps
            <span className="block text-[9px] text-slate-500 mt-0.5">for demo only</span>
          </button>
          <button onClick={() => citymapperUrl && window.open(citymapperUrl, 'citymapper-compare')}
            disabled={!citymapperUrl}
            className={`${demoBtnBase} ${citymapperUrl ? demoBtnActive : demoBtnDisabled}`}>
            {'\u25a1'} Open CityMapper
            <span className="block text-[9px] text-slate-500 mt-0.5">for demo only</span>
          </button>
        </div>
      )}

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
