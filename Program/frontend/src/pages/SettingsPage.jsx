import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshCw, Database, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { fetchSettings, updateSettings, fetchDatasets, refreshCache } from '../utils/api';

const STORAGE_KEY = 'sgtb-settings';
const DEFAULT_SETTINGS = {
  language: 'en',
  default_wt_time: 0.25,
  default_wt_cost: 0.25,
  default_wt_risk: 0.25,
  default_wt_comfort: 0.25,
};

function loadSettings() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return stored ? { ...DEFAULT_SETTINGS, ...stored } : null;
  } catch { return null; }
}

function saveToLocal(settings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  localStorage.setItem('sgtb-lang', settings.language);
}

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const [settings, setSettings] = useState(() => loadSettings() || DEFAULT_SETTINGS);
  const [datasets, setDatasets] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState(null);

  // Try to sync from backend on mount, but localStorage is the source of truth
  useEffect(() => {
    fetchDatasets().catch(() => null).then(d => setDatasets(d));
    fetchSettings().catch(() => null).then(s => {
      if (s) {
        const merged = { ...DEFAULT_SETTINGS, ...loadSettings(), ...s };
        setSettings(merged);
        saveToLocal(merged);
        i18n.changeLanguage(merged.language);
      }
    });
  }, []);

  function updateLocal(next) {
    setSettings(next);
    saveToLocal(next);
  }

  function handleLanguageChange(lang) {
    const next = { ...settings, language: lang };
    updateLocal(next);
    i18n.changeLanguage(lang);
  }

  async function handleSave() {
    if (!settings) return;
    setSaving(true);
    saveToLocal(settings);
    try {
      await updateSettings(settings);
      setMessage({ type: 'success', text: t('settings.saved') });
    } catch {
      // Still saved locally even if backend fails
      setMessage({ type: 'success', text: t('settings.saved') });
    }
    setSaving(false);
    setTimeout(() => setMessage(null), 2000);
  }

  async function handleRefresh() {
    setRefreshing(true);
    try {
      const result = await refreshCache();
      setDatasets(result);
      setMessage({ type: 'success', text: t('settings.cacheRefreshed') });
    } catch {
      setMessage({ type: 'error', text: t('settings.refreshFailed') });
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
      <h1 className="text-xl font-bold text-white font-display animate-fade-up">{t('settings.title')}</h1>

      {/* Preferences */}
      {settings && (
        <div className="glass rounded-2xl p-4 space-y-4 animate-fade-up delay-1">
          <h2 className="text-sm font-semibold text-slate-200 font-display">{t('settings.preferences')}</h2>
          <div>
            <label className="text-[11px] text-slate-500 mb-1 block font-display">{t('settings.language')}</label>
            <select
              value={settings.language || 'en'}
              onChange={e => handleLanguageChange(e.target.value)}
              className="input-dark w-full px-3 py-2.5 rounded-xl text-sm"
            >
              <option value="en">{t('settings.langEn')}</option>
              <option value="zh">{t('settings.langZh')}</option>
              <option value="ms">{t('settings.langMs')}</option>
              <option value="ta">{t('settings.langTa')}</option>
            </select>
          </div>
          <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider pt-2 font-display">{t('settings.defaultWeights')}</h3>
          {[
            { key: 'default_wt_time', label: t('weight.time') },
            { key: 'default_wt_cost', label: t('weight.cost') },
            { key: 'default_wt_risk', label: t('weight.risk') },
            { key: 'default_wt_comfort', label: t('weight.comfort') },
          ].map(({ key, label }) => (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs text-slate-400 w-20">{label}</span>
              <input
                type="range"
                min="0" max="1" step="0.05"
                value={settings[key] ?? 0.25}
                onChange={e => updateLocal({ ...settings, [key]: parseFloat(e.target.value) })}
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
            {t('settings.save')}
          </button>
        </div>
      )}

      {/* Data Status */}
      <div className="glass rounded-2xl p-4 space-y-3 animate-fade-up delay-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 font-display">
            <Database size={15} className="text-slate-500" />
            {t('settings.dataSources')}
          </h2>
          <button onClick={handleRefresh} disabled={refreshing}
            className="text-[11px] text-amber-400 font-medium flex items-center gap-1 font-display hover:text-amber-300 transition-colors">
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            {t('settings.refresh')}
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
                      <AlertCircle size={10} /> {t('settings.fallback')}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md ring-1 ring-emerald-500/20">
                      <CheckCircle size={10} /> {t('settings.live')}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[11px] text-slate-500">{t('settings.backendOffline')}</p>
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
