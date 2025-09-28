from flask import Blueprint, jsonify, request
from db import Database
from blood_interpreter import interpret_lab_results
from medical_knowledge import MedicalCore
from utils.telegram import send_telegram_notification
from utils.viber import send_viber_notification
from openai import OpenAI
import logging
from datetime import datetime
from bson import ObjectId
from ai_recommendations import AIRecommendations

handlers_bp = Blueprint('handlers', __name__)
logger = logging.getLogger(__name__)

# Конфігурація
db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
openai_client = OpenAI(api_key="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")  
medical_knowledge = MedicalCore
ai_recommendations = AIRecommendations(openai_client.api_key)  # Інтеграція AI

@handlers_bp.route('/api/handlers/analyze_results', methods=['POST'])
def analyze_results():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        results = data.get('results')

        if not user_id or not results:
            return jsonify({"error": "Потрібні user_id і results"}), 400

        # Нормалізація даних
        normalized_results = {}
        for test_name, value_data in results.items():
            if isinstance(value_data, dict) and "value" in value_data and "unit" in value_data:
                normalized_results[test_name] = value_data
            else:
                normalized_results[test_name] = {"value": float(value_data), "unit": "г/л"}

        # Інтерпретація через blood_interpreter
        interpretation = interpret_lab_results(normalized_results)

        # AI-аналіз через GPT-4o Mini з інтеграцією ai_recommendations
        recommendations = ai_recommendations.get_recommendations(normalized_results)

        db.insert_document("lab_results", {
            "user_id": user_id,
            "results": normalized_results,
            "interpretation": interpretation,
            "ai_recommendations": recommendations,
            "created_at": datetime.utcnow()
        })

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "results": normalized_results,
            "interpretation": interpretation,
            "ai_recommendations": recommendations
        })

    except Exception as e:
        logger.error(f"Error in analyze_results: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@handlers_bp.route('/api/handlers/send_notification', methods=['POST'])
def send_notification():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        message = data.get('message')
        notification_type = data.get('type')  # order, payment, feedback

        if not user_id or not message or not notification_type:
            return jsonify({"error": "user_id, message і type обов'язкові"}), 400

        user = db.find_document("users", {"telegram_id": user_id})
        if not user:
            return jsonify({"error": "Користувача не знайдено"}), 404

        notification = {
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "created_at": datetime.utcnow()
        }
        db.insert_document("notifications", notification)

        # Надсилання сповіщення
        if user.get("telegram_id"):
            send_telegram_notification(user["telegram_id"], message)
        if user.get("viber_id"):
            send_viber_notification(user["viber_id"], message)

        logger.info(f"Notification sent to user {user_id}: {message}")
        return jsonify({"status": "success", "message": "Сповіщення надіслано"})

    except Exception as e:
        logger.error(f"Error in send_notification: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@handlers_bp.route('/api/handlers/subscription_check', methods=['POST'])
def subscription_check():
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "user_id обов'язковий"}), 400

        subscription = db.find_document("user_profiles", {"user_id": user_id, "subscription_active": True})
        is_active = bool(subscription)

        return jsonify({"status": "success", "subscription_active": is_active})

    except Exception as e:
        logger.error(f"Error in subscription_check: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@handlers_bp.route('/api/handlers/womens_health', methods=['POST'])
def womens_health():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        query = data.get('query', 'рекомендації для жінок')

        if not user_id:
            return jsonify({"error": "user_id обов'язковий"}), 400

        user_profile = db.find_document("user_profiles", {"user_id": user_id})
        gender = user_profile.get("gender", "unknown") if user_profile else "unknown"

        if gender not in ["female", "unknown"]:
            return jsonify({"error": "Тільки для жінок або невідомої статі"}), 403

        lab_results = db.find_document("lab_results", {"user_id": user_id})
        results = lab_results.get("results", {}) if lab_results else {}

        # Жіночі + загальні рекомендації з AI
        womens_knowledge = medical_knowledge.womens_health
        general_knowledge = {k: v for k, v in medical_knowledge.supplements_database.items() if k not in womens_knowledge}
        prompt = f"Консультація для жінки {user_id}. Аналізи: {results}. Запит: {query}. Використовуй жіночі дані: {womens_knowledge} і загальні: {general_knowledge}. Дай рекомендації."
        response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        answer = response.choices[0].message.content

        # Додати AI-рекомендації
        recommendations = ai_recommendations.get_recommendations(results)

        return jsonify({"status": "success", "user_id": user_id, "query": query, "answer": answer, "ai_recommendations": recommendations})

    except Exception as e:
        logger.error(f"Error in womens_health: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500
