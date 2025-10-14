from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
from fastapi import HTTPException
from subscription_manager import SubscriptionManager
from former_user import FormerUser
from logger_agent import LoggerAgent
from security_agent import SecurityAgent
from assistant.steroids.questionnaire import SteroidQuestionnaire
from assistant.steroids.supplements import SupplementsDatabase, Supplement
from models.steroid_cycle import SteroidCycle, CycleStatus

class CycleGoal(Enum):
    BULKING = "bulking"
    CUTTING = "cutting"
    RECOMP = "recomp"
    STRENGTH = "strength"

@dataclass
class CycleRecommendation:
    cycle_name: str
    duration: str
    compounds: List[Dict]
    supplements: List[Supplement]
    cost_usd: float
    safety_rating: str
    match_percentage: float

class SteroidAgent:
    def __init__(self):
        self.questionnaire = SteroidQuestionnaire()
        self.supplements_db = SupplementsDatabase()
        self.former_user = FormerUser()
        self.subscription_manager = SubscriptionManager()
        self.logger_agent = LoggerAgent()
        self.security_agent = SecurityAgent()

    def get_recommendations(self, input_text: str, user_id: str = None) -> Dict:
        """Генерує рекомендації курсів на основі тексту або профілю."""
        if user_id:
            self.security_agent.check_user(user_id)
            self.subscription_manager.check_interaction_limit(user_id)

        user_data = self.former_user.get_user_data(user_id) if user_id else {}
        history = user_data.get("history", [])

        # Аналізуємо запит
        goal = self._parse_goal(input_text)
        recommendations = {
            "cycles": [],
            "supplements": [],
            "warnings": []
        }

        # Базові рекомендації курсів
        cycle_data = self._get_cycle_data(goal)
        for cycle in cycle_data:
            suitability = self._calculate_suitability(cycle, user_data)
            recommendations["cycles"].append(CycleRecommendation(
                cycle_name=cycle["name"],
                duration=cycle["duration"],
                compounds=cycle["compounds"],
                supplements=self.supplements_db.get_supplement_plan(cycle["category"]),
                cost_usd=cycle["cost_usd"],
                safety_rating=suitability["safety_rating"],
                match_percentage=suitability["match_percentage"]
            ).__dict__)

        # Додаємо БАДи
        recommendations["supplements"] = [
            supp.__dict__ for supp in self.supplements_db.get_supplement_by_purpose(goal.value if goal else "general_health")
        ]

        self.logger_agent.log_request(user_id or "anonymous", "steroid_recommendations", self.logger_agent.token_usage_per_request)
        return recommendations

    def start_course(self, user_id: str, cycle_name: str, supplements: List[str] = None) -> Dict:
        """Запускає курс і налаштовує сповіщення."""
        self.security_agent.check_user(user_id)
        self.subscription_manager.check_interaction_limit(user_id)

        user_data = self.former_user.get_user_data(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="Користувача не знайдено")

        # Збереження курсу
        self.former_user.record_course(user_id, cycle_name, "start")
        
        # Збереження стеку БАДів і розкладу сповіщень
        supplement_plan = self.supplements_db.get_supplement_plan("on_cycle") if not supplements else [
            self.supplements_db.supplements.get(supp_id) for supp_id in supplements
        ]
        self.former_user.update_user_data(user_id, {
            "active_supplements": [supp.__dict__ for supp in supplement_plan if supp],
            "notification_schedule": self._generate_notification_schedule(supplement_plan)
        })

        self.logger_agent.log_subscription_event(user_id, "start_course", f"Course {cycle_name} started with supplements")
        return {"message": f"Курс {cycle_name} розпочато, сповіщення налаштовано"}

    def start_supplement_stack(self, user_id: str, supplement_ids: List[str]) -> Dict:
        """Запускає стек БАДів і налаштовує сповіщення."""
        self.security_agent.check_user(user_id)
        self.subscription_manager.check_interaction_limit(user_id)

        user_data = self.former_user.get_user_data(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="Користувача не знайдено")

        supplement_plan = [self.supplements_db.supplements.get(supp_id) for supp_id in supplement_ids]
        if not all(supplement_plan):
            raise HTTPException(status_code=400, detail="Некоректні ID БАДів")

        self.former_user.update_user_data(user_id, {
            "active_supplements": [supp.__dict__ for supp in supplement_plan if supp],
            "notification_schedule": self._generate_notification_schedule(supplement_plan)
        })

        self.logger_agent.log_subscription_event(user_id, "start_supplement_stack", f"Supplement stack started: {supplement_ids}")
        return {"message": f"Стек БАДів розпочато, сповіщення налаштовано"}

    def _parse_goal(self, input_text: str) -> Optional[CycleGoal]:
        """Визначає ціль із тексту запиту."""
        input_text = input_text.lower()
        if "масса" in input_text or "bulking" in input_text:
            return CycleGoal.BULKING
        elif "сушка" in input_text or "cutting" in input_text:
            return CycleGoal.CUTTING
        elif "рекомп" in input_text or "recomp" in input_text:
            return CycleGoal.RECOMP
        elif "сила" in input_text or "strength" in input_text:
            return CycleGoal.STRENGTH
        return None

    def _get_cycle_data(self, goal: Optional[CycleGoal]) -> List[Dict]:
        """Повертає дані курсів за ціллю (заглушка)."""
        cycles = [
            {
                "name": "Beginner Bulking",
                "duration": "8 weeks",
                "compounds": [{"name": "Testosterone Enanthate", "dose": "300mg/week"}],
                "category": "short_cycles",
                "cost_usd": 100.0
            },
            {
                "name": "Intermediate Cutting",
                "duration": "12 weeks",
                "compounds": [{"name": "Testosterone Propionate", "dose": "100mg/EOD"}],
                "category": "medium_cycles",
                "cost_usd": 150.0
            }
        ]
        return [c for c in cycles if not goal or c["category"] == goal.value]

    def _calculate_suitability(self, cycle: Dict, user_data: Dict) -> Dict:
        """Розраховує придатність курсу."""
        return {
            "overall_score": 7,
            "safety_rating": "medium",
            "match_percentage": 75.0,
            "concerns": [],
            "benefits": ["Відповідає рівню досвіду"]
        }

    def _generate_notification_schedule(self, supplements: List[Supplement]) -> List[Dict]:
        """Генерує розклад сповіщень для Telegram."""
        schedule = []
        for supp in supplements:
            if supp:
                schedule.append({
                    "supplement_name": supp.name,
                    "timing": supp.timing.value,
                    "dosage": supp.dosage,
                    "time": "08:00" if supp.timing == "morning" else "20:00"
                })
        return schedule
