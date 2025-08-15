import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import SignIn from './pages/SignIn';
import SignUp from './pages/SignUp';
import Dashboard from './pages/Dashboard';
import ModernDashboard from './pages/ModernDashboard';
import RoutePlanner from './pages/RoutePlanner';
import EnhancedRoutePlanner from './pages/EnhancedRoutePlanner';
import PWASettings from './pages/PWASettings';
import PWAManager from './components/PWAManager';
import './App.css';
import Alerts from './pages/Alerts';
import Predictions from './pages/Predictions';

function App() {
  return (
    <PWAManager>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/signin" element={<SignIn />} />
            <Route path="/signup" element={<SignUp />} />
            <Route path="/dashboard" element={<ModernDashboard />} />
            <Route path="/old-dashboard" element={<Dashboard />} />
            <Route path="/route-planner" element={<EnhancedRoutePlanner />} />
            <Route path="/simple-route-planner" element={<RoutePlanner />} />
            <Route path="/pwa-settings" element={<PWASettings />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/predictions" element={<Predictions />} />
          </Routes>
        </div>
      </Router>
    </PWAManager>
  );
}

export default App;
