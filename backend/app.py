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
