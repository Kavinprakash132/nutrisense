import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, PlusCircle, PieChart, LayoutDashboard } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import AddMeal from './pages/AddMeal';

function Navbar() {
  const location = useLocation();
  return (
    <nav className="navbar">
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold', fontSize: '1.25rem', color: 'var(--primary)' }}>
          <Activity size={24} />
          <span>NutriSense</span>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
          Smart diet insights for Tamil Nadu lifestyle
        </span>
      </div>
      <div className="nav-links">
        <Link to="/" className={location.pathname === '/' ? 'active' : ''} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <LayoutDashboard size={18} /> Dashboard
        </Link>
        <Link to="/add-meal" className={location.pathname === '/add-meal' ? 'active' : ''} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <PlusCircle size={18} /> Add Meal
        </Link>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/add-meal" element={<AddMeal />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
