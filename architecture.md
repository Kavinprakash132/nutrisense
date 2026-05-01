# NutriSense – System Architecture

## 1. System Overview
NutriSense is an ML-based diet quality analyzer tailored for the Tamil Nadu food lifestyle. It evaluates the nutritional quality of meals, focusing on local cuisine, and provides a health score based on macronutrient balance. The system features a hybrid data approach: it relies primarily on a specialized local dataset for Tamil Nadu foods and falls back to the Open Food Facts API for general items.

## 2. Full Architecture
The system follows a modern 3-tier architecture:

*   **Frontend (Client Layer):** React.js single-page application (SPA). Handles user interactions, meal inputs with specific unit conversions, and visualizes nutritional scores and insights using interactive charts.
*   **Backend (Application Layer):** Flask REST API (Python 3.14). Manages business logic, unit conversions, fallback scoring algorithms, and handles external API communication.
*   **Database (Data Layer):** Firebase Firestore. Stores user profiles, meal logs, and daily summaries. Handles user authentication.
*   **External APIs:** Open Food Facts API (Fallback food data source).

## 3. Data Flow (Text Diagram)

```text
[ User (Web Browser) ]
        |
        | 1. Enters Meal (e.g., "3 Idlis", "1 cup Rice")
        v
[ React Frontend ]
        |
        | 2. POST /predict { food: "idli", quantity: 3, unit: "piece" }
        v
[ Flask Backend ] 
        |
        |-- 3a. Check Local Dataset (Tamil Nadu Foods)
        |       [ Local JSON/Python Dictionary ] -> Match Found? -> Return Data
        |
        |-- 3b. If Not Found -> External API Fallback
        |       [ Open Food Facts API ] -> Fetch & Normalize Data
        |
        | 4. Processing & Unit Conversion
        |    (Convert "piece" to "grams" -> calculate total macros)
        v
[ Nutrition Engine & ML/Scoring Module ]
        |
        | 5. Calculate Health Score (A-F Grade)
        |    (Using ML model or Rule-based formula fallback)
        v
[ Flask Backend ]
        |
        | 6. Save Log to Database
        v
[ Firebase Firestore ] (Collections: users, meals, daily_summary)
        |
        | 7. Return JSON Response (Score, Macros, Breakdown)
        v
[ React Frontend ]
        |
        | 8. Render Charts, Colors (Green/Yellow/Red), & Recommendations
        v
[ User (Visual Feedback) ]
```

## 4. Module Breakdown

### 4.1 Frontend Modules (React)
*   **Auth Module:** Login and Signup components integrated with Firebase Auth.
*   **Dashboard Module:** Displays daily summary, recent meals, and high-level charts.
*   **Meal Input Module:** Form with intelligent unit selection (grams, ml, piece, serving) based on food type.
*   **Report & Visualization Module:** Renders progress charts, score breakdowns, and color-coded feedback (Green/Yellow/Red).

### 4.2 Backend Modules (Flask)
*   **API Routes (`app.py`):** Defines endpoints (`GET /`, `GET /test`, `POST /predict`, `POST /analyze-meal`).
*   **Food Data Manager (`food_data.py`):** Handles querying the local dataset and the Open Food Facts API fallback. Normalizes API responses.
*   **Nutrition & Scoring Engine (`utils.py`):** 
    *   Converts user units (pieces, cups) to standard grams based on local dataset rules.
    *   Calculates the final nutritional score using the defined rule-based formula.
*   **Database Connector:** Firebase Admin SDK integration for saving meal logs and retrieving user history.

### 4.3 Data Modules
*   **Local Tamil Nadu Dataset:** A structured JSON or dictionary containing 30+ verified local foods with baseline metrics per 100g and default unit conversions (e.g., 1 idli = 40g).
*   **Firebase Collections:** 
    *   `users`: User profile and calorie goals.
    *   `meals`: Individual food entries.
    *   `daily_summary`: Aggregated daily macros and scores.
