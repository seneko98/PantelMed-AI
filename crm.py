```python
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from datetime import datetime
from typing import Dict, List
import logging
from db import Database
from utils.telegram import send_telegram_notification
from utils.viber import send_viber_notification

logger = logging.getLogger(__name__)

crm_bp = Blueprint('crm', __name__, url_prefix='/api/crm')

ADMIN_PASSWORD = "pantelmed_admin_2024"

def require_admin(f):
    def wrapper(*args, **kwargs):
        password = request.args.get('password')
        if password != ADMIN_PASSWORD:
            return jsonify({"error": "Неправильний пароль"}), 401
        return f(*args, **kwargs)
    return wrapper

@crm_bp.route('/notifications', methods=['GET', 'POST'])
@cross_origin()
@require_admin
def manage_notifications():
    """Керування сповіщеннями (апка + шоп)"""
    try:
        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")

        if request.method == 'GET':
            notifications = list(db.collections["notifications"].find({}, {"_id": 0}).sort("created_at", -1).limit(50))
            return jsonify({"status": "success", "notifications": notifications})

        data = request.get_json()
        user_id = data.get("user_id")
        message = data.get("message")
        notification_type = data.get("type")  # order, payment, feedback

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

        # Надсилаємо сповіщення
        if user.get("telegram_id"):
            send_telegram_notification(user["telegram_id"], message)
        elif user.get("viber_id"):
            send_viber_notification(user["viber_id"], message)

        logger.info(f"Notification sent to user {user_id}: {message}")
        return jsonify({"status": "success", "message": "Сповіщення надіслано"})

    except Exception as e:
        logger.error(f"Error in manage_notifications: {str(e)}")
        return jsonify({"error": f"Помилка при роботі зі сповіщеннями: {str(e)}"}), 500

@crm_bp.route('/feedback', methods=['POST'])
@cross_origin()
def submit_feedback():
    """Фідбек від користувачів"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        feedback = data.get("feedback")
        order_id = data.get("order_id")

        if not user_id or not feedback:
            return jsonify({"error": "user_id і feedback обов'язкові"}), 400

        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
        user = db.find_document("users", {"telegram_id": user_id})
        if not user:
            return jsonify({"error": "Користувача не знайдено"}), 404

        feedback_data = {
            "user_id": user_id,
            "feedback": feedback,
            "order_id": order_id,
            "created_at": datetime.utcnow()
        }
        db.insert_document("feedback", feedback_data)

        # Сповіщення адміну
        admin_message = f"Новий фідбек від {user_id}: {feedback}"
        if order_id:
            admin_message += f" (Замовлення #{order_id})"
        send_telegram_notification("YOUR_ADMIN_ID", admin_message)

        logger.info(f"Feedback submitted by user {user_id}: {feedback}")
        return jsonify({"status": "success", "message": "Фідбек отримано"})

    except Exception as e:
        logger.error(f"Error in submit_feedback: {str(e)}")
        return jsonify({"error": f"Помилка при отриманні фідбеку: {str(e)}"}), 500

@crm_bp.route('/orders', methods=['GET'])
@cross_origin()
@require_admin
def list_orders():
    """Список замовлень (актуальні/відправлені)"""
    try:
        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
        orders = list(db.collections["orders"].find({}, {"_id": 0}).sort("created_at", -1))
        active_orders = [order for order in orders if order["status"] == "active"]
        shipped_orders = [order for order in orders if order["status"] == "shipped"]

        logger.info("Orders listed")
        return jsonify({"status": "success", "orders": orders, "active_orders": active_orders, "shipped_orders": shipped_orders})

    except Exception as e:
        logger.error(f"Error in list_orders: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@crm_bp.route('/shop_transitions', methods=['GET'])
@cross_origin()
@require_admin
def shop_transitions():
    """Статистика переходів у шоп"""
    try:
        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
        transitions = list(db.collections["shop_transitions"].find({}, {"_id": 0}).sort("created_at", -1))
        total_transitions = len(transitions)
        purchases = len([t for t in transitions if t["purchased"]])

        logger.info("Shop transitions stats generated")
        return jsonify({"status": "success", "total_transitions": total_transitions, "purchases": purchases, "conversion_rate": purchases / total_transitions * 100 if total_transitions > 0 else 0})

    except Exception as e:
        logger.error(f"Error in shop_transitions: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500
