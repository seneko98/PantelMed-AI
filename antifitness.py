import json
from typing import Dict, Any, List
from fastapi import HTTPException
from former_user import FormerUser
from security_agent import SecurityAgent
from subscription_manager import SubscriptionManager
from logger_agent import LoggerAgent
from pay import process_usdt_payment
import datetime

class AntiFitnessProtocol:
    def __init__(self, user_id: str):
        self.user_manager = FormerUser()
        self.security_agent = SecurityAgent()
        self.subscription_manager = SubscriptionManager()
        self.logger_agent = LoggerAgent()

        # Безпека + підписка
        self.security_agent.check_user(user_id)
        self.subscription_manager.check_interaction_limit(user_id)

        self.user_profile = self.user_manager.get_user_data(user_id)
        self.stress_level = self.user_profile.get('stress_level', 'medium')
        self.sleep_quality = self.user_profile.get('sleep_quality', '6-7 годин')
        self.recovery_needs = self.user_profile.get('recovery_needs', [])
        self.goals = self.user_profile.get('goals', {})
        self.protocol = self.generate_protocol()

    def analyze_recovery_needs(self) -> List[str]:
        """Аналіз потреб у відновленні на основі профілю."""
        needs = []
        if self.stress_level in ['high', 'very high']:
            needs.append("Стрес-менеджмент")
        if 'poor' in self.sleep_quality:
            needs.append("Покращення сну")
        if 'overtraining' in self.recovery_needs:
            needs.append("Відновлення після тренувань")
        if 'mental_fatigue' in self.recovery_needs:
            needs.append("Ментальне відновлення")
        return needs

    def generate_protocol(self) -> Dict[str, Any]:
        needs = self.analyze_recovery_needs()
        protocol = {
            "daily_routine": self.get_daily_routine(needs),
            "weekly_practices": self.get_weekly_practices(needs),
            "breathing_exercises": self.get_breathing_exercises(),
            "meditation": self.get_meditation_plan(),
            "cold_therapy": self.get_cold_therapy(),
            "sauna": self.get_sauna_protocol(),
            "supplements": self.get_supplements(),
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "user_id": self.user_profile['user_id']
        }

        # Збереження в former_user
        self.user_manager.update_user_data(self.user_profile['user_id'], {
            "antifitness_protocol": protocol
        })
        self.logger_agent.log_request(self.user_profile['user_id'], "generate_antifitness_protocol", 0)
        return protocol

    def get_daily_routine(self, needs: List[str]) -> List[str]:
        routine = ["Ранкова дихальна гімнастика (4-7-8)", "10 хв прогулянки на природі"]
        if "Стрес-менеджмент" in needs:
            routine.append("Вечірній ритуал: чай з мелісою + journaling")
        return routine

    def get_weekly_practices(self, needs: List[str]) -> Dict[str, str]:
        practices = {
            "Понеділок": "Йога для хребта (30 хв)",
            "Середа": "Пілатес core (20 хв)",
            "П’ятниця": "Розтяжка + foam roller"
        }
        if "Відновлення після тренувань" in needs:
            practices["Неділя"] = "Легка йога + медитація"
        return practices

    def get_breathing_exercises(self) -> List[Dict]:
        return [
            {"name": "4-7-8", "description": "Вдих 4с, затримка 7с, видих 8с", "when": "Перед сном"},
            {"name": "Box Breathing", "description": "4-4-4-4", "when": "При стресі"}
        ]

    def get_meditation_plan(self) -> Dict:
        return {
            "type": "Mindfulness",
            "duration": "10 хв щодня",
            "app": "Headspace / Insight Timer",
            "focus": "Сканування тіла"
        }

    def get_cold_therapy(self) -> Dict:
        return {
            "method": "Холодний душ",
            "protocol": "30 сек холод → 1 хв тепло → повторити 3 рази",
            "frequency": "3-5 разів на тиждень"
        }

    def get_sauna_protocol(self) -> Dict:
        return {
            "temperature": "70-80°C",
            "duration": "15-20 хв",
            "frequency": "1-2 рази на тиждень",
            "hydration": "1 л води до + після"
        }

    def get_supplements(self) -> List[str]:
        base = ['Магній 400мг (вечір)', 'Ашваганда 300мг', 'L-теанін 200мг']
        if self.stress_level == 'very high':
            base.append('Родіола 200мг (ранок)')
        return base

def get_antifitness_protocol(user_id: str, payment_confirmed: bool = False) -> Dict:
    """Ендпоінт-функція для FastAPI."""
    if not payment_confirmed:
        # Преміум-протокол — 5 USDT
        payment_status = process_usdt_payment(user_id, amount=5)
        if not payment_status:
            raise HTTPException(status_code=402, detail="Потрібна оплата 5 USDT для преміум антифітнес-протоколу.")
    
    protocol = AntiFitnessProtocol(user_id)
    return protocol.protocol

if __name__ == "__main__":
    # Тест
    test_protocol = AntiFitnessProtocol("test_user_1")
    print(json.dumps(test_protocol.protocol, ensure_ascii=False, indent=2))
