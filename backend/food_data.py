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
                
        except requests.exceptions.Timeout as e:
            logger.error(f"API Timeout Error: {e}")
            return {"error": "External food API timed out. Please try again later."}
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
