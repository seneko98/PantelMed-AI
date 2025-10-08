import json
import os
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class IGF1ProtocolHandler:
    def __init__(self):
        self.data_dir = "data/igf1"
        self.protocol = {
            "meta": {
                "title": "Протокол IGF-1 та HGH для PantelMed",
                "description": "Превентивний біохакінг для регенерації та антиейджингу з контролем ризиків."
            },
            "mechanisms": {
                "hgh_igf1": {
                    "name": "HGH та IGF-1",
                    "description": "HGH стимулює синтез IGF-1 для відновлення тканин. Рівні падають на 14% щороку після 30-40 років, викликаючи соматопаузу.",
                    "benefits": {
                        "skin": "+20-30% синтез колагену/еластину, зволоження, зменшення зморшок.",
                        "hair": "+15-25% густота, подовження фази росту.",
                        "nails": "Посилення кератину, зменшення ламкості.",
                        "muscles": "+30-50% синтез білка, профілактика саркопенії.",
                        "joints": "+25-40% мобільність через синовіальну рідину.",
                        "hydration": "Протидія висиханню клітин."
                    },
                    "paradox": "Високий IGF-1 (>300 нг/мл) прискорює старіння через метаболічний перегрів. Баланс через цикли."
                }
            },
            "risks": {
                "oncology": "Ризик при IGF-1 >300 нг/мл (рак простати, молочної залози).",
                "diabetes": "+10-20% підвищення глюкози, антагонізм з інсуліном.",
                "other": "Набряки, біль у суглобах, карпальний тунель."
            },
            "risk_mitigation": {
                "oncology": ["Траметес 1-3 г/день", "Куркумін 500-1000 мг", "Ресвератрол 200-500 мг", "EGCG 300-600 мг", "Низьке запалення (кето/середземноморська)"],
                "diabetes": ["Берберин 500-1000 мг", "Кориця 1-2 г", "Хром піколінат 200-400 мкг", "Метформін 500-1000 мг (рецепт)"],
                "general": ["150 хв/тиждень активності", "BMI <25", "CRP <1 мг/л"]
            },
            "assessment": {
                "initial_tests": ["IGF-1 (80-250 нг/мл)", "HGH", "Інсулін", "HbA1c", "C-пептид", "Кортизол", "Тестостерон", "CRP", "Онкомаркери"],
                "dosage_factors": {
                    "bmi": {"<20": "Низькі дози", "20-25": "Стандарт", ">25": "Вищі при активності"},
                    "activity": {"<5k": "Низька", "5-10k": "Середня", ">10k + 3-5 тренувань": "Висока"},
                    "diet": {"Високовуглеводна": "Нижчі дози", "Балансована": "Середня", "Кето/карнівор": "Вища толерантність"}
                },
                "monitoring": "Кожні 3-4 місяці, коригування доз на 20% за IGF-1."
            },
            "natural_boost": {
                "diet": [
                    "Кето/Карнівор: 40-50% жирів, 30% білків (1.6-2 г/кг), <50-100 г вуглеводів.",
                    "Середземноморська: Овочі, риба, горіхи.",
                    "Голодування 16/8, 2-3 дні/тиждень (+300% HGH)."
                ],
                "training": ["HIIT 20 хв, 2-3 рази/тиждень (+400-700% HGH)", "Силові 3 рази/тиждень", "Йога для мобільності"],
                "supplements": [
                    "L-аргінін 3-5 г (буст HGH)",
                    "Глютамін 2-5 г (+78% HGH)",
                    "GABA 500-1000 мг (сон)",
                    "Колаген II 10 г/день",
                    "Гіалуронова кислота 100-200 мг",
                    "Вітамін D3 2000-4000 МО + Омега-3 2 г"
                ],
                "practices": ["7-8 год сну", "Медитація 10 хв/день"]
            },
            "therapeutic_protocols": {
                "cycle": "8-12 тижнів, 5-6 днів/тиждень, перерва 4-8 тижнів.",
                "dosage_table": {
                    "hgh": {"low": "0.3-0.5 МО", "medium": "0.5-1 МО", "high": "1-2 МО"},
                    "ipamorelin": {"low": "100-200 мкг", "medium": "200-300 мкг", "high": "300-400 мкг"},
                    "ibutamoren": {"low": "10 мг", "medium": "15-20 мг", "high": "20-25 мг"}
                },
                "timing": ["Ранок натще", "Перед тренуванням (30-60 хв)", "Вечір"],
                "injection_tips": ["Живіт/стегно, голка 29-31G", "Берберин 500 мг перед HGH", "Кориця 1-2 г з їжею"]
            },
            "pct": {
                "description": "Відновлення ендогенного виділення після циклу.",
                "protocol": ["Ібутоморен 10-15 мг/день", "L-аргінін 3-5 г", "Глютамін 2-5 г", "Голодування, HIIT"],
                "monitoring": "Тести IGF-1 після PCT."
            },
            "example_protocol": {
                "phase1": "Оцінка (Тиждень 1): Аналізи (~500-1000 грн)",
                "phase2": "Природний буст: Дієта кето, 5 тренувань/тиждень",
                "phase3": "Цикл (8-12 тижнів): HGH 1-2 МО + Іпаморелін 300 мкг",
                "phase4": "PCT (4-8 тижнів): Ібутоморен 10-15 мг",
                "cost": "Старт ~500-2000 USD/місяць (USDT/Web3 через Guardian)"
            }
        }

    def create_igf1_json_files(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        with open(os.path.join(self.data_dir, "igf1_protocol.json"), "w") as f:
            json.dump(self.protocol, f, indent=2)

    def process_igf1_query(self, query: str, user, lab_results: Dict) -> Dict:
        if "igf1" in query.lower() or "hgh" in query.lower():
            return {
                "protocol": self.protocol,
                "credo": "PantelMed фокусується на регенерації та якості життя через персоналізовані протоколи.",
                "other_files": "Для ГЗТ див. steroids.py; Для антиейджингу див. anti_aging.py."
            }
        return {"message": "Запит не пов’язаний із IGF-1. Перевір anti_aging.py."}

    @staticmethod
    def test_processing():
        handler = IGF1ProtocolHandler()
        user_mock = type('User', (), {'has_access': lambda x: True})()
        lab_results = {"igf1": {"value": 150, "unit": "ng/ml"}}
        print("\n🧪 Testing IGF-1 Processing:")
        try:
            response = handler.process_igf1_query("IGF-1 протокол", user_mock, lab_results)
            print(f"✅ IGF-1 processed: {response['protocol']['meta']['title']}")
        except Exception as e:
            print(f"❌ Processing error: {e}")

if __name__ == "__main__":
    handler = IGF1ProtocolHandler()
    handler.create_igf1_json_files()
    IGF1ProtocolHandler.test_processing()
    print("\n🚀 IGF-1 protocol module integration complete!")
