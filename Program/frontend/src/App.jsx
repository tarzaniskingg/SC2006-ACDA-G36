import { useState, useCallback } from 'react'
import { Routes, Route } from 'react-router-dom'
import MainView from './pages/MainView'
import ScoringPage from './pages/ScoringPage'
import SettingsPage from './pages/SettingsPage'
import BottomNav from './components/BottomNav'
import { fetchRoutes } from './utils/api'

function App() {
  const [results, setResults] = useState(null)
  const [query, setQuery] = useState(null)
  const [selectedRoute, setSelectedRoute] = useState(null)

  const [searchForm, setSearchForm] = useState({
    origin: '',
    destination: '',
    modes: { transit: true, driving: true },
    weights: { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 },
    constraints: { max_walk_min: '', max_transfers: '', max_budget: '' },
  })

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

  return (
    <div className="max-w-lg mx-auto h-screen flex flex-col relative overflow-hidden" style={{ background: '#080c18' }}>
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
  )
}

export default App
