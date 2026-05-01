# NutriSense - Master Project Document

This document contains EVERYTHING required to recreate the NutriSense full-stack application from scratch.

---

# 📁 SECTION 1 — PROJECT STRUCTURE

```text
nutrisense/
├── backend/
│   ├── app.py
│   ├── utils.py
│   ├── food_data.py
│   ├── firebase_service.py
│   ├── requirements.txt
│   └── serviceAccountKey.json (placeholder)
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── firebase_config.js (placeholder)
│       ├── api/
│       │   └── client.js
│       └── pages/
│           ├── Dashboard.jsx
│           └── AddMeal.jsx
```

---

# 📦 SECTION 2 — FULL CODE

## filename: backend/app.py

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from food_data import FoodDataManager
from utils import calculate_nutrients, rule_based_score
from firebase_service import FirebaseService

app = Flask(__name__)
CORS(app)  # Allow frontend to connect

# Initialize Data Manager
food_manager = FoodDataManager()

def format_response(success, data=None, errors=None):
    """
    Standardizes all API responses to:
    { "success": bool, "data": dict/null, "errors": list }
    """
    if errors is None:
        errors = []
    return jsonify({
        "success": success,
        "data": data,
        "errors": errors
    })

@app.route("/", methods=["GET"])
def home():
    return format_response(True, data={"status": "NutriSense API is running", "version": "1.0"})

@app.route("/test", methods=["GET"])
def test():
    return format_response(True, data={"message": "Test successful", "status": 200})

@app.route("/predict", methods=["POST"])
def predict():
    """
    ML-only/Single food prediction endpoint.
    Expects JSON: { "food": "idli", "quantity": 3, "unit": "piece" }
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return format_response(False, errors=["Invalid or empty JSON body"]), 400
            
        print("Incoming request:", data)
        
        if "food" not in data:
            return format_response(False, errors=["Missing 'food' in request body"]), 400
            
        food_query = data["food"]
        try:
            quantity = float(data.get("quantity", 1))
        except ValueError:
            return format_response(False, errors=["Quantity must be a number"]), 400
            
        if quantity <= 0:
            return format_response(False, errors=["Quantity must be greater than zero"]), 400
            
        unit = data.get("unit", "grams")
        
        # 1. Lookup Food
        food_info = food_manager.search_food(food_query)
        if food_info.get("error"):
            return format_response(False, errors=[food_info["error"]]), 404
            
        # 2. Calculate Nutrients
        total_grams, total_nutrients = calculate_nutrients(
            food_info["nutrition_per_100g"], 
            quantity, 
            unit, 
            food_info["default_weight_g"]
        )
        
        # 3. Score
        score_result = rule_based_score(
            protein_g=total_nutrients["protein_g"],
            carbs_g=total_nutrients["carbs_g"],
            fat_g=total_nutrients["fat_g"],
            calories=total_nutrients["calories"],
            target_calories=600  # Target for a single meal
        )
        
        return format_response(True, data={
            "food_name": food_info["name"],
            "source": food_info["source"],
            "input": {"quantity": quantity, "unit": unit},
            "total_grams": total_grams,
            "nutrients": total_nutrients,
            "health_score": score_result
        }), 200
        
    except Exception as e:
        return format_response(False, errors=[f"Server error: {str(e)}"]), 500

@app.route("/analyze-meal", methods=["POST"])
def analyze_meal():
    """
    Main logic endpoint for a full meal.
    Expects JSON: 
    { 
        "user_id": "optional_firebase_uid",
        "foods": [
            {"food": "idli", "quantity": 3, "unit": "piece"},
            {"food": "sambar", "quantity": 1, "unit": "cup"}
        ]
    }
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return format_response(False, errors=["Invalid or empty JSON body"]), 400
            
        print("Incoming request:", data)
        
        if "foods" not in data or not isinstance(data["foods"], list) or len(data["foods"]) == 0:
            return format_response(False, errors=["Missing or invalid 'foods' array in request body"]), 400
            
        meal_total_nutrients = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
        analyzed_foods = []
        errors = []
        
        for item in data["foods"]:
            food_query = item.get("food")
            if not food_query:
                errors.append("Empty food entry skipped")
                continue
                
            try:
                quantity = float(item.get("quantity", 1))
            except ValueError:
                errors.append(f"Food '{food_query}': Quantity must be a number")
                continue
                
            if quantity <= 0:
                errors.append(f"Food '{food_query}': Quantity must be greater than zero")
                continue
                
            unit = item.get("unit", "grams")
            
            # Lookup
            food_info = food_manager.search_food(food_query)
            if food_info.get("error"):
                errors.append(f"Food '{food_query}': {food_info['error']}")
                continue
                
            # Calculate
            total_grams, nutrients = calculate_nutrients(
                food_info["nutrition_per_100g"], 
                quantity, 
                unit, 
                food_info["default_weight_g"]
            )
            
            # Aggregate
            meal_total_nutrients["calories"] += nutrients["calories"]
            meal_total_nutrients["protein_g"] += nutrients["protein_g"]
            meal_total_nutrients["carbs_g"] += nutrients["carbs_g"]
            meal_total_nutrients["fat_g"] += nutrients["fat_g"]
            
            analyzed_foods.append({
                "food_name": food_info["name"],
                "quantity": quantity,
                "unit": unit,
                "total_grams": total_grams,
                "nutrients": nutrients,
                "image_url": food_info.get("image_url")
            })
            
        # If no foods were successfully analyzed, return failure
        if not analyzed_foods:
            return format_response(False, errors=errors), 400
            
        # Round final totals to 2 decimal places
        for k in meal_total_nutrients:
            meal_total_nutrients[k] = round(meal_total_nutrients[k], 2)
            
        # Calculate final score for the whole meal
        score_result = rule_based_score(
            protein_g=meal_total_nutrients["protein_g"],
            carbs_g=meal_total_nutrients["carbs_g"],
            fat_g=meal_total_nutrients["fat_g"],
            calories=meal_total_nutrients["calories"],
            target_calories=600  # Default target per meal
        )
        
        response_data = {
            "meal_summary": {
                "total_nutrients": meal_total_nutrients,
                "health_score": score_result
            },
            "foods": analyzed_foods
        }
        
        # Async save to Firebase if user_id is provided
        try:
            user_id = data.get("user_id")
            if user_id:
                FirebaseService.save_meal_async(user_id, response_data)
        except Exception as e:
            print("Firebase async error:", e)
        
        return format_response(True, data=response_data, errors=errors), 200

    except Exception as e:
        return format_response(False, errors=[f"Server error: {str(e)}"]), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

```

## filename: backend/utils.py

```python
def calculate_nutrients(nutrition_per_100g, quantity, unit, default_weight_g):
    """
    Converts units to grams and calculates total macronutrients for the given quantity.
    """
    # 1. Determine total grams
    if unit == "grams" or unit == "g":
        total_grams = quantity
    else:
        # Fallback to 100g if unit not found in defaults
        weight_per_unit = default_weight_g.get(unit, 100)
        total_grams = quantity * weight_per_unit
        
    # 2. Calculate nutrients based on total grams
    multiplier = total_grams / 100.0
    
    total_nutrients = {
        "calories": round(nutrition_per_100g.get("calories", 0) * multiplier, 2),
        "protein_g": round(nutrition_per_100g.get("protein_g", 0) * multiplier, 2),
        "carbs_g": round(nutrition_per_100g.get("carbs_g", 0) * multiplier, 2),
        "fat_g": round(nutrition_per_100g.get("fat_g", 0) * multiplier, 2)
    }
    
    return round(total_grams, 2), total_nutrients

def rule_based_score(protein_g, carbs_g, fat_g, calories, target_calories=2000):
    """
    Fallback formula to calculate health score (0-100) based on macronutrient ratios.
    """
    # Avoid division by zero
    safe_calories = max(calories, 1)
    
    protein_ratio = (protein_g * 4) / safe_calories
    carb_ratio = (carbs_g * 4) / safe_calories
    fat_ratio = (fat_g * 9) / safe_calories
    calorie_ratio = min(calories / target_calories, 1.5)

    score = 0
    
    # Protein scoring
    if 0.10 <= protein_ratio <= 0.35:
        score += 30
    else:
        score += max(0, 20 - abs(protein_ratio - 0.225) * 100)
        
    # Carb scoring
    if 0.45 <= carb_ratio <= 0.65:
        score += 30
    else:
        score += max(0, 20 - abs(carb_ratio - 0.55) * 100)
        
    # Fat scoring
    if 0.20 <= fat_ratio <= 0.35:
        score += 20
    else:
        score += max(0, 15 - abs(fat_ratio - 0.275) * 100)
        
    score += 20 * (1 - abs(calorie_ratio - 1.0))

    final_score = round(max(0, min(score, 100)), 2)
    
    # Determine Grade
    if final_score >= 90:
        grade = "A"
    elif final_score >= 75:
        grade = "B"
    elif final_score >= 60:
        grade = "C"
    elif final_score >= 40:
        grade = "D"
    else:
        grade = "F"
        
    return {
        "score": final_score,
        "grade": grade
    }

```

## filename: backend/food_data.py

```python
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Phase 2: Tamil Nadu Food Dataset (30+ Foods)
# Each entry requires nutrients per 100g, unit options, default weight, tags, and image URL.

TAMIL_NADU_FOODS = {
    # --- BREAKFAST FOODS ---
    "idli": {
        "name": "Idli",
        "calories_per_100g": 145,
        "protein_per_100g": 4.5,
        "carbs_per_100g": 30.0,
        "fat_per_100g": 0.4,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 40, "serving": 120},  # 3 pieces in a serving
        "tags": ["breakfast", "vegetarian", "steamed"],
        "image_url": "https://example.com/images/idli.jpg"
    },
    "dosa": {
        "name": "Dosa",
        "calories_per_100g": 168,
        "protein_per_100g": 3.9,
        "carbs_per_100g": 29.0,
        "fat_per_100g": 3.7,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 100, "serving": 100},
        "tags": ["breakfast", "vegetarian", "pan-fried"],
        "image_url": "https://example.com/images/dosa.jpg"
    },
    "vada": {
        "name": "Medu Vada",
        "calories_per_100g": 334,
        "protein_per_100g": 9.5,
        "carbs_per_100g": 43.0,
        "fat_per_100g": 14.0,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 45, "serving": 90},
        "tags": ["breakfast", "vegetarian", "fried"],
        "image_url": "https://example.com/images/vada.jpg"
    },
    "pongal": {
        "name": "Ven Pongal",
        "calories_per_100g": 212,
        "protein_per_100g": 5.0,
        "carbs_per_100g": 26.0,
        "fat_per_100g": 9.5,
        "units": ["grams", "cup", "serving"],
        "default_weight_g": {"cup": 200, "serving": 250},
        "tags": ["breakfast", "vegetarian", "rice"],
        "image_url": "https://example.com/images/pongal.jpg"
    },
    "upma": {
        "name": "Rava Upma",
        "calories_per_100g": 190,
        "protein_per_100g": 4.0,
        "carbs_per_100g": 28.0,
        "fat_per_100g": 6.5,
        "units": ["grams", "cup", "serving"],
        "default_weight_g": {"cup": 150, "serving": 200},
        "tags": ["breakfast", "vegetarian"],
        "image_url": "https://example.com/images/upma.jpg"
    },
    "appam": {
        "name": "Appam",
        "calories_per_100g": 180,
        "protein_per_100g": 3.0,
        "carbs_per_100g": 38.0,
        "fat_per_100g": 1.5,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 60, "serving": 120},
        "tags": ["breakfast", "vegetarian", "pancake"],
        "image_url": "https://example.com/images/appam.jpg"
    },
    "idiyappam": {
        "name": "Idiyappam",
        "calories_per_100g": 175,
        "protein_per_100g": 3.2,
        "carbs_per_100g": 39.0,
        "fat_per_100g": 0.5,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 50, "serving": 150},
        "tags": ["breakfast", "vegetarian", "steamed"],
        "image_url": "https://example.com/images/idiyappam.jpg"
    },
    "puttu": {
        "name": "Puttu",
        "calories_per_100g": 220,
        "protein_per_100g": 4.5,
        "carbs_per_100g": 45.0,
        "fat_per_100g": 2.0,
        "units": ["grams", "cup", "serving"],
        "default_weight_g": {"cup": 120, "serving": 150},
        "tags": ["breakfast", "vegetarian", "steamed"],
        "image_url": "https://example.com/images/puttu.jpg"
    },
    
    # --- RICE LUNCH / MEALS ---
    "white_rice": {
        "name": "White Rice (Boiled)",
        "calories_per_100g": 130,
        "protein_per_100g": 2.7,
        "carbs_per_100g": 28.0,
        "fat_per_100g": 0.3,
        "units": ["grams", "cup", "serving"],
        "default_weight_g": {"cup": 175, "serving": 200},
        "tags": ["lunch", "vegetarian", "staple"],
        "image_url": "https://example.com/images/white_rice.jpg"
    },
    "lemon_rice": {
        "name": "Lemon Rice",
        "calories_per_100g": 180,
        "protein_per_100g": 3.5,
        "carbs_per_100g": 30.0,
        "fat_per_100g": 5.0,
        "units": ["grams", "cup", "serving"],
        "default_weight_g": {"cup": 180, "serving": 250},
        "tags": ["lunch", "vegetarian", "rice"],
        "image_url": "https://example.com/images/lemon_rice.jpg"
    },
    "curd_rice": {
        "name": "Curd Rice",
        "calories_per_100g": 120,
        "protein_per_100g": 4.0,
        "carbs_per_100g": 18.0,
        "fat_per_100g": 3.5,
        "units": ["grams", "cup", "serving"],
        "default_weight_g": {"cup": 200, "serving": 250},
        "tags": ["lunch", "vegetarian", "rice"],
        "image_url": "https://example.com/images/curd_rice.jpg"
    },

    # --- CURRY / LENTILS ---
    "sambar": {
        "name": "Sambar",
        "calories_per_100g": 70,
        "protein_per_100g": 3.0,
        "carbs_per_100g": 10.0,
        "fat_per_100g": 2.0,
        "units": ["ml", "cup", "serving"],
        "default_weight_g": {"ml": 1, "cup": 240, "serving": 200},
        "tags": ["curry", "vegetarian", "lentils"],
        "image_url": "https://example.com/images/sambar.jpg"
    },
    "rasam": {
        "name": "Rasam",
        "calories_per_100g": 40,
        "protein_per_100g": 1.5,
        "carbs_per_100g": 6.0,
        "fat_per_100g": 1.0,
        "units": ["ml", "cup", "serving"],
        "default_weight_g": {"ml": 1, "cup": 240, "serving": 200},
        "tags": ["soup", "vegetarian"],
        "image_url": "https://example.com/images/rasam.jpg"
    },
    "poriyal": {
        "name": "Vegetable Poriyal",
        "calories_per_100g": 85,
        "protein_per_100g": 2.5,
        "carbs_per_100g": 9.0,
        "fat_per_100g": 4.5,
        "units": ["grams", "cup", "serving"],
        "default_weight_g": {"cup": 100, "serving": 150},
        "tags": ["side", "vegetarian", "vegetables"],
        "image_url": "https://example.com/images/poriyal.jpg"
    },

    # --- ANIMAL PROTEIN ---
    "chicken_chettinad": {
        "name": "Chicken Chettinad",
        "calories_per_100g": 190,
        "protein_per_100g": 14.0,
        "carbs_per_100g": 6.0,
        "fat_per_100g": 12.0,
        "units": ["grams", "serving", "cup"],
        "default_weight_g": {"cup": 200, "serving": 250},
        "tags": ["curry", "non-vegetarian", "protein"],
        "image_url": "https://example.com/images/chicken_chettinad.jpg"
    },
    "mutton_biryani": {
        "name": "Mutton Biryani",
        "calories_per_100g": 225,
        "protein_per_100g": 11.0,
        "carbs_per_100g": 24.0,
        "fat_per_100g": 9.5,
        "units": ["grams", "serving", "plate"],
        "default_weight_g": {"serving": 300, "plate": 400},
        "tags": ["lunch", "non-vegetarian", "rice", "protein"],
        "image_url": "https://example.com/images/mutton_biryani.jpg"
    },
    "fish_curry": {
        "name": "Meen Kuzhambu (Fish Curry)",
        "calories_per_100g": 140,
        "protein_per_100g": 12.0,
        "carbs_per_100g": 5.0,
        "fat_per_100g": 8.0,
        "units": ["grams", "serving", "cup"],
        "default_weight_g": {"cup": 220, "serving": 250},
        "tags": ["curry", "non-vegetarian", "protein"],
        "image_url": "https://example.com/images/fish_curry.jpg"
    },
    "egg_curry": {
        "name": "Egg Curry",
        "calories_per_100g": 155,
        "protein_per_100g": 8.0,
        "carbs_per_100g": 7.0,
        "fat_per_100g": 10.5,
        "units": ["grams", "serving", "cup"],
        "default_weight_g": {"cup": 200, "serving": 250},
        "tags": ["curry", "non-vegetarian", "protein"],
        "image_url": "https://example.com/images/egg_curry.jpg"
    },
    "boiled_egg": {
        "name": "Boiled Egg",
        "calories_per_100g": 155,
        "protein_per_100g": 13.0,
        "carbs_per_100g": 1.1,
        "fat_per_100g": 11.0,
        "units": ["piece", "grams"],
        "default_weight_g": {"piece": 55},
        "tags": ["protein", "non-vegetarian"],
        "image_url": "https://example.com/images/boiled_egg.jpg"
    },

    # --- DINNER / BREADS ---
    "parotta": {
        "name": "Parotta",
        "calories_per_100g": 320,
        "protein_per_100g": 7.0,
        "carbs_per_100g": 48.0,
        "fat_per_100g": 11.0,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 80, "serving": 160},
        "tags": ["dinner", "vegetarian", "bread"],
        "image_url": "https://example.com/images/parotta.jpg"
    },
    "chapati": {
        "name": "Chapati",
        "calories_per_100g": 297,
        "protein_per_100g": 9.0,
        "carbs_per_100g": 60.0,
        "fat_per_100g": 3.0,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 35, "serving": 70},
        "tags": ["dinner", "vegetarian", "bread"],
        "image_url": "https://example.com/images/chapati.jpg"
    },
    "poori": {
        "name": "Poori",
        "calories_per_100g": 320,
        "protein_per_100g": 7.0,
        "carbs_per_100g": 40.0,
        "fat_per_100g": 15.0,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 40, "serving": 120},
        "tags": ["breakfast", "vegetarian", "fried"],
        "image_url": "https://example.com/images/poori.jpg"
    },

    # --- STREET FOOD / SNACKS ---
    "kothu_parotta": {
        "name": "Kothu Parotta",
        "calories_per_100g": 260,
        "protein_per_100g": 9.0,
        "carbs_per_100g": 35.0,
        "fat_per_100g": 10.0,
        "units": ["grams", "serving", "plate"],
        "default_weight_g": {"serving": 250, "plate": 350},
        "tags": ["street-food", "dinner"],
        "image_url": "https://example.com/images/kothu_parotta.jpg"
    },
    "bajji": {
        "name": "Bajji (Plantain/Chili)",
        "calories_per_100g": 290,
        "protein_per_100g": 4.5,
        "carbs_per_100g": 35.0,
        "fat_per_100g": 15.0,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 50, "serving": 100},
        "tags": ["snack", "vegetarian", "fried"],
        "image_url": "https://example.com/images/bajji.jpg"
    },
    "bonda": {
        "name": "Aloo Bonda",
        "calories_per_100g": 270,
        "protein_per_100g": 4.0,
        "carbs_per_100g": 32.0,
        "fat_per_100g": 14.0,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 60, "serving": 120},
        "tags": ["snack", "vegetarian", "fried"],
        "image_url": "https://example.com/images/bonda.jpg"
    },
    "paniyaram": {
        "name": "Kuzhi Paniyaram",
        "calories_per_100g": 210,
        "protein_per_100g": 4.5,
        "carbs_per_100g": 32.0,
        "fat_per_100g": 7.0,
        "units": ["piece", "grams", "serving"],
        "default_weight_g": {"piece": 25, "serving": 125},  # 5 pieces per serving
        "tags": ["snack", "breakfast", "vegetarian"],
        "image_url": "https://example.com/images/paniyaram.jpg"
    },

    # --- BEVERAGES / DESSERTS ---
    "filter_coffee": {
        "name": "Filter Coffee (with milk & sugar)",
        "calories_per_100g": 60,
        "protein_per_100g": 1.5,
        "carbs_per_100g": 8.0,
        "fat_per_100g": 2.5,
        "units": ["ml", "cup", "glass"],
        "default_weight_g": {"ml": 1, "cup": 120, "glass": 150},
        "tags": ["beverage", "vegetarian"],
        "image_url": "https://example.com/images/filter_coffee.jpg"
    },
    "masala_chai": {
        "name": "Masala Chai",
        "calories_per_100g": 55,
        "protein_per_100g": 1.5,
        "carbs_per_100g": 7.5,
        "fat_per_100g": 2.0,
        "units": ["ml", "cup", "glass"],
        "default_weight_g": {"ml": 1, "cup": 120, "glass": 150},
        "tags": ["beverage", "vegetarian"],
        "image_url": "https://example.com/images/masala_chai.jpg"
    },
    "payasam": {
        "name": "Payasam",
        "calories_per_100g": 160,
        "protein_per_100g": 3.0,
        "carbs_per_100g": 25.0,
        "fat_per_100g": 5.5,
        "units": ["ml", "cup", "serving"],
        "default_weight_g": {"ml": 1, "cup": 150, "serving": 150},
        "tags": ["dessert", "vegetarian", "sweet"],
        "image_url": "https://example.com/images/payasam.jpg"
    },
    "kesari": {
        "name": "Rava Kesari",
        "calories_per_100g": 310,
        "protein_per_100g": 3.5,
        "carbs_per_100g": 48.0,
        "fat_per_100g": 11.5,
        "units": ["grams", "serving", "cup"],
        "default_weight_g": {"serving": 100, "cup": 150},
        "tags": ["dessert", "vegetarian", "sweet"],
        "image_url": "https://example.com/images/kesari.jpg"
    },
    
    # --- FRUITS / OTHERS ---
    "banana": {
        "name": "Banana",
        "calories_per_100g": 89,
        "protein_per_100g": 1.1,
        "carbs_per_100g": 22.8,
        "fat_per_100g": 0.3,
        "units": ["piece", "grams"],
        "default_weight_g": {"piece": 118},
        "tags": ["fruit", "snack", "vegan"],
        "image_url": "https://example.com/images/banana.jpg"
    },
    "curd": {
        "name": "Curd (Yogurt)",
        "calories_per_100g": 98,
        "protein_per_100g": 3.5,
        "carbs_per_100g": 4.3,
        "fat_per_100g": 4.3,
        "units": ["ml", "cup", "grams", "serving"],
        "default_weight_g": {"ml": 1, "cup": 240, "serving": 100},
        "tags": ["dairy", "vegetarian", "side"],
        "image_url": "https://example.com/images/curd.jpg"
    },
    "buttermilk": {
        "name": "Neer Mor (Spiced Buttermilk)",
        "calories_per_100g": 40,
        "protein_per_100g": 3.3,
        "carbs_per_100g": 4.8,
        "fat_per_100g": 0.9,
        "units": ["ml", "glass", "cup"],
        "default_weight_g": {"ml": 1, "glass": 250, "cup": 200},
        "tags": ["beverage", "dairy", "vegetarian"],
        "image_url": "https://example.com/images/buttermilk.jpg"
    }
}


class FoodDataManager:
    def __init__(self):
        self.local_db = TAMIL_NADU_FOODS
        self.cache = {}

    def search_food(self, query):
        """
        Hybrid lookup:
        1. Check memory cache
        2. Check local dataset (exact or partial match)
        3. Fallback to Open Food Facts API
        """
        query_lower = query.lower().strip()
        
        if query_lower in self.cache:
            return self.cache[query_lower]
        
        # 1. Local Search
        # Direct key match
        if query_lower in self.local_db:
            res = self._format_local_response(self.local_db[query_lower])
            self.cache[query_lower] = res
            return res
        
        # Partial match on name
        for key, food_item in self.local_db.items():
            if query_lower in food_item["name"].lower():
                res = self._format_local_response(food_item)
                self.cache[query_lower] = res
                return res
                
        # 2. API Fallback (Open Food Facts)
        logger.info(f"'{query}' not found in local DB. Calling Open Food Facts API...")
        res = self._fetch_from_api(query)
        self.cache[query_lower] = res
        return res

    def _format_local_response(self, food_item):
        return {
            "source": "local",
            "name": food_item["name"],
            "nutrition_per_100g": {
                "calories": food_item["calories_per_100g"],
                "protein_g": food_item["protein_per_100g"],
                "carbs_g": food_item["carbs_per_100g"],
                "fat_g": food_item["fat_per_100g"]
            },
            "units": food_item["units"],
            "default_weight_g": food_item["default_weight_g"],
            "tags": food_item["tags"],
            "image_url": food_item["image_url"],
            "error": None
        }

    def _fetch_from_api(self, query):
        def _safe_float(val):
            try:
                if val is None or str(val).strip() == "": return 0.0
                return float(val)
            except ValueError:
                return 0.0
                
        try:
            url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                "search_terms": query,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 1
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if "products" in data and len(data["products"]) > 0:
                product = data["products"][0]
                nutriments = product.get("nutriments", {})
                
                # Extract and normalize nutriments (default to 0 if missing)
                calories = nutriments.get("energy-kcal_100g", 0)
                protein = nutriments.get("proteins_100g", 0)
                carbs = nutriments.get("carbohydrates_100g", 0)
                fat = nutriments.get("fat_100g", 0)
                
                return {
                    "source": "api",
                    "name": product.get("product_name", query.capitalize()),
                    "nutrition_per_100g": {
                        "calories": _safe_float(calories),
                        "protein_g": _safe_float(protein),
                        "carbs_g": _safe_float(carbs),
                        "fat_g": _safe_float(fat)
                    },
                    # General defaults for API foods
                    "units": ["grams", "serving"],
                    "default_weight_g": {"serving": 100},
                    "tags": ["general"],
                    "image_url": product.get("image_url", "https://via.placeholder.com/150"),
                    "error": None
                }
            else:
                return {"error": "Food not found in local DB or API fallback."}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error: {e}")
            return {"error": f"API fallback failed: {str(e)}"}

# Test block
if __name__ == "__main__":
    manager = FoodDataManager()
    print("Testing Local Match (Idli):")
    print(json.dumps(manager.search_food("idli"), indent=2))
    
    print("\nTesting Partial Match (Biryani):")
    print(json.dumps(manager.search_food("biryani"), indent=2))
    
    print("\nTesting API Fallback (Oats):")
    print(json.dumps(manager.search_food("oats"), indent=2))

```

## filename: backend/firebase_service.py

```python
import firebase_admin
from firebase_admin import credentials, firestore
import threading
import logging
import datetime
from datetime import timezone

logger = logging.getLogger(__name__)

# Initialize Firebase (Requires a serviceAccountKey.json in the backend folder)
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase initialized successfully.")
except Exception as e:
    logger.warning(f"Firebase not initialized. Make sure serviceAccountKey.json exists. Error: {e}")
    db = None

class FirebaseService:
    @staticmethod
    def save_meal_async(user_id, meal_data):
        """
        Saves a meal to Firestore asynchronously to avoid blocking the API response.
        """
        if not db:
            logger.error("Cannot save meal: Firebase DB is not initialized.")
            return
            
        def _save():
            try:
                # 1. Save to 'meals' collection
                meal_ref = db.collection("meals").document()
                timestamp = datetime.datetime.now(timezone.utc)
                
                document_data = {
                    "user_id": user_id,
                    "timestamp": timestamp,
                    "foods": meal_data.get("foods", []),
                    "total_nutrients": meal_data.get("meal_summary", {}).get("total_nutrients", {}),
                    "health_score": meal_data.get("meal_summary", {}).get("health_score", {}),
                }
                meal_ref.set(document_data)
                logger.info(f"Meal saved successfully with ID: {meal_ref.id}")
                
                # 2. Update 'daily_summary'
                date_str = timestamp.strftime("%Y-%m-%d")
                summary_ref = db.collection("daily_summary").document(f"{user_id}_{date_str}")
                
                summary_doc = summary_ref.get()
                if summary_doc.exists:
                    # Append totals
                    current = summary_doc.to_dict()
                    updated_totals = {
                        "calories": current.get("calories", 0) + document_data["total_nutrients"].get("calories", 0),
                        "protein_g": current.get("protein_g", 0) + document_data["total_nutrients"].get("protein_g", 0),
                        "carbs_g": current.get("carbs_g", 0) + document_data["total_nutrients"].get("carbs_g", 0),
                        "fat_g": current.get("fat_g", 0) + document_data["total_nutrients"].get("fat_g", 0),
                    }
                    
                    # Store meal reference
                    meal_refs = current.get("meal_refs", [])
                    meal_refs.append(meal_ref.id)
                    
                    summary_ref.update({
                        "total_nutrients": updated_totals,
                        "meal_refs": meal_refs,
                        "last_updated": timestamp
                    })
                else:
                    # Create new daily summary
                    summary_ref.set({
                        "user_id": user_id,
                        "date": date_str,
                        "total_nutrients": document_data["total_nutrients"],
                        "meal_refs": [meal_ref.id],
                        "last_updated": timestamp
                    })
                logger.info(f"Daily summary updated for {date_str}")
                
            except Exception as e:
                logger.error(f"Error saving to Firebase: {e}")

        # Run in background thread
        thread = threading.Thread(target=_save)
        thread.start()

    @staticmethod
    def create_or_update_user(user_id, email, display_name, target_calories=2000):
        """
        Creates or updates a user profile.
        """
        if not db:
            return
            
        try:
            user_ref = db.collection("users").document(user_id)
            user_ref.set({
                "email": email,
                "display_name": display_name,
                "target_calories": target_calories,
                "last_login": datetime.datetime.now(timezone.utc)
            }, merge=True)
            logger.info(f"User {user_id} profile updated.")
        except Exception as e:
            logger.error(f"Error updating user: {e}")

```

## filename: backend/requirements.txt

```text
flask
flask-cors
firebase-admin
requests

```

## filename: frontend/package.json

```json
{
  "name": "nutrisense-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.6.0",
    "firebase": "^10.7.0",
    "lucide-react": "^0.300.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "recharts": "^2.10.3"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8"
  }
}

```

## filename: frontend/vite.config.js

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  }
})

```

## filename: frontend/index.html

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <title>NutriSense - Diet Analyzer</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>

```

## filename: frontend/src/main.jsx

```javascript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

```

## filename: frontend/src/App.jsx

```javascript
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

```

## filename: frontend/src/index.css

```css
:root {
  --color-green: #10b981;
  --color-yellow: #f59e0b;
  --color-red: #ef4444;
  --bg-color: #f8fafc;
  --card-bg: #ffffff;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --border-color: #e2e8f0;
  --primary: #3b82f6;
  --primary-hover: #2563eb;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', sans-serif;
  background-color: var(--bg-color);
  color: var(--text-main);
  -webkit-font-smoothing: antialiased;
}

/* Layout */
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

/* Navbar */
.navbar {
  background: var(--card-bg);
  padding: 1rem 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  text-decoration: none;
  color: var(--text-muted);
  font-weight: 500;
  transition: color 0.2s;
  padding: 0.5rem 0;
}

.nav-links a:hover, .nav-links a.active {
  color: var(--primary);
  border-bottom: 2px solid var(--primary);
  margin-bottom: -2px;
}

/* Card */
.card {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  margin-bottom: 1.5rem;
  border: 1px solid var(--border-color);
  transition: all 0.2s ease-in-out;
}

.card:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-main);
}

/* Grid & Layouts */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--bg-color);
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.form-row {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
}

/* Forms & Inputs */
.form-group {
  margin-bottom: 1rem;
  flex: 1;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--text-main);
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  font-family: inherit;
  font-size: 1rem;
}

.btn-primary {
  background-color: var(--primary);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: none;
}

.btn-primary:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background-color: #e2e8f0;
  color: var(--text-main);
}

.btn-secondary:hover {
  background-color: #cbd5e1;
}

/* Score Colors */
.score-green { color: var(--color-green); }
.score-yellow { color: var(--color-yellow); }
.score-red { color: var(--color-red); }

/* Alerts */
.alert {
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.alert-error {
  background-color: #fef2f2;
  color: #991b1b;
  border: 1px solid #f87171;
}

.alert-warning {
  background-color: #fffbeb;
  color: #92400e;
  border: 1px solid #fcd34d;
}

/* Skeleton Loading */
.skeleton {
  background: #e2e8f0;
  border-radius: 4px;
  animation: pulse 1.5s infinite ease-in-out;
}
.skeleton-text { height: 1rem; width: 100%; margin-bottom: 0.75rem; }
.skeleton-circle { height: 120px; width: 120px; border-radius: 50%; margin: 0 auto; }
.skeleton-block { height: 200px; width: 100%; border-radius: 8px; margin-bottom: 1rem; }

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

/* Animations */
.fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Responsiveness */
@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .form-row {
    flex-direction: column;
    align-items: stretch;
  }
  .stat-grid {
    grid-template-columns: 1fr 1fr;
  }
}

```

## filename: frontend/src/api/client.js

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const analyzeMeal = async (foods) => {
  try {
    const response = await api.post('/analyze-meal', { foods });
    return response.data;
  } catch (error) {
    if (error.response) {
      throw error.response.data;
    }
    throw { success: false, errors: ['Network error. Is the backend running?'] };
  }
};

export default api;

```

## filename: frontend/src/pages/Dashboard.jsx

```javascript
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

```

## filename: frontend/src/pages/AddMeal.jsx

```javascript
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

```

---

# ⚙️ SECTION 3 — REQUIREMENTS

## Python dependencies (requirements.txt)
```text
flask
flask-cors
firebase-admin
requests
```

## Node dependencies (package.json)
```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "firebase": "^10.7.0",
    "lucide-react": "^0.300.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "recharts": "^2.10.3"
  }
}
```

---

# 🔐 SECTION 4 — FIREBASE SETUP

1. **Create Firebase Project:** Go to the Firebase Console and create a new project.
2. **Enable Firestore:** Navigate to Firestore Database and click "Create Database".
3. **Enable Authentication:** Go to Authentication > Sign-in method, and enable Email/Password.
4. **Download serviceAccountKey.json:** Go to Project Settings > Service Accounts > Generate new private key.
5. **Place in backend/:** Save the downloaded JSON file as `backend/serviceAccountKey.json`.
6. **Add frontend firebase config:** Copy your web app config from Firebase settings and place it in `frontend/src/firebase_config.js`.

---

# 🚀 SECTION 5 — RUN INSTRUCTIONS

## Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

## Frontend
```bash
cd frontend
npm install
npm run dev
```

---

# 🧪 SECTION 6 — TESTING

Sample API request for `/analyze-meal`:

```json
{
  "foods": [
    {"food": "idli", "quantity": 3, "unit": "piece"},
    {"food": "sambar", "quantity": 1, "unit": "cup"}
  ]
}
```
