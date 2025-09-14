from flask import Blueprint, request, jsonify 
from flask_cors import cross_origin
from datetime import datetime
from typing import Dict, Optional
import logging
from db import Database
from pay import process_payment  # Інтеграція з pay.py для USDT/Web3
from utils.telegram import send_telegram_notification
from utils.viber import send_viber_notification
from bson import ObjectId

logger = logging.getLogger(__name__)

shop_bp = Blueprint('shop', __name__, url_prefix='/api/shop')

# Конфігурація продуктів із категоріями та тестовими цінами
SHOP_PRODUCTS = {
    'zinc': {'name': 'Цинк Піколінат', 'price': 1.3, 'category': 'minerals', 'emoji': '🛡️'},
    'magnesium': {'name': 'Магній Хелат', 'price': 2.6, 'category': 'minerals', 'emoji': '⚡'},
    'ashwagandha': {'name': 'Ашваганда', 'price': 2.6, 'category': 'adaptogens', 'emoji': '🌱'},
    'niacinamide_serum': {'name': 'Сироватка з ніацинамідом', 'price': 2.6, 'category': 'skincare', 'emoji': '💧'},
    'retinol_serum': {'name': 'Сироватка з ретинолом', 'price': 2.6, 'category': 'antiaging', 'emoji': '⏳'},
    'vitamin_d': {'name': 'Вітамін D3', 'price': 1.3, 'category': 'vitamins', 'emoji': '☀️'},
    'dopa_mucuna': {'name': 'Допа мукуна', 'price': 2.6, 'category': 'nootropics', 'emoji': '🧠'}
}

@shop_bp.route('/cart', methods=['GET', 'POST'])
@cross_origin()
def manage_cart():
    """Керування кошиком (отримання/оновлення)"""
    try:
        user_id = request.args.get('user_id') if request.method == 'GET' else request.get_json().get('user_id')
        if not user_id:
            return jsonify({"error": "user_id обов'язковий"}), 400

        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
        user = db.find_document("users", {"telegram_id": user_id})
        if not user:
            return jsonify({"error": "Користувача не знайдено"}), 404

        if request.method == 'GET':
            cart = db.find_document("carts", {"user_id": user_id}) or {"items": [], "total": 0}
            db.insert_document("shop_transitions", {"user_id": user_id, "purch...(truncated 4616 characters)...          "items": order["items"],
            "total": order["total"],
            "contact_info": order["contact_info"],
            "created_at": order["created_at"].isoformat()
        })

    except Exception as e:
        logger.error(f"Error in order_status: {str(e)}")
        return jsonify({"error": f"Помилка при перевірці статусу: {str(e)}"}), 500

@shop_bp.route('/create_order', methods=['POST'])
@cross_origin()
def create_order():
    """Створення замовлення"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        cart_items = data.get('cart_items')
        contact_info = data.get('contact_info')

        if not user_id or not cart_items or not contact_info:
            return jsonify({"error": "Потрібні user_id, cart_items і contact_info"}), 400

        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
        user = db.find_document("users", {"telegram_id": user_id}) or db.find_document("users", {"viber_id": user_id})
        if not user:
            return jsonify({"error": "Користувача не знайдено"}), 404

        total = sum(SHOP_PRODUCTS[item['product_id']]['price'] * item['quantity'] for item in cart_items if item['product_id'] in SHOP_PRODUCTS)
        order = {
            "user_id": user_id,
            "items": cart_items,
            "total": total,
            "contact_info": contact_info,
            "created_at": datetime.utcnow(),
            "status": "pending"
        }
        order_id = db.insert_document("orders", order)

        # Тригер сповіщень
        if user.get('telegram_id'):
            send_telegram_notification(user['telegram_id'], f"Нове замовлення #{order_id}! Сума: {total} USDT")
        if user.get('viber_id'):
            send_viber_notification(user['viber_id'], f"Нове замовлення #{order_id}! Сума: {total} USDT")

        logger.info(f"Order created for user {user_id}, order_id: {order_id}")
        return jsonify({"status": "success", "order_id": str(order_id), "total": total})

    except Exception as e:
        logger.error(f"Error in create_order: {str(e)}")
        return jsonify({"error": f"Помилка при створенні замовлення: {str(e)}"}), 500

@shop_bp.route('/order_status/<order_id>', methods=['GET'])
@cross_origin()
def order_status(order_id):
    """Перевірка статусу замовлення"""
    try:
        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
        order = db.find_document("orders", {"_id": ObjectId(order_id)})
        if not order:
            return jsonify({"error": "Замовлення не знайдено"}), 404

        return jsonify({
            "status": order["status"],
            "items": order["items"],
            "total": order["total"],
            "contact_info": order["contact_info"],
            "created_at": order["created_at"].isoformat()
        })

    except Exception as e:
        logger.error(f"Error in order_status: {str(e)}")
        return jsonify({"error": f"Помилка при перевірці статусу: {str(e)}"}), 500

@shop_bp.route('/connect_messenger', methods=['POST'])
@cross_origin()
def connect_messenger():
    """Підключення месенджера (Telegram/Viber)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        messenger = data.get('messenger')  # 'telegram' або 'viber'
        messenger_id = data.get('messenger_id')

        if not user_id or not messenger or not messenger_id:
            return jsonify({"error": "Потрібні user_id, messenger і messenger_id"}), 400

        db = Database("mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0")
        user = db.find_document("users", {"telegram_id": user_id}) or db.find_document("users", {"viber_id": user_id})
        if not user:
            return jsonify({"error": "Користувача не знайдено"}), 404

        updates = {"updated_at": datetime.utcnow()}
        if messenger == 'telegram':
            updates['telegram_id'] = messenger_id
        elif messenger == 'viber':
            updates['viber_id'] = messenger_id
        db.update_document("users", {"telegram_id": user_id}, {"$set": updates})

        logger.info(f"Messenger {messenger} connected for user {user_id}")
        return jsonify({"status": "success", "message": f"Підключено {messenger} для {user_id}"})

    except Exception as e:
        logger.error(f"Error in connect_messenger: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@shop_bp.route('/products', methods=['GET'])
@cross_origin()
def get_products():
    """Отримання списку продуктів із фільтрами за категоріями"""
    try:
        category = request.args.get('category')
        products = SHOP_PRODUCTS.values()
        if category:
            products = [p for p in products if p['category'] == category]
        return jsonify({"products": list(products)})
    except Exception as e:
        logger.error(f"Error in get_products: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500
