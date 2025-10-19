import json
from typing import Dict, Any, List
from fastapi import HTTPException
from former_user import FormerUser
from steroids import generate_hormone_recommendation
from pay import process_usdt_payment
import openai
from security_agent import SecurityAgent
from subscription_manager import SubscriptionManager
from logger_agent import LoggerAgent

class CosmetologyProtocol:
    def __init__(self, user_id: str):
        self.user_manager = FormerUser()
        self.security_agent = SecurityAgent()
        self.subscription_manager = SubscriptionManager()
        self.logger_agent = LoggerAgent()
        openai.api_key = "your-openai-api-key-here"
        
        # Перевірка безпеки та підписки
        self.security_agent.check_user(user_id)
        self.subscription_manager.check_interaction_limit(user_id)
        
        self.user_profile = self.user_manager.get_user_data(user_id)
        self.age = self.user_profile.get('age', 30)
        self.gender = self.user_profile.get('gender', 'male')
        self.skin_type = self.user_profile.get('skin_type', 'normal')
        self.aging_type = self.user_profile.get('aging_type', 'muscular')
        self.analyses = self.user_profile.get('analyses', [])
        self.face_type_results = self.run_face_type_test()
        self.protocol = self.generate_protocol()

    def run_face_type_test(self) -> Dict[str, Any]:
        return {
            'skin_type': self.skin_type,
            'aging_type': self.aging_type,
            'under_eye_issues': self.user_profile.get('under_eye_issues', {'dark_circles': False, 'puffiness': False}),
            'acne_prone': self.user_profile.get('acne_prone', False)
        }

    def check_hormone_correlation(self) -> List[str]:
        warnings = []
        for analysis in self.analyses:
            if analysis['type'] == 'estradiol' and analysis['value'] > 40:
                warnings.append("Високий естрадіол може спричиняти акне через надлишок себуму.")
            if analysis['type'] == 'dht' and analysis['value'] > 85:
                warnings.append("Високий DHT може посилювати акне через стимуляцію сальних залоз.")
        return warnings

    def generate_protocol(self) -> Dict[str, Any]:
        protocol = {
            'morning': self.get_morning_routine(),
            'evening': self.get_evening_routine(),
            'supplements': self.get_supplements(),
            'warnings': self.check_hormone_correlation(),
            'generated_at': datetime.datetime.utcnow().isoformat()
        }
        
        # Збереження протоколу в former_user
        self.user_manager.update_user_data(self.user_profile['user_id'], {
            "skin_care_protocol": protocol
        })
        self.logger_agent.log_request(self.user_profile['user_id'], "generate_protocol", 0)
        return protocol

    def get_morning_routine(self) -> List[str]:
        routine = [
            "Вмивання (гель або молочко без мила)",
            "Тонік або сироватка з вітаміном C",
            "Зволожуючий крем",
            "SPF 30-50"
        ]
        if self.face_type_results['acne_prone']:
            routine.insert(1, "Саліцилова кислота 2%")
        return routine

    def get_evening_routine(self) -> List[str]:
        routine = [
            "Вмивання",
            "Актив (ретинол, ніацинамід)",
            "Зволожуючий крем"
        ]
        if self.face_type_results['under_eye_issues']['dark_circles']:
            routine.append("Крем під очі з кофеїном")
        return routine

    def get_supplements(self) -> List[str]:
        supps = ['NAC 600мг (детокс)', 'Омега-3 1000мг (протизапально)', 'Пробіотики (Lactobacillus, для мікробіому)',
                 'Цинк 15-30мг (знижує 5α-редуктазу)', 'Віт.C 1г', 'Колаген 10г']
        if self.face_type_results['acne_prone']:
            supps.append('Розторопша/холін (підтримка печінки)')
        return supps

    def generate_ai_recommendations(self, prompt: str) -> str:
        """AI-рекомендації через OpenAI (заміна grok_api)."""
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500
        ).choices[0].text.strip()
        return response

def get_skin_protocol(user_id: str, payment_confirmed: bool = False) -> Dict:
    if not payment_confirmed:
        payment_status = process_usdt_payment(user_id, amount=10)
        if not payment_status:
            raise HTTPException(status_code=402, detail="Потрібна оплата через USDT.")
    protocol = CosmetologyProtocol(user_id)
    return protocol.protocol

if __name__ == "__main__":
    protocol = CosmetologyProtocol(user_id="test_user_1")
    protocol.save_protocol()
    print("Протокол згенеровано та збережено.")
