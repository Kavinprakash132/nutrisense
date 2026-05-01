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
