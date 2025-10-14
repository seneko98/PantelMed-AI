from typing import Dict
import datetime
import logging
from fastapi import HTTPException
from former_user import FormerUser

logger = logging.getLogger(__name__)

class SubscriptionManager:
    def __init__(self):
        self.former_user = FormerUser()
        self.interaction_limit = 40  # Початковий ліміт AI-запитів
        self.analysis_limit = 5  # Ліміт аналізів (5 за 5 місяців)
        self.subscription_period = 150  # 5 місяців у днях
        self.monthly_reset = 30  # Днів у місяці

    def check_interaction_limit(self, user_id: str) -> bool:
        """Перевіряє, чи не перевищено ліміт AI-запитів."""
        user_data = self.former_user.get_user_data(user_id)
        interactions = len([i for i in user_data.get("history", []) if i.get("type") == "query"])
        interaction_balance = user_data.get("interaction_balance", self.interaction_limit)
        if interactions >= interaction_balance:
            logger.warning(f"User {user_id} reached interaction limit")
            raise HTTPException(status_code=402, detail="Interaction limit exceeded. Upgrade your plan via /api/payments.")
        return True

    def check_analysis_limit(self, user_id: str) -> bool:
        """Перевіряє, чи не перевищено ліміт аналізів."""
        user_data = self.former_user.get_user_data(user_id)
        analysis_count = user_data.get("analysis_count", 0)
        analysis_limit = user_data.get("analysis_limit", self.analysis_limit)
        if analysis_count >= analysis_limit:
            logger.warning(f"User {user_id} reached analysis limit")
            raise HTTPException(status_code=402, detail="Analysis limit exceeded. Upgrade your plan via /api/payments.")
        return True

    def reset_interaction_limit(self, user_id: str):
        """Скидає ліміт AI-запитів щомісяця, додаючи залишок."""
        user_data = self.former_user.get_user_data(user_id)
        current_interactions = len([i for i in user_data.get("history", []) if i.get("type") == "query"])
        subscription_start = user_data.get("subscription_start", datetime.datetime.utcnow().isoformat())
        months_passed = (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(subscription_start)).days / self.monthly_reset

        # Залишок запитів додається до нового ліміту
        remaining = max(0, user_data.get("interaction_balance", self.interaction_limit) - current_interactions)
        new_limit = 15 if months_passed >= 1 else 40
        new_balance = remaining + new_limit

        self.former_user.update_user_data(user_id, {
            "interaction_balance": new_balance,
            "last_reset": datetime.datetime.utcnow().isoformat()
        })
        logger.info(f"Interaction limit reset for user {user_id}: new balance {new_balance}")

    def get_balance(self, user_id: str) -> Dict:
        """Повертає баланс запитів і аналізів."""
        user_data = self.former_user.get_user_data(user_id)
        interactions = len([i for i in user_data.get("history", []) if i.get("type") == "query"])
        analyses = user_data.get("analysis_count", 0)
        interaction_balance = user_data.get("interaction_balance", self.interaction_limit)
        analysis_limit = user_data.get("analysis_limit", self.analysis_limit)

        return {
            "interactions": {
                "used": interactions,
                "remaining": max(0, interaction_balance - interactions),
                "limit": interaction_balance
            },
            "analyses": {
                "used": analyses,
                "remaining": max(0, analysis_limit - analyses),
                "limit": analysis_limit
            }
        }

    def update_limits(self, user_id: str, item: str, amount: int):
        """Оновлює ліміти після покупки."""
        user_data = self.former_user.get_user_data(user_id)
        update_data = {}
        if item == "interaction":
            update_data["interaction_balance"] = user_data.get("interaction_balance", self.interaction_limit) + amount
        elif item == "analysis":
            update_data["analysis_limit"] = user_data.get("analysis_limit", self.analysis_limit) + amount
        self.former_user.update_user_data(user_id, update_data)
        logger.info(f"Updated {item} limit for user {user_id}: added {amount}")
