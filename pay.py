from fastapi import HTTPException
from pydantic import BaseModel
from subscription_manager import SubscriptionManager
from former_user import FormerUser
from logger_agent import LoggerAgent
import datetime
from typing import Dict, Optional
from bson import ObjectId

subscription_manager = SubscriptionManager()
former_user = FormerUser()
logger_agent = LoggerAgent()

# Конфігурація
TRON_WALLET = "TQeHa8VdwfyybxtioW4ggbnDC1rbWe8nFa"
MODULE_PRICE = 2.6  # USD (USDT) за пакет із 30 запитів/аналізів (тестовий режим)
PACKAGE_SIZE = 30  # Кількість запитів/аналізів у пакеті

class PaymentInput(BaseModel):
    user_id: str
    item: str  # "interaction", "analysis", "package", "module"
    item_id: Optional[str] = None  # ID пакета або модуля (наприклад, "analyzer")
    amount: int  # Кількість пакетів
    usdt_address: str  # Адреса для оплати USDT

class PaymentCheckInput(BaseModel):
    user_id: str
    payment_id: str  # ID платежу в MongoDB

async def create_payment(payment: PaymentInput) -> Dict:
    """Створює платіж для пакета або модуля (заглушка для onramper/TRON)."""
    if payment.item not in ["interaction", "analysis", "package", "module"]:
        raise HTTPException(status_code=400, detail="Invalid item: must be 'interaction', 'analysis', 'package', or 'module'")
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    user_data = former_user.get_user_data(payment.user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    # Визначаємо тип покупки
    item_name = payment.item
    amount_usdt = payment.amount * MODULE_PRICE
    if payment.item in ["package", "module"]:
        if not payment.item_id:
            raise HTTPException(status_code=400, detail="Потрібно вказати item_id для package або module")
        item_name = payment.item_id  # Наприклад, "analyzer" або "consultation"

    # Збереження платежу
    payment_data = {
        "user_id": payment.user_id,
        "item_type": payment.item,
        "item_id": payment.item_id or payment.item,
        "item_name": item_name,
        "amount": amount_usdt,
        "usdt_address": payment.usdt_address,
        "payment_method": "crypto",
        "status": "pending",
        "date": datetime.datetime.utcnow().isoformat()
    }
    payment_id = former_user.users.insert_one(payment_data).inserted_id
    logger_agent.log_request(payment.user_id, "create_payment", amount_usdt)

    return {
        "message": f"Payment of {amount_usdt} USDT for {payment.amount * PACKAGE_SIZE} {payment.item}(s) created",
        "payment_id": str(payment_id)
    }

async def check_payment_status(check: PaymentCheckInput) -> Dict:
    """Перевіряє статус платежу (заглушка для TRON)."""
    payment = former_user.users.find_one({"_id": ObjectId(check.payment_id), "user_id": check.user_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Платіж не знайдено")

    # Заглушка для перевірки TRON-транзакції
    payment_status = "pending"  # TODO: Реальна інтеграція з TRON
    if payment_status == "success":
        # Оновлення лімітів через subscription_manager
        if payment["item_type"] in ["interaction", "analysis"]:
            subscription_manager.update_limits(check.user_id, payment["item_type"], payment["amount"] * PACKAGE_SIZE)
        # Оновлення модулів/пакетів
        user_data = former_user.get_user_data(check.user_id)
        update_data = {"subscription_active": True}
        if payment["item_type"] == "package":
            # Заглушка: припускаємо, що пакет містить модулі
            update_data["active_modules"] = user_data.get("active_modules", []) + [payment["item_id"]]
        elif payment["item_type"] == "module":
            update_data["active_modules"] = user_data.get("active_modules", []) + [payment["item_id"]]
        
        former_user.update_user_data(check.user_id, update_data)
        former_user.users.update_one(
            {"_id": ObjectId(check.payment_id)},
            {"$set": {"status": "success"}}
        )
        logger_agent.log_subscription_event(check.user_id, "payment_success", f"Payment {check.payment_id} confirmed")

    return {
        "status": payment_status,
        "payment_id": check.payment_id,
        "item_name": payment["item_name"],
        "amount": payment["amount"],
        "subscription_active": payment_status == "success"
    }
