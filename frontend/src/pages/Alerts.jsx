import React, { useEffect, useState } from 'react';
import api from '../services/api';

export default function Alerts() {
  const [rules, setRules] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ name: 'My Rule', city: '', temperature_max: '', wind_speed_max: '', email_enabled: true });

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [r, a] = await Promise.all([api.getAlertRules(), api.getRecentAlerts()]);
      setRules(r);
      setAlerts(a);
    } catch (e) {
      setError(e.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const createRule = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...form };
      if (payload.temperature_max === '') delete payload.temperature_max;
      if (payload.wind_speed_max === '') delete payload.wind_speed_max;
      const created = await api.createAlertRule(payload);
      setRules([created, ...rules]);
      setForm({ name: 'My Rule', city: '', temperature_max: '', wind_speed_max: '', email_enabled: true });
    } catch (e) {
      alert(e.message);
    }
  };

  const removeRule = async (id) => {
    if (!confirm('Delete this rule?')) return;
    try {
      await api.deleteAlertRule(id);
      setRules(rules.filter(r => r.id !== id));
    } catch (e) {
      alert(e.message);
    }
  };

  if (loading) return <div style={{ padding: 20 }}>Loading...</div>;
  if (error) return <div style={{ padding: 20, color: 'red' }}>{error}</div>;

  return (
    <div style={{ padding: 20 }}>
      <h2>Alert Rules</h2>
      <form onSubmit={createRule} style={{ marginBottom: 20 }}>
        <input placeholder="Rule name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
        <input placeholder="City ID" value={form.city} onChange={e => setForm({ ...form, city: e.target.value })} />
        <input placeholder="Temp max (°C)" value={form.temperature_max} onChange={e => setForm({ ...form, temperature_max: e.target.value })} />
        <input placeholder="Wind max (km/h)" value={form.wind_speed_max} onChange={e => setForm({ ...form, wind_speed_max: e.target.value })} />
        <label>
          <input type="checkbox" checked={form.email_enabled} onChange={e => setForm({ ...form, email_enabled: e.target.checked })} /> Email
        </label>
        <button type="submit">Create Rule</button>
      </form>

      <ul>
        {rules.map(r => (
          <li key={r.id}>
            {r.name} - City {r.city} - {r.severity} - {r.is_active ? 'Active' : 'Inactive'}
            <button onClick={() => removeRule(r.id)} style={{ marginLeft: 10 }}>Delete</button>
          </li>
        ))}
      </ul>

      <h2 style={{ marginTop: 30 }}>Recent Alerts</h2>
      <ul>
        {alerts.map(a => (
          <li key={a.id}>
            [{a.severity}] {a.title} - {a.message}
          </li>
        ))}
      </ul>
    </div>
  );
}