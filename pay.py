from fastapi import HTTPException
from pydantic import BaseModel
from subscription_manager import SubscriptionManager
from former_user import FormerUser
from logger_agent import LoggerAgent
import datetime
from typing import Dict, Optional
from bson import ObjectId
import uuid

subscription_manager = SubscriptionManager()
former_user = FormerUser()
logger_agent = LoggerAgent()

# Конфігурація
TRON_WALLET = "TQeHa8VdwfyybxtioW4ggbnDC1rbWe8nFa"
MODULE_PRICE = 2.6  # USD (USDT) за пакет із 30 запитів/аналізів (тестовий режим)
PACKAGE_SIZE = 30  # Кількість запитів/аналізів у пакеті

class PaymentProcessor:
    def __init__(self):
        self.provider = "onramper"  # Замінити на реальний провайдер
        self.network = "Ethereum"  # Мережа для USDT (може бути Tron)

    async def create_payment(self, user_id: str, item: str, item_id: Optional[str], amount: int, usdt_address: str) -> Dict:
        """Створення платежу в USDT."""
        try:
            payment_id = str(uuid.uuid4())
            # Симуляція запиту до Web3-провайдера
            payment_data = {
                "payment_id": payment_id,
                "user_id": user_id,
                "item": item,
                "item_id": item_id or item,
                "amount": amount,
                "usdt_address": usdt_address,
                "status": "pending",
                "created_at": datetime.datetime.utcnow().isoformat(),
                "provider": self.provider,
                "network": self.network
            }
            # Логіка для onramper/guardian API (додати реальний виклик)
            print(f"Simulating payment creation: {payment_data}")

            # Збереження в MongoDB (з pay (4).py)
            former_user.users.insert_one(payment_data)
            logger_agent.log_request(user_id, "create_payment", amount * MODULE_PRICE)

            return {"status": "success", "payment_id": payment_id, "details": payment_data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")

    async def check_payment_status(self, payment_id: str, user_id: str) -> Dict:
        """Перевірка статусу платежу."""
        try:
            payment = former_user.users.find_one({"_id": ObjectId(payment_id), "user_id": user_id})
            if not payment:
                raise HTTPException(status_code=404, detail="Платіж не знайдено")

            # Заглушка для перевірки TRON-транзакції
            payment_status = "pending"  # TODO: Реальна інтеграція з TRON
            if payment_status == "success":
                # Оновлення лімітів через subscription_manager
                if payment["item"] in ["interaction", "analysis"]:
                    subscription_manager.update_limits(user_id, payment["item"], payment["amount"] * PACKAGE_SIZE)
                # Оновлення модулів/пакетів (з pay (4).py)
                user_data = former_user.get_user_data(user_id)
                update_data = {"subscription_active": True}
                if payment["item"] == "package":
                    update_data["active_modules"] = user_data.get("active_modules", []) + [payment["item_id"]]
                elif payment["item"] == "module":
                    update_data["active_modules"] = user_data.get("active_modules", []) + [payment["item_id"]]
                
                former_user.update_user_data(user_id, update_data)
                former_user.users.update_one(
                    {"_id": ObjectId(payment_id)},
                    {"$set": {"status": "success"}}
                )
                logger_agent.log_subscription_event(user_id, "payment_success", f"Payment {payment_id} confirmed")

            return {
                "status": payment_status,
                "payment_id": payment_id,
                "item_name": payment["item"],
                "amount": payment["amount"],
                "subscription_active": payment_status == "success"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Payment status check failed: {str(e)}")
