import React from 'react';
import { Link } from 'react-router-dom';
import { Activity, Flame, Drumstick, Wheat, Droplet, Clock, ChevronRight } from 'lucide-react';

function Dashboard() {
  // Simulated data for polished product rendering
  const recentMeals = [
    { id: 1, name: "3x Idli, 1x Sambar", time: "Today, 8:30 AM", score: 85, grade: "B", calories: 430 },
    { id: 2, name: "1x Chicken Chettinad, 2x Parotta", time: "Yesterday, 8:00 PM", score: 65, grade: "C", calories: 830 },
    { id: 3, name: "1x Filter Coffee", time: "Yesterday, 4:00 PM", score: 92, grade: "A", calories: 60 }
  ];

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold' }}>Good Morning, Prakash</h1>
          <p style={{ color: 'var(--text-muted)' }}>Here is your nutrition summary for today.</p>
        </div>
        <Link to="/add-meal" className="btn btn-primary">Log New Meal</Link>
      </div>
      
      {/* Daily Summary Panel */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 className="card-title" style={{ margin: 0 }}>Daily Summary</h2>
          <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)', background: '#f1f5f9', padding: '0.25rem 0.75rem', borderRadius: '12px' }}>
            {recentMeals.length} Meals Logged
          </span>
        </div>
        
        <div className="stat-grid">
          <div className="stat-card">
            <Flame size={24} color="#f97316" style={{ margin: '0 auto 0.5rem' }} />
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>1500</div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Calories</div>
          </div>
          <div className="stat-card">
            <Drumstick size={24} color="#3b82f6" style={{ margin: '0 auto 0.5rem' }} />
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>50g</div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Protein</div>
          </div>
          <div className="stat-card">
            <Wheat size={24} color="#f59e0b" style={{ margin: '0 auto 0.5rem' }} />
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>200g</div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Carbs</div>
          </div>
          <div className="stat-card">
            <Droplet size={24} color="#ef4444" style={{ margin: '0 auto 0.5rem' }} />
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>40g</div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Fat</div>
          </div>
          <div className="stat-card" style={{ background: '#ecfdf5', borderColor: '#a7f3d0' }}>
            <Activity size={24} color="#10b981" style={{ margin: '0 auto 0.5rem' }} />
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>82 (B)</div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Avg Score</div>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* History / Recent Meals */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 className="card-title" style={{ margin: 0 }}>Recent Meals</h2>
            <Clock size={20} color="var(--text-muted)" />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {recentMeals.length > 0 ? (
              recentMeals.map((meal) => (
                <div key={meal.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'var(--bg-color)', borderRadius: '8px', border: '1px solid var(--border-color)', transition: 'background 0.2s', cursor: 'pointer' }} className="hover-bg-slate">
                  <div>
                    <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.25rem' }}>{meal.name}</h3>
                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                      <span>{meal.time}</span>
                      <span>•</span>
                      <span>{meal.calories} kcal</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ 
                      width: '40px', height: '40px', borderRadius: '50%', 
                      background: meal.score >= 75 ? '#d1fae5' : meal.score >= 60 ? '#fef3c7' : '#fee2e2',
                      color: meal.score >= 75 ? '#059669' : meal.score >= 60 ? '#d97706' : '#dc2626',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '1.125rem'
                    }}>
                      {meal.grade}
                    </div>
                    <ChevronRight size={20} color="var(--text-muted)" />
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                No meals logged yet. Log a meal to see history.
              </div>
            )}
          </div>
        </div>

        {/* Daily Recommendations */}
        <div className="card">
          <h2 className="card-title">Actionable Insights</h2>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '1rem', listStyle: 'none' }}>
            <li style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #3b82f6' }}>
              <strong>Great Protein!</strong> You hit your protein target for the morning. Maintain this balance for lunch.
            </li>
            <li style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #f59e0b' }}>
              <strong>Watch the Carbs.</strong> Try substituting white rice with millet or quinoa for dinner to keep your blood sugar steady.
            </li>
            <li style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #10b981' }}>
              <strong>Excellent Consistency.</strong> You've logged 3 meals in a row. Keep it up!
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
