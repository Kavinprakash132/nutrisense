import React, { useState, useRef, useMemo } from 'react';
import { analyzeMeal } from '../api/client';
import { Trash2, Plus, AlertCircle, CheckCircle, Info, ChevronRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

function AddMeal() {
  const [foods, setFoods] = useState([{ food: '', quantity: 1, unit: 'grams' }]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState([]);
  const [warnings, setWarnings] = useState([]);
  
  const lastInputRef = useRef(null);

  const handleAddFood = () => {
    setFoods([...foods, { food: '', quantity: 1, unit: 'grams' }]);
    setTimeout(() => {
      if (lastInputRef.current) lastInputRef.current.focus();
    }, 50);
  };

  const handleRemoveFood = (index) => {
    if (foods.length > 1) {
      setFoods(foods.filter((_, i) => i !== index));
    }
  };

  const handleChange = (index, field, value) => {
    const newFoods = [...foods];
    newFoods[index][field] = value;
    setFoods(newFoods);
  };

  const validateForm = () => {
    for (let f of foods) {
      if (!f.food.trim()) return "Food name cannot be empty (e.g. Idli, Dosa)";
      if (f.quantity <= 0) return "Quantity must be greater than zero";
    }
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setWarnings([]);
    setResult(null);

    const validationError = validateForm();
    if (validationError) {
      setErrors([validationError]);
      return;
    }

    setLoading(true);
    try {
      const response = await analyzeMeal(foods);
      
      if (response.success) {
        setResult(response.data);
        if (response.errors && response.errors.length > 0) {
          setWarnings(response.errors);
        }
      } else {
        setErrors(response.errors || ['Analysis failed completely.']);
      }
    } catch (err) {
      setErrors(err.errors || ['Failed to connect to the server.']);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 75) return 'var(--color-green)';
    if (score >= 60) return 'var(--color-yellow)';
    return 'var(--color-red)';
  };

  const chartData = useMemo(() => {
    if (!result) return [];
    return [
      { name: 'Protein (g)', value: result.meal_summary.total_nutrients.protein_g, fill: '#3b82f6' },
      { name: 'Carbs (g)', value: result.meal_summary.total_nutrients.carbs_g, fill: '#f59e0b' },
      { name: 'Fat (g)', value: result.meal_summary.total_nutrients.fat_g, fill: '#ef4444' }
    ];
  }, [result]);

  const recommendations = useMemo(() => {
    if (!result) return [];
    const { protein_g, carbs_g, fat_g, calories } = result.meal_summary.total_nutrients;
    const recs = [];
    
    const safeCals = Math.max(calories, 1);
    if ((protein_g * 4) / safeCals < 0.15) recs.push({ text: "Increase protein intake (add egg, dal, or chicken)", type: "warning", color: "#3b82f6" });
    else recs.push({ text: "Excellent protein ratio!", type: "success", color: "#10b981" });

    if ((carbs_g * 4) / safeCals > 0.65) recs.push({ text: "Carbs are a bit high. Try smaller rice portions.", type: "warning", color: "#f59e0b" });
    if ((fat_g * 9) / safeCals > 0.35) recs.push({ text: "Fat content is high. Consider less oil or fried items.", type: "warning", color: "#ef4444" });

    return recs;
  }, [result]);

  const getInsightText = () => {
    if (!result) return "";
    const { protein_g, carbs_g, calories } = result.meal_summary.total_nutrients;
    const safeCals = Math.max(calories, 1);
    const pRatio = (protein_g * 4) / safeCals;
    const cRatio = (carbs_g * 4) / safeCals;
    
    if (cRatio > 0.65) return "This meal is moderately balanced but slightly high in carbohydrates.";
    if (pRatio < 0.15) return "This meal provides energy but is lacking in protein.";
    if (pRatio >= 0.20 && cRatio <= 0.55) return "Excellent choice! This is a highly balanced, protein-rich meal.";
    return "This meal provides a moderate balance of macronutrients.";
  };

  return (
    <div className="dashboard-grid fade-in">
      <div className="card">
        <h2 className="card-title">Analyze Meal</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          Enter your food items and units. e.g., "3 Idli pieces" or "200 grams Rice".
        </p>
        
        {errors.length > 0 && (
          <div className="alert alert-error fade-in">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              <AlertCircle size={18} /> Error
            </div>
            <ul style={{ paddingLeft: '1.5rem' }}>
              {errors.map((err, i) => <li key={i}>{err}</li>)}
            </ul>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {foods.map((item, index) => (
            <div key={index} className="form-row fade-in">
              <div className="form-group" style={{ flex: 2, marginBottom: 0 }}>
                <label className="form-label">Food</label>
                <input 
                  type="text" 
                  className="form-control" 
                  placeholder="e.g. Idli, Sambar, Chicken" 
                  value={item.food}
                  onChange={(e) => handleChange(index, 'food', e.target.value)}
                  ref={index === foods.length - 1 ? lastInputRef : null}
                  required
                />
              </div>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label className="form-label">Qty</label>
                <input 
                  type="number" 
                  min="0.1" 
                  step="0.1" 
                  className="form-control" 
                  value={item.quantity}
                  onChange={(e) => handleChange(index, 'quantity', e.target.value)}
                  required
                />
              </div>
              <div className="form-group" style={{ flex: 1.5, marginBottom: 0 }}>
                <label className="form-label">Unit <span style={{fontSize: '0.75rem', fontWeight: 'normal', color: 'var(--text-muted)'}}>(select one)</span></label>
                <select 
                  className="form-control" 
                  value={item.unit}
                  onChange={(e) => handleChange(index, 'unit', e.target.value)}
                >
                  <option value="grams">Grams</option>
                  <option value="ml">ml</option>
                  <option value="piece">Piece</option>
                  <option value="serving">Serving</option>
                  <option value="cup">Cup</option>
                </select>
              </div>
              {foods.length > 1 && (
                <button type="button" className="btn btn-secondary" onClick={() => handleRemoveFood(index)} style={{ padding: '0.75rem', marginBottom: 0 }}>
                  <Trash2 size={18} color="var(--color-red)" />
                </button>
              )}
            </div>
          ))}

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
            <button type="button" className="btn btn-secondary" onClick={handleAddFood} style={{ display: 'flex', gap: '0.5rem' }}>
              <Plus size={18} /> Add Food
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              Analyze Meal
            </button>
          </div>
        </form>
      </div>

      <div className="card" style={{ minHeight: '500px' }}>
        <h2 className="card-title">Results</h2>
        
        {loading ? (
          <div className="fade-in" style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
              <div className="skeleton skeleton-circle"></div>
            </div>
            <div className="skeleton skeleton-text" style={{ width: '60%', margin: '0 auto 2rem' }}></div>
            <div className="stat-grid" style={{ marginBottom: '2rem' }}>
              <div className="skeleton skeleton-block" style={{ height: '80px' }}></div>
              <div className="skeleton skeleton-block" style={{ height: '80px' }}></div>
              <div className="skeleton skeleton-block" style={{ height: '80px' }}></div>
            </div>
            <div className="skeleton skeleton-block"></div>
          </div>
        ) : result ? (
          <div className="fade-in">
            {warnings.length > 0 && (
              <div className="alert alert-warning fade-in" style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                  <AlertCircle size={18} /> Partial Success
                </div>
                <ul style={{ paddingLeft: '1.5rem' }}>
                  {warnings.map((err, i) => <li key={i}>{err}</li>)}
                </ul>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', marginBottom: '2rem', textAlign: 'center' }}>
              <div style={{ 
                width: '120px', height: '120px', borderRadius: '50%', 
                border: `8px solid ${getScoreColor(result.meal_summary.health_score.score)}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', marginBottom: '1rem'
              }}>
                <div style={{ fontSize: '3rem', fontWeight: 'bold', color: getScoreColor(result.meal_summary.health_score.score) }}>
                  {result.meal_summary.health_score.grade}
                </div>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                {result.meal_summary.health_score.score} / 100
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '300px', lineHeight: '1.5' }}>
                {getInsightText()}
              </p>
            </div>

            <div className="stat-grid" style={{ marginBottom: '2rem' }}>
              <div className="stat-card">
                <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{result.meal_summary.total_nutrients.calories}</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Calories</div>
              </div>
              <div className="stat-card">
                <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{result.meal_summary.total_nutrients.protein_g}g</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Protein</div>
              </div>
              <div className="stat-card">
                <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{result.meal_summary.total_nutrients.carbs_g}g</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Carbs</div>
              </div>
              <div className="stat-card">
                <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{result.meal_summary.total_nutrients.fat_g}g</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Fat</div>
              </div>
            </div>

            <h3 style={{ fontSize: '1.125rem', marginBottom: '1rem', fontWeight: '600' }}>Macronutrient Chart</h3>
            <div style={{ height: '250px', marginBottom: '2rem' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip cursor={{fill: '#f1f5f9'}} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <h3 style={{ fontSize: '1.125rem', marginBottom: '1rem', fontWeight: '600' }}>AI Suggestions</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '2rem' }}>
              {recommendations.map((rec, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px', borderLeft: `4px solid ${rec.color}` }}>
                  <Info size={20} color={rec.color} style={{ flexShrink: 0, marginTop: '0.125rem' }} />
                  <span>{rec.text}</span>
                </div>
              ))}
            </div>
            
            <h3 style={{ fontSize: '1.125rem', marginBottom: '1rem', fontWeight: '600' }}>Items Processed</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {result.foods.map((food, i) => (
                <li key={i} style={{ padding: '0.75rem', background: '#f1f5f9', borderRadius: '6px', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <ChevronRight size={16} color="var(--primary)" />
                    <span style={{ fontWeight: '500' }}>{food.quantity} {food.unit} {food.food_name}</span>
                  </div>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{food.nutrients.calories} kcal</span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '300px', color: 'var(--text-muted)' }}>
            <CheckCircle size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
            <p style={{ fontSize: '1.125rem', fontWeight: '500' }}>Ready to analyze</p>
            <p style={{ fontSize: '0.875rem' }}>Add your first meal to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default AddMeal;
