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

handlers_bp = Blueprint('handlers', __name__)
logger = logging.getLogger(__name__)

# Конфігурація
db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
openai_client = OpenAI(api_key="your_api_key_here")  # Placeholder
medical_knowledge = MedicalCore

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

        # AI-аналіз через GPT-4o Mini
        prompt = f"Аналізуй медичні дані: {normalized_results}. Використовуй базу: {medical_knowledge.supplements_database}. Дай рекомендації."
        response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        ai_recommendations = response.choices[0].message.content

        db.insert_document("lab_results", {
            "user_id": user_id,
            "results": normalized_results,
            "interpretation": interpretation,
            "ai_recommendations": ai_recommendations,
            "created_at": datetime.utcnow()
        })

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "results": normalized_results,
            "interpretation": interpretation,
            "ai_recommendations": ai_recommendations
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
        channel = data.get('channel', 'telegram')  # За замовчуванням Telegram

        if not user_id or not message:
            return jsonify({"error": "Потрібні user_id і message"}), 400

        if channel == 'telegram':
            send_telegram_notification(user_id, message)
        elif channel == 'viber':
            send_viber_notification(user_id, message)
        else:
            return jsonify({"error": "Непідтримуваний канал"}), 400

        db.insert_document("notifications", {
            "user_id": user_id,
            "type": "notification",
            "message": message,
            "channel": channel,
            "created_at": datetime.utcnow()
        })

        return jsonify({"status": "success", "message": "Сповіщення відправлено"})

    except Exception as e:
        logger.error(f"Error in send_notification: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@handlers_bp.route('/api/handlers/subscription_check', methods=['POST'])
def subscription_check():
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "Потрібен user_id"}), 400

        subscription = db.find_document("users", {"user_id": user_id, "subscription_active": True})
        is_active = bool(subscription)

        return jsonify({"status": "success", "user_id": user_id, "subscription_active": is_active})

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
            return jsonify({"error": "Потрібен user_id"}), 400

        user_profile = db.find_document("user_profiles", {"user_id": user_id})
        gender = user_profile.get("gender", "unknown") if user_profile else "unknown"

        if gender not in ["female", "unknown"]:
            return jsonify({"error": "Тільки для жінок або невідомої статі"}), 403

        lab_results = db.find_document("lab_results", {"user_id": user_id})
        results = lab_results.get("results", {}) if lab_results else {}

        # Жіночі + загальні рекомендації
        womens_knowledge = medical_knowledge.womens_health
        general_knowledge = {k: v for k, v in medical_knowledge.supplements_database.items() if k not in womens_knowledge}
        prompt = f"Консультація для жінки {user_id}. Аналізи: {results}. Запит: {query}. Використовуй жіночі дані: {womens_knowledge} і загальні: {general_knowledge}. Дай рекомендації."
        response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        answer = response.choices[0].message.content

        return jsonify({"status": "success", "user_id": user_id, "query": query, "answer": answer})

    except Exception as e:
        logger.error(f"Error in womens_health: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500
