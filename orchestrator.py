from typing import Dict
import openai
from clinical_agent import ClinicalAgent
from steroids import SteroidAgent
from subscription_manager import SubscriptionManager
from logger_agent import LoggerAgent

class Orchestrator:
    def __init__(self):
        self.clinical_agent = ClinicalAgent()
        self.steroid_agent = SteroidAgent()
        self.subscription_manager = SubscriptionManager()
        self.logger_agent = LoggerAgent()

    def process(self, validated_input: Dict) -> str:
        """Обробляє валідований запит і повертає відповідь."""
        user_id = validated_input.get("user_id")
        if user_id:
            # Перевірка лімітів перед обробкою
            self.subscription_manager.check_interaction_limit(user_id)

        input_text = validated_input["text"]
        history = validated_input.get("history", [])

        # Визначаємо тип запиту
        if "курс" in input_text.lower() or "steroid" in input_text.lower():
            response = self.steroid_agent.get_recommendations(input_text)
        else:
            prompt = f"На основі історії {history}, дай рекомендацію для запиту: {input_text}"
            response = self.clinical_agent.analyze(prompt, history)

        # Логування запиту
        self.logger_agent.log_request(user_id or "anonymous", "orchestrator_process", self.logger_agent.token_usage_per_request)

        return response
