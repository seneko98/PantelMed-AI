from typing import Dict, List
import pymongo
import logging
import datetime
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class FormerUser:
    def __init__(self):
        # Підключення до MongoDB
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["pantelmed"]
        self.users = self.db["users"]
        self.interaction_limit = 40  # Початковий ліміт AI-запитів
        self.analysis_limit = 5  # Початковий ліміт аналізів (5 за 5 місяців)
        self.subscription_period = 150  # 5 місяців у днях
        self.monthly_reset = 30  # Днів у місяці

    def get_user_data(self, user_id: str) -> Dict:
        """Отримує всі дані користувача (аналізи, історія проблем, курси, цілі)."""
        user_data = self.users.find_one({"user_id": user_id})
        return user_data if user_data else {}

    def update_user_data(self, user_id: str, data: Dict):
        """Оновлює профіль користувача (вага, цілі, історія, платежі)."""
        current_data = self.get_user_data(user_id)
        history = current_data.get("history", [])
        query_interactions = [i for i in history if i.get("type") == "query"]
        if len(query_interactions) >= current_data.get("interaction_balance", self.interaction_limit) and data.get("history", [{}])[0].get("type") == "query":
            logger.warning(f"User {user_id} reached interaction limit")
            raise HTTPException(status_code=402, detail="Interaction limit exceeded. Upgrade your plan via /api/payments.")

        self.users.update_one(
            {"user_id": user_id},
            {"$set": data, "$push": {"history": data["history"][-1] if data.get("history") else {}}},
            upsert=True
        )
        logger.info(f"User {user_id} data updated: {data}")

    def add_problem(self, user_id: str, problem: str, date: str):
        """Додає проблему (наприклад, low_serotonin, high_hematocrit) до профілю."""
        current_data = self.get_user_data(user_id)
        problems = current_data.get("problems", [])
        if len(problems) >= 50:  # Ліміт проблем
            logger.warning(f"User {user_id} reached problem limit")
            raise HTTPException(status_code=402, detail="Problem limit exceeded. Upgrade your plan via /api/payments.")

        self.users.update_one(
            {"user_id": user_id},
            {"$push": {"problems": {"issue": problem, "date": date}}},
            upsert=True
        )
        logger.info(f"Problem {problem} added for user {user_id} on {date}")

    def add_analysis(self, user_id: str, analysis_type: str, value: float, date: str):
        """Додає результат аналізу (наприклад, testosterone: 300)."""
        current_data = self.get_user_data(user_id)
        analysis_count = current_data.get("analysis_count", 0)
        if analysis_count >= current_data.get("analysis_limit", self.analysis_limit):
            logger.warning(f"User {user_id} reached analysis limit")
            raise HTTPException(status_code=402, detail="Analysis limit exceeded. Upgrade your plan via /api/payments.")

        self.users.update_one(
            {"user_id": user_id},
            {"$push": {"analyses": {"type": analysis_type, "value": value, "date": date}}},
            upsert=True
        )
        self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"analysis_count": 1}},
            upsert=True
        )
        logger.info(f"Analysis {analysis_type}: {value} added for user {user_id} on {date}")

    def record_course(self, user_id: str, course_name: str, action: str, date: str = None):
        """Записує вибір або старт курсу."""
        if action not in ["select", "start"]:
            logger.error(f"Invalid action {action} for user {user_id}")
            raise HTTPException(status_code=400, detail="Invalid action: must be 'select' or 'start'")

        update_data = {}
        if action == "select":
            update_data = {"selected_course": course_name}
        elif action == "start":
            update_data = {
                "active_course": course_name,
                "course_start_date": date or datetime.datetime.utcnow().isoformat()
            }

        self.users.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )
        logger.info(f"Course {course_name} {action} recorded for user {user_id}")

        return {"message": f"Курс {course_name} {action} успішно записано."}

    def get_interaction_count(self, user_id: str) -> int:
        """Рахує кількість AI-взаємодій (тести/інтерпретація не рахуються)."""
        user_data = self.get_user_data(user_id)
        return len([i for i in user_data.get("history", []) if i.get("type") == "query"])

    def get_analysis_count(self, user_id: str) -> int:
        """Рахує кількість аналізів."""
        user_data = self.get_user_data(user_id)
        return user_data.get("analysis_count", 0)

    def reset_interaction_limit(self, user_id: str):
        """Скидає ліміт AI-запитів щомісяця, додаючи залишок."""
        user_data = self.get_user_data(user_id)
        current_interactions = self.get_interaction_count(user_id)
        subscription_end = user_data.get("subscription_end", datetime.datetime.utcnow().isoformat())
        months_passed = (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(user_data.get("subscription_start", datetime.datetime.utcnow().isoformat()))).days / self.monthly_reset

        # Залишок запитів додається до нового ліміту
        remaining = max(0, user_data.get("interaction_balance", self.interaction_limit) - current_interactions)
        new_limit = 15 if months_passed >= 1 else 40
        new_balance = remaining + new_limit

        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"interaction_balance": new_balance, "last_reset": datetime.datetime.utcnow().isoformat()}},
            upsert=True
        )
        logger.info(f"Interaction limit reset for user {user_id}: new balance {new_balance}")
