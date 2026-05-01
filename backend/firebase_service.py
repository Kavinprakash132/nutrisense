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
