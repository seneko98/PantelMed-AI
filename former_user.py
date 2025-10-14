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

    def get_user_data(self, user_id: str) -> Dict:
        """Отримує всі дані користувача (аналізи, історія проблем, курси, цілі)."""
        user_data = self.users.find_one({"user_id": user_id})
        return user_data if user_data else {}

    def update_user_data(self, user_id: str, data: Dict):
        """Оновлює профіль користувача (вага, цілі, історія, платежі, стеки)."""
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

    def record_supplement_stack(self, user_id: str, supplements: List[Dict], schedule: List[Dict]):
        """Зберігає стек БАДів і розклад сповіщень."""
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "active_supplements": supplements,
                "notification_schedule": schedule
            }},
            upsert=True
        )
        logger.info(f"Supplement stack and schedule recorded for user {user_id}")

    def get_interaction_count(self, user_id: str) -> int:
        """Рахує кількість AI-взаємодій (тести/інтерпретація не рахуються)."""
        user_data = self.get_user_data(user_id)
        return len([i for i in user_data.get("history", []) if i.get("type") == "query"])

    def get_analysis_count(self, user_id: str) -> int:
        """Рахує кількість аналізів."""
        user_data = self.get_user_data(user_id)
        return user_data.get("analysis_count", 0)
