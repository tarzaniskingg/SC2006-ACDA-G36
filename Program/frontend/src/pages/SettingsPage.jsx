import { useState, useEffect } from 'react';
import { RefreshCw, Database, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { fetchSettings, updateSettings, fetchDatasets, refreshCache } from '../utils/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [datasets, setDatasets] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    Promise.all([
      fetchSettings().catch(() => null),
      fetchDatasets().catch(() => null),
    ]).then(([s, d]) => {
      setSettings(s);
      setDatasets(d);
      setLoading(false);
    });
  }, []);

  async function handleSave() {
    if (!settings) return;
    setSaving(true);
    try {
      await updateSettings(settings);
      setMessage({ type: 'success', text: 'Settings saved' });
    } catch {
      setMessage({ type: 'error', text: 'Failed to save settings' });
    }
    setSaving(false);
    setTimeout(() => setMessage(null), 2000);
  }

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await refreshCache();
      const d = await fetchDatasets().catch(() => null);
      setDatasets(d);
      setMessage({ type: 'success', text: 'Cache refreshed' });
    } catch {
      setMessage({ type: 'error', text: 'Failed to refresh cache' });
    }
    setRefreshing(false);
    setTimeout(() => setMessage(null), 2000);
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center pb-24">
        <Loader2 className="animate-spin text-sky-500" size={24} />
      </div>
    );
  }

  // datasets response is { sources: { name: { ... } } }
  const sources = datasets?.sources || {};

  return (
    <div className="flex-1 px-4 pt-6 pb-24 space-y-4">
      <h1 className="text-xl font-bold text-slate-900">Settings</h1>

      {/* Preferences */}
      {settings && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Preferences</h2>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Language</label>
            <select
              value={settings.language || 'en'}
              onChange={e => setSettings({ ...settings, language: e.target.value })}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30"
            >
              <option value="en">English</option>
              <option value="zh">Chinese</option>
              <option value="ms">Malay</option>
              <option value="ta">Tamil</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Units</label>
            <select
              value={settings.units || 'metric'}
              onChange={e => setSettings({ ...settings, units: e.target.value })}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30"
            >
              <option value="metric">Metric (km)</option>
              <option value="imperial">Imperial (mi)</option>
            </select>
          </div>

          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide pt-2">Default Weights</h3>
          {[
            { key: 'default_wt_time', label: 'Time' },
            { key: 'default_wt_reliability', label: 'Reliability' },
            { key: 'default_wt_crowding', label: 'Crowding' },
            { key: 'default_wt_budget', label: 'Budget' },
          ].map(({ key, label }) => (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs text-slate-600 w-20">{label}</span>
              <input
                type="range"
                min="0" max="1" step="0.05"
                value={settings[key] ?? 0.25}
                onChange={e => setSettings({ ...settings, [key]: parseFloat(e.target.value) })}
                className="flex-1 accent-sky-500"
              />
              <span className="text-xs font-mono text-slate-400 w-8 text-right">
                {(settings[key] ?? 0.25).toFixed(2)}
              </span>
            </div>
          ))}

          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-sky-500 text-white font-semibold py-2.5 rounded-xl text-sm disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
            Save Settings
          </button>
        </div>
      )}

      {/* Data Status */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <Database size={16} className="text-slate-400" />
            Data Sources
          </h2>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-xs text-sky-500 font-medium flex items-center gap-1"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {Object.keys(sources).length > 0 ? (
          <div className="space-y-2">
            {Object.entries(sources).map(([key, info]) => (
              <div key={key} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                <span className="text-xs font-medium text-slate-600">{key}</span>
                <div className="flex items-center gap-2">
                  {info.is_fallback ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                      <AlertCircle size={10} /> Fallback
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                      <CheckCircle size={10} /> Live
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400">Could not load dataset info</p>
        )}
      </div>

      {/* Toast message */}
      {message && (
        <div className={`fixed top-4 left-4 right-4 z-50 px-4 py-3 rounded-xl text-sm font-medium shadow-lg transition-all ${
          message.type === 'success' ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'
        }`}>
          {message.text}
        </div>
      )}
    </div>
  );
}
