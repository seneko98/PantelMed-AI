import json
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from former_user import FormerUser
from security_agent import SecurityAgent
from subscription_manager import SubscriptionManager
from logger_agent import LoggerAgent
import datetime

# ===========================================
# ПОВНА СИСТЕМА ЖІНОЧОГО ЗДОРОВ'Я (Python-порт з JS)
# Версія 3.0 - 3-бальна шкала, 7 модулів
# ===========================================

COMPLETE_WOMENS_HEALTH_SYSTEM = {
    "module_config": {
        "name": "complete_womens_health",
        "version": "3.0",
        "gender_restriction": "female_only",
        "requires_age": True,
        "scoring_system": "3_point_scale",
        "age_ranges": {
            "reproductive": "18-45",
            "perimenopause": "45-55",
            "postmenopause": "55+"
        },
        "languages": ["uk", "en"],
        "default_language": "uk"
    },

    # ===========================================
    # ОЦІНКА ЕСТРАДІОЛУ
    # ===========================================
    "estradiol_assessment": {
        "meta": {
            "name": "Естрадіол та естрогенний баланс",
            "emoji": "blooming_flower",
            "title": "ЕСТРАДІОЛ - основний жіночий гормон",
            "description": "регулює менструальний цикл, настрій, кісткову щільність, серцево-судинну систему",
            "dysfunction_effects": "може призводити до ПМС, нерегулярного циклу, набряків, емоційних коливань",
            "type": "female_hormone",
            "threshold": 3,
            "priority": "high"
        },
        "questions": {
            "primary": [
                {
                    "id": "est_p1",
                    "text": "Чи відчуваєте болючість або набряклість грудей перед місячними?",
                    "weight": 1.0,
                    "clinical_significance": "high",
                    "type": "multiple_choice",
                    "options": [
                        {"text": "Так, дуже болюче", "score": 2},
                        {"text": "Іноді, легке", "score": 1},
                        {"text": "Ні", "score": 0}
                    ]
                },
                {
                    "id": "est_p2",
                    "text": "Чи є у вас сильні перепади настрою перед місячними?",
                    "weight": 1.0,
                    "options": [
                        {"text": "Так, дуже сильні", "score": 2},
                        {"text": "Помірні", "score": 1},
                        {"text": "Ні", "score": 0}
                    ]
                },
                {
                    "id": "est_p3",
                    "text": "Чи є набряки ніг або рук перед місячними?",
                    "weight": 0.8,
                    "options": [
                        {"text": "Так, сильні", "score": 2},
                        {"text": "Легкі", "score": 1},
                        {"text": "Ні", "score": 0}
                    ]
                }
            ],
            "secondary": [
                {
                    "id": "est_s1",
                    "text": "Чи є у вас акне перед місячними?",
                    "weight": 0.7,
                    "options": [
                        {"text": "Так, сильне", "score": 2},
                        {"text": "Легке", "score": 1},
                        {"text": "Ні", "score": 0}
                    ]
                }
            ]
        }
    },

    # ===========================================
    # ПРОЛАКТИН
    # ===========================================
    "prolactin_assessment": {
        "meta": {
            "name": "Пролактин та лактація",
            "emoji": "droplet",
            "title": "ПРОЛАКТИН - гормон стресу та лактації",
            "threshold": 2
        },
        "questions": {
            "primary": [
                {
                    "id": "pro_p1",
                    "text": "Чи є у вас виділення з грудей (не під час годування)?",
                    "weight": 1.5,
                    "options": [
                        {"text": "Так, регулярно", "score": 2},
                        {"text": "Іноді", "score": 1},
                        {"text": "Ні", "score": 0}
                    ]
                }
            ]
        }
    },

    # ===========================================
    # СПКЯ
    # ===========================================
    "pcos_assessment": {
        "meta": {
            "name": "Синдром полікістозних яєчників",
            "emoji": "warning",
            "title": "СПКЯ - гормональний дисбаланс",
            "threshold": 4
        },
        "questions": {
            "primary": [
                {
                    "id": "pcos_p1",
                    "text": "Чи є у вас нерегулярний цикл (більше 35 днів)?",
                    "weight": 1.2,
                    "options": [{"text": "Так", "score": 2}, {"text": "Іноді", "score": 1}, {"text": "Ні", "score": 0}]
                },
                {
                    "id": "pcos_p2",
                    "text": "Чи є акне на обличчі/спині?",
                    "weight": 1.0,
                    "options": [{"text": "Так, сильне", "score": 2}, {"text": "Легке", "score": 1}, {"text": "Ні", "score": 0}]
                },
                {
                    "id": "pcos_p3",
                    "text": "Чи є зайвий ріст волосся на тілі (гірсутизм)?",
                    "weight": 1.3,
                    "options": [{"text": "Так", "score": 2}, {"text": "Ледь помітно", "score": 1}, {"text": "Ні", "score": 0}]
                }
            ]
        }
    },

    # ===========================================
    # КАНДИДОЗ
    # ===========================================
    "candidiasis_assessment": {
        "meta": {
            "name": "Кандидоз та мікробіом",
            "emoji": "microbe",
            "title": "КАНДИДОЗ - грибкова інфекція",
            "threshold": 3
        },
        "questions": {
            "primary": [
                {
                    "id": "cand_p1",
                    "text": "Чи є свербіж або печіння в інтимній зоні?",
                    "weight": 1.5,
                    "options": [{"text": "Так, часто", "score": 2}, {"text": "Іноді", "score": 1}, {"text": "Ні", "score": 0}]
                }
            ]
        }
    },

    # ===========================================
    # ВПЛ
    # ===========================================
    "hpv_assessment": {
        "meta": {
            "name": "ВПЛ та онкоскринінг",
            "emoji": "shield",
            "title": "ВПЛ - вірус папіломи",
            "threshold": 1
        },
        "questions": {
            "primary": [
                {
                    "id": "hpv_p1",
                    "text": "Чи робили ви ПАП-тест за останні 3 роки?",
                    "weight": 2.0,
                    "options": [{"text": "Ні", "score": 2}, {"text": "Так, норма", "score": 0}]
                }
            ]
        }
    },

    # ===========================================
    # ДІЄТИ ТА ТРЕНУВАННЯ
    # ===========================================
    "nutrition_training_system": {
        "nutrition": {
            "low_gi": ["кіноа", "гречка", "бобові", "ягоди"],
            "anti_inflammatory": ["куркума", "імбир", "зелень"],
            "hormone_balance": ["авокадо", "лосось", "горіхи"]
        },
        "training": {
            "hiit": "2 рази на тиждень, 20 хв",
            "yoga": "для гормонального балансу, 3 рази",
            "strength": "опорно-руховий апарат"
        }
    },

    # ===========================================
    # МАГАЗИН
    # ===========================================
    "shop_integration": {
        "recommended_items": [
            {"id": "vit_d", "name": "Вітамін D 2000 МО", "price": 15},
            {"id": "magnesium", "name": "Магній 400мг", "price": 12},
            {"id": "inositol", "name": "Інозитол 2г", "price": 25}
        ]
    },

    # ===========================================
    # РЕКОМЕНДАЦІЇ
    # ===========================================
    "recommendations": {
        "estradiol_assessment": [
            "Циклічна терапія прогестероном",
            "Вітамін E 400 МО",
            "Зменшити кофеїн"
        ],
        "pcos_assessment": [
            "Інозитол 2г/день",
            "Спіронолактон 25мг (за призначенням)",
            "Низький ГІ"
        ]
    }
}

class WomensHealthProtocol:
    def __init__(self, user_id: str):
        self.user_manager = FormerUser()
        self.security_agent = SecurityAgent()
        self.subscription_manager = SubscriptionManager()
        self.logger_agent = LoggerAgent()

        self.security_agent.check_user(user_id)
        self.subscription_manager.check_interaction_limit(user_id)

        self.user_profile = self.user_manager.get_user_data(user_id)

        if self.user_profile.get('gender') != 'female':
            raise HTTPException(status_code=403, detail="Розділ жіночого здоров'я доступний тільки для жінок.")

        self.config = COMPLETE_WOMENS_HEALTH_SYSTEM
        self.protocol = self.generate_protocol()

    def generate_protocol(self) -> Dict:
        protocol = {
            "estradiol": self.assess_module("estradiol_assessment"),
            "prolactin": self.assess_module("prolactin_assessment"),
            "pcos": self.assess_module("pcos_assessment"),
            "candidiasis": self.assess_module("candidiasis_assessment"),
            "hpv": self.assess_module("hpv_assessment"),
            "nutrition_training": self.config["nutrition_training_system"],
            "shop_recommendations": self.config["shop_integration"]["recommended_items"],
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "user_id": self.user_profile['user_id']
        }

        self.user_manager.update_user_data(self.user_profile['user_id'], {
            "womens_health_protocol": protocol
        })
        self.logger_agent.log_request(self.user_profile['user_id'], "generate_womens_health", 0)
        return protocol

    def assess_module(self, module_key: str) -> Dict:
        module = self.config.get(module_key, {})
        questions = module.get("questions", {})
        score = 0
        answered = []

        for section in questions.values():
            for q in section:
                user_answer = self.user_profile.get(q["id"])
                if user_answer is not None:
                    option = next((opt for opt in q["options"] if opt["text"] == user_answer), None)
                    if option:
                        score += option["score"] * q.get("weight", 1)
                        answered.append({"id": q["id"], "answer": user_answer, "score": option["score"]})

        meta = module.get("meta", {})
        return {
            "score": min(int(score), 10),
            "threshold": meta.get("threshold", 3),
            "risk_level": "high" if score >= meta.get("threshold", 3) else "low",
            "answered": answered,
            "recommendations": self.config["recommendations"].get(module_key, [])
        }

def get_womens_health_protocol(user_id: str) -> Dict:
    protocol = WomensHealthProtocol(user_id)
    return protocol.protocol

if __name__ == "__main__":
    # Тест
    test_user = {"user_id": "test_female_1", "gender": "female", "est_p1": "Так, дуже болюче", "pcos_p1": "Так"}
    # Симуляція former_user
    class MockFormerUser:
        def get_user_data(self, uid): return test_user
        def update_user_data(self, uid, data): print("Збережено:", data.keys())
    FormerUser.get_user_data = MockFormerUser().get_user_data
    FormerUser.update_user_data = MockFormerUser().update_user_data

    result = get_womens_health_protocol("test_female_1")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:500] + "...")
