import { useEffect, useState } from 'react';
import { fetchCrowdingHeatmap } from '../utils/api';
import { crowdColor } from '../utils/helpers';

export default function CrowdingHeatmap({ stationName, compact = false }) {
  const [intervals, setIntervals] = useState([]);
  const [label, setLabel] = useState('');
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!stationName) return;
    fetchCrowdingHeatmap(stationName)
      .then(data => {
        setIntervals(data.intervals || []);
        setLabel(`${data.station || stationName} (${data.line || ''})`);
      })
      .catch(() => setError(true));
  }, [stationName]);

  if (error || !intervals.length) return null;

  // Parse intervals into 30-min blocks from 6AM to 11PM
  const blocks = [];
  for (const iv of intervals) {
    try {
      const d = new Date(iv.start);
      const h = d.getHours();
      const m = d.getMinutes();
      if (h >= 6 && h <= 23) {
        blocks.push({ hour: h, min: m, level: iv.crowd_level });
      }
    } catch {
      // skip
    }
  }

  if (!blocks.length) return null;

  // Current time marker
  const now = new Date();
  const nowH = now.getHours();
  const nowFrac = (nowH - 6 + now.getMinutes() / 60);
  const totalHours = 17; // 6AM to 11PM
  const nowPct = Math.max(0, Math.min(100, (nowFrac / totalHours) * 100));

  if (compact) {
    return (
      <div className="space-y-0.5">
        <div className="relative h-3 flex rounded-full overflow-hidden">
          {blocks.map((b, i) => (
            <div
              key={i}
              className="flex-1"
              style={{ backgroundColor: crowdColor(b.level) }}
              title={`${b.hour}:${String(b.min).padStart(2, '0')} — ${b.level}`}
            />
          ))}
          {nowH >= 6 && nowH <= 23 && (
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-slate-800"
              style={{ left: `${nowPct}%` }}
              title="Now"
            />
          )}
        </div>
        <div className="flex justify-between text-[9px] text-slate-400">
          <span>6AM</span>
          <span>12PM</span>
          <span>6PM</span>
          <span>11PM</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-[10px] text-slate-500">
        <span className="font-medium">{label || stationName}</span>
      </div>
      <div className="relative h-5 flex rounded-lg overflow-hidden">
        {blocks.map((b, i) => (
          <div
            key={i}
            className="flex-1 transition-colors"
            style={{ backgroundColor: crowdColor(b.level) }}
            title={`${b.hour}:${String(b.min).padStart(2, '0')} — ${b.level}`}
          />
        ))}
        {nowH >= 6 && nowH <= 23 && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-slate-900"
            style={{ left: `${nowPct}%` }}
          >
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[8px] font-bold text-slate-700">
              Now
            </div>
          </div>
        )}
      </div>
      <div className="flex justify-between text-[9px] text-slate-400">
        <span>6 AM</span>
        <span>9 AM</span>
        <span>12 PM</span>
        <span>3 PM</span>
        <span>6 PM</span>
        <span>9 PM</span>
        <span>11 PM</span>
      </div>
    </div>
  );
}
