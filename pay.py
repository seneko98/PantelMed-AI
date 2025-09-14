from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from datetime import datetime
from typing import Dict, Optional
import logging
from db import Database
from bson import ObjectId

logger = logging.getLogger(__name__)

pay_bp = Blueprint('pay', __name__, url_prefix='/api/pay')

# Конфігурація
TRON_WALLET = "TQeHa8VdwfyybxtioW4ggbnDC1rbWe8nFa"
MODULE_PRICE = 2.6  # USD для всіх пакетів/модулів (тестовий режим)

@pay_bp.route('/create', methods=['POST'])
@cross_origin()
def create_payment():
    """Створення платежу для пакета або модуля"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        package_id = data.get("package_id")  # ID пакета з MongoDB
        module = data.get("module")  # Наприклад, 'analyzer', 'consultation'
        payment_method = data.get("payment_method")  # 'crypto' або 'cod' (Нова Пошта)
        contact_info = data.get("contact_info")  # Для Нової Пошти

        if not user_id:
            return jsonify({"error": "user_id обов'язковий"}), 400

        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
        
        # Перевірка, чи існує користувач
        user = db.find_document("users", {"telegram_id": user_id})
        if not user:
            return jsonify({"error": "Користувача не знайдено"}), 404

        # Визначаємо, що оплачуємо
        if package_id:
            package = db.find_document("packages", {"_id": ObjectId(package_id)})
            if not package:
                return jsonify({"error": "Пакет не знайдено"}), 404
            item_type = "package"
            item_id = package_id
            item_name = package["name"]
            amount = package.get("price", MODULE_PRICE)
        elif module:
            item_type = "module"
            item_id = module
            item_name = module
            amount = MODULE_PRICE
        else:
            return jsonify({"error": "Потрібно вказати package_id або module"}), 400

        # Створюємо платіж
        payment = {
            "user_id": user_id,
            "item_type": item_type,
            "item_id": item_id,
            "item_name": item_name,
            "amount": amount,
            "payment_method": payment_method,
            "contact_info": contact_info,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        payment_id = db.collections["payments"].insert_one(payment).inserted_id

        logger.info(f"Payment created: {payment_id} for user {user_id}, amount ${amount}")
        return jsonify({
            "status": "success",
            "payment_id": str(payment_id),
            "amount": amount,
            "payment_method": payment_method,
            "tron_wallet": TRON_WALLET if payment_method == "crypto" else None
        })

    except Exception as e:
        logger.error(f"Error in create_payment: {str(e)}")
        return jsonify({"error": f"Помилка при створенні платежу: {str(e)}"}), 500

@pay_bp.route('/status', methods=['GET'])
@cross_origin()
def check_payment_status():
    """Перевірка статусу платежу з видачею преміум-доступу"""
    try:
        payment_id = request.args.get("payment_id")
        if not payment_id:
            return jsonify({"error": "payment_id обов'язковий"}), 400

        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
        payment = db.find_document("payments", {"_id": ObjectId(payment_id)})

        if not payment:
            return jsonify({"error": "Платіж не знайдено"}), 404

        # Логіка перевірки крипто (заглушка, реалізуємо пізніше)
        if payment["payment_method"] == "crypto":
            # TODO: Перевірка транзакції в TRON
            payment_status = "pending"  # Заглушка
        else:
            payment_status = payment["status"]

        if payment_status == "success":
            user_id = payment["user_id"]
            # Оновлення преміум-доступу в user_profiles
            db.update_document("user_profiles", {"user_id": user_id}, {"$set": {"subscription_active": True}})
            # Оновлення модулів (як було)
            if payment["item_type"] == "package":
                db.collections["users"].update_one(
                    {"telegram_id": user_id},
                    {"$addToSet": {"active_modules": {"$each": db.find_document("packages", {"_id": ObjectId(payment["item_id"])})["modules"]}}}
                )
            else:
                db.collections["users"].update_one(
                    {"telegram_id": user_id},
                    {"$addToSet": {"active_modules": payment["item_id"]}}
                )

        return jsonify({
            "status": payment_status,
            "payment_id": str(payment_id),
            "item_name": payment["item_name"],
            "amount": payment["amount"],
            "subscription_active": payment_status == "success"
        })

    except Exception as e:
        logger.error(f"Error in check_payment_status: {str(e)}")
        return jsonify({"error": f"Помилка при перевірці статусу: {str(e)}"}), 500
