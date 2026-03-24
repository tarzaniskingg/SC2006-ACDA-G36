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
        <Loader2 className="animate-spin text-amber-400" size={24} />
      </div>
    );
  }

  const sources = datasets?.sources || {};

  return (
    <div className="flex-1 px-4 pt-6 pb-24 space-y-4">
      <h1 className="text-xl font-bold text-white font-display animate-fade-up">Settings</h1>

      {/* Preferences */}
      {settings && (
        <div className="glass rounded-2xl p-4 space-y-4 animate-fade-up delay-1">
          <h2 className="text-sm font-semibold text-slate-200 font-display">Preferences</h2>
          <div>
            <label className="text-[11px] text-slate-500 mb-1 block font-display">Language</label>
            <select
              value={settings.language || 'en'}
              onChange={e => setSettings({ ...settings, language: e.target.value })}
              className="input-dark w-full px-3 py-2.5 rounded-xl text-sm"
            >
              <option value="en">English</option>
              <option value="zh">Chinese</option>
              <option value="ms">Malay</option>
              <option value="ta">Tamil</option>
            </select>
          </div>
          <div>
            <label className="text-[11px] text-slate-500 mb-1 block font-display">Units</label>
            <select
              value={settings.units || 'metric'}
              onChange={e => setSettings({ ...settings, units: e.target.value })}
              className="input-dark w-full px-3 py-2.5 rounded-xl text-sm"
            >
              <option value="metric">Metric (km)</option>
              <option value="imperial">Imperial (mi)</option>
            </select>
          </div>

          <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider pt-2 font-display">Default Weights</h3>
          {[
            { key: 'default_wt_time', label: 'Time' },
            { key: 'default_wt_reliability', label: 'Reliability' },
            { key: 'default_wt_crowding', label: 'Crowding' },
            { key: 'default_wt_budget', label: 'Budget' },
          ].map(({ key, label }) => (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs text-slate-400 w-20">{label}</span>
              <input
                type="range"
                min="0" max="1" step="0.05"
                value={settings[key] ?? 0.25}
                onChange={e => setSettings({ ...settings, [key]: parseFloat(e.target.value) })}
                className="flex-1"
              />
              <span className="text-xs font-mono text-slate-500 w-8 text-right">
                {(settings[key] ?? 0.25).toFixed(2)}
              </span>
            </div>
          ))}

          <button onClick={handleSave} disabled={saving}
            className="w-full btn-primary py-2.5 rounded-xl text-sm font-display font-semibold flex items-center justify-center gap-2">
            {saving ? <Loader2 size={15} className="animate-spin" /> : <CheckCircle size={15} />}
            Save Settings
          </button>
        </div>
      )}

      {/* Data Status */}
      <div className="glass rounded-2xl p-4 space-y-3 animate-fade-up delay-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 font-display">
            <Database size={15} className="text-slate-500" />
            Data Sources
          </h2>
          <button onClick={handleRefresh} disabled={refreshing}
            className="text-[11px] text-amber-400 font-medium flex items-center gap-1 font-display hover:text-amber-300 transition-colors">
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {Object.keys(sources).length > 0 ? (
          <div className="space-y-2">
            {Object.entries(sources).map(([key, info]) => (
              <div key={key} className="flex items-center justify-between py-1.5 border-b border-white/[0.04] last:border-0">
                <span className="text-[11px] font-medium text-slate-300">{key}</span>
                <div className="flex items-center gap-2">
                  {info.is_fallback ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-md ring-1 ring-amber-500/20">
                      <AlertCircle size={10} /> Fallback
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md ring-1 ring-emerald-500/20">
                      <CheckCircle size={10} /> Live
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[11px] text-slate-500">Could not load dataset info</p>
        )}
      </div>

      {/* Toast */}
      {message && (
        <div className={`fixed top-4 left-4 right-4 z-50 max-w-lg mx-auto px-4 py-3 rounded-xl text-sm font-medium font-display shadow-lg transition-all ${
          message.type === 'success' ? 'bg-emerald-500/90 text-white' : 'bg-red-500/90 text-white'
        }`} style={{ backdropFilter: 'blur(8px)' }}>
          {message.text}
        </div>
      )}
    </div>
  );
}
