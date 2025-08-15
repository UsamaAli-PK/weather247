import React, { useState } from 'react';
import api from '../services/api';

export default function Predictions() {
  const [cities, setCities] = useState('London,Paris');
  const [results, setResults] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      const list = cities.split(',').map(s => s.trim()).filter(Boolean);
      const data = await api.getBatchAIPredictions(list);
      setResults(data.results || [data]);
      const a = await api.getPredictionAnalytics();
      setAnalytics(a);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>AI Predictions</h2>
      <div>
        <input value={cities} onChange={e => setCities(e.target.value)} placeholder="Comma-separated cities" />
        <button onClick={fetchPredictions} disabled={loading}>{loading ? 'Loading...' : 'Fetch'}</button>
      </div>
      <div style={{ display: 'flex', gap: 30, marginTop: 20 }}>
        <div style={{ flex: 1 }}>
          <h3>Results</h3>
          {results.map((r, idx) => (
            <div key={idx} style={{ border: '1px solid #ddd', padding: 10, marginBottom: 10 }}>
              <div><strong>{r.city}</strong></div>
              <div>Predictions: {r.predictions ? r.predictions.length : 0}</div>
            </div>
          ))}
        </div>
        <div style={{ flex: 1 }}>
          <h3>Analytics</h3>
          {analytics && (
            <pre style={{ background: '#f7f7f7', padding: 10 }}>{JSON.stringify(analytics, null, 2)}</pre>
          )}
        </div>
      </div>
    </div>
  );
}