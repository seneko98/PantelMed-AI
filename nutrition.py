from typing import Dict, List
from fastapi import HTTPException
from former_user import FormerUser
from security_agent import SecurityAgent
from subscription_manager import SubscriptionManager
from logger_agent import LoggerAgent
import datetime

class NutritionProtocol:
    def __init__(self, user_id: str):
        self.user_manager = FormerUser()
        self.security_agent = SecurityAgent()
        self.subscription_manager = SubscriptionManager()
        self.logger_agent = LoggerAgent()

        self.security_agent.check_user(user_id)
        self.subscription_manager.check_interaction_limit(user_id)

        self.user_profile = self.user_manager.get_user_data(user_id)
        self.goals = self.user_profile.get('goals', {})
        self.protocol = self.generate_protocol()

    def generate_protocol(self) -> Dict:
        goal = self.goals.get('primary', 'health')
        protocols = {
            'fat_loss': self.fat_loss_protocol(),
            'muscle_gain': self.muscle_gain_protocol(),
            'hormone_balance': self.hormone_protocol(),
            'health': self.general_health_protocol()
        }
        selected = protocols.get(goal, protocols['health'])

        self.user_manager.update_user_data(self.user_profile['user_id'], {
            "nutrition_protocol": selected
        })
        self.logger_agent.log_request(self.user_profile['user_id'], "generate_nutrition", 0)
        return selected

    def fat_loss_protocol(self) -> Dict:
        return {
            "diet": "Кето / Інтервальне голодування 16:8",
            "macros": "Жири 70%, Білок 25%, Вуглеводи 5%",
            "foods": ["Авокадо", "Лосос", "Яйця", "Горіхи"],
            "timing": "Останній прийом їжі — 19:00"
        }

    def muscle_gain_protocol(self) -> Dict:
        return {
            "diet": "Високобілкова",
            "macros": "Білок 2.2г/кг, Вуглеводи 4-6г/кг, Жири 1г/кг",
            "foods": ["Курка", "Рис", "Сир", "Банани"],
            "timing": "5-6 прийомів їжі"
        }

    def hormone_protocol(self) -> Dict:
        return {
            "diet": "Антизапальна",
            "macros": "Збалансована",
            "foods": ["Броколі", "Ягоди", "Куркума", "Зелений чай"],
            "avoid": ["Цукор", "Транжири", "Алкоголь"]
        }

    def general_health_protocol(self) -> Dict:
        return {
            "diet": "Средземноморська",
            "macros": "Збалансована",
            "foods": ["Риба", "Овочі", "Фрукти", "Цільнозернові"],
            "tip": "80% натуральних продуктів"
        }

def get_nutrition_protocol(user_id: str) -> Dict:
    protocol = NutritionProtocol(user_id)
    return protocol.protocol
