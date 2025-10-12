from typing import Dict
from fastapi import HTTPException
from former_user import FormerUser
import datetime
import logging

logger = logging.getLogger(__name__)

class SecurityAgent:
    def __init__(self):
        self.former_user = FormerUser()
        self.weight_change_limit = 6  # кг/місяць
        self.extreme_weight_limit = 10  # для 130+ кг
        self.goal_change_limit = 1  # Зміна цілей 1 раз на 2 місяці
        self.goal_change_period = 60  # 2 місяці в днях

    def check_user(self, user_id: str):
        """Перевіряє, чи не заблоковано профіль."""
        user_data = self.former_user.get_user_data(user_id)
        if user_data.get("profile_locked", False):
            logger.warning(f"User {user_id} profile locked: {user_data.get('lock_reason', 'Unknown reason')}")
            raise HTTPException(
                status_code=403,
                detail=f"Profile locked: {user_data.get('lock_reason', 'Unknown reason')}"
            )

    def check_weight(self, user_id: str, new_weight: float):
        """Перевіряє зміну ваги (з файлу безпека мулбти акк.txt)."""
        user_data = self.former_user.get_user_data(user_id)
        last_weight = user_data.get("last_weight", new_weight)
        weight_diff = abs(new_weight - last_weight)

        if user_data.get("weight", 0) > 130 and weight_diff > self.extreme_weight_limit:
            self.former_user.update_user_data(user_id, {
                "profile_locked": True,
                "lock_reason": "Extreme weight change detected",
                "suspicious_changes_count": user_data.get("suspicious_changes_count", 0) + 1
            })
            logger.warning(f"User {user_id} locked: Extreme weight change detected")
            raise HTTPException(
                status_code=403,
                detail="Підозрюю, що ви використовуєте один акаунт для двох людей. Це юридично некоректне використання платформи, що не відповідає нашій етиці. Створіть окремий акаунт."
            )
        elif weight_diff > self.weight_change_limit:
            self.former_user.update_user_data(user_id, {
                "profile_locked": True,
                "lock_reason": "Weight change exceeds limit",
                "suspicious_changes_count": user_data.get("suspicious_changes_count", 0) + 1,
                "lock_until": (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
            })
            logger.warning(f"User {user_id} locked: Weight change exceeds limit")
            raise HTTPException(
                status_code=403,
                detail="Підозрюю, що ви використовуєте один акаунт для двох людей. Це юридично некоректне використання платформи, що не відповідає нашій етиці. Створіть окремий акаунт."
            )

        self.former_user.update_user_data(user_id, {"last_weight": new_weight})
        return {"message": "Weight check passed"}

    def check_goal_change(self, user_id: str, new_goals: List[str]):
        """Перевіряє зміну цілей (1 раз на 2 місяці)."""
        user_data = self.former_user.get_user_data(user_id)
        last_goal_change = user_data.get("last_goal_change")
        goal_changes = user_data.get("goal_changes_count", 0)

        if last_goal_change:
            time_passed = (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(last_goal_change)).days
            if time_passed < self.goal_change_period and goal_changes >= self.goal_change_limit:
                self.former_user.update_user_data(user_id, {
                    "profile_locked": True,
                    "lock_reason": "Too many goal changes",
                    "suspicious_changes_count": user_data.get("suspicious_changes_count", 0) + 1,
                    "lock_until": (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
                })
                logger.warning(f"User {user_id} locked: Too many goal changes")
                raise HTTPException(
                    status_code=403,
                    detail="Підозрюю, що ви використовуєте один акаунт для двох людей. Це юридично некоректне використання платформи, що не відповідає нашій етиці. Створіть окремий акаунт."
                )

        self.former_user.update_user_data(user_id, {
            "last_goal_change": datetime.datetime.utcnow().isoformat(),
            "goal_changes_count": goal_changes + 1
        })
        return {"message": "Goal change check passed"}
