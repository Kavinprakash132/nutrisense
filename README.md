# NutriSense 🥗

NutriSense is a production-ready, ML-enhanced diet quality analysis system designed specifically for the Tamil Nadu food lifestyle. It helps users log meals, calculate macronutrient breakdowns, and provides actionable, personalized AI insights based on nutritional ratios.

## ✨ Features
* **Hybrid Data Engine:** Uses a highly curated local database of 30+ Tamil Nadu foods (Idli, Dosa, Sambar, etc.) with a seamless fallback to the Open Food Facts API for general queries.
* **Smart Scoring:** Mathematically grades meals (A-F) based on optimal macronutrient balances.
* **Actionable Insights:** Dynamically generates dietary recommendations depending on if meals are too high in carbs, lacking in protein, or heavy in fats.
* **Premium Dashboard:** Modern React SPA featuring animated Recharts, card layouts, skeleton loaders, and partial-failure handling.
* **Non-Blocking Architecture:** Firebase Firestore writes are threaded to ensure the API responds instantly.

## 🛠️ Tech Stack
* **Frontend:** React (Vite), Axios, Recharts, Lucide Icons, Vanilla CSS
* **Backend:** Flask, Python 3.14
* **Database:** Firebase Firestore (Admin SDK)
* **External APIs:** Open Food Facts

## 🚀 Setup Steps

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Ensure serviceAccountKey.json is placed in this directory!
python app.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to access the NutriSense dashboard!
