from openai import OpenAI
import requests
from typing import Dict, List
import logging
import asyncio
from medical_knowledge import MedicalCore
from custom_recommendations import get_custom_recommendations
from anti_aging import AntiAgingHandler

logger = logging.getLogger(__name__)

class AIRecommendations:
    def __init__(self, api_key: str, pubmed_api_keys: List[str]):
        self.client = OpenAI(api_key=api_key)
        self.pubmed_api = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.pubmed_api_keys = pubmed_api_keys
        self.api_key = api_key
        self.medical_knowledge = MedicalCore
        self.custom_recommendations = get_custom_recommendations()
        self.anti_aging_handler = AntiAgingHandler()

    async def _fetch_pubmed(self, query: str, api_key: str) -> List[Dict]:
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "api_key": api_key
        }
        try:
            response = requests.get(self.pubmed_api, params=params)
            data = response.json()
            articles = data.get("esearchresult", {}).get("idlist", [])
            return [{"id": id, "query": query, "api_key": api_key} for id in articles[:5]]
        except Exception as e:
            logger.error(f"Error in _fetch_pubmed with {api_key}: {str(e)}")
            return [{"error": str(e), "api_key": api_key}]

    async def research_pubmed(self, query: str) -> List[Dict]:
        tasks = [self._fetch_pubmed(query, key) for key in self.pubmed_api_keys]
        results = await asyncio.gather(*tasks)
        return [item for sublist in results for item in sublist]

    def get_recommendations(self, lab_results: Dict[str, Dict[str, float | str]]) -> Dict:
        base_knowledge = self.medical_knowledge.supplements_database
        custom = self.custom_recommendations
        anti_aging = self.anti_aging_handler.process("Анти-ейджинг рекомендації", None, lab_results)
        pubmed_results = asyncio.run(self.research_pubmed(f"anti-aging recommendations {list(lab_results.keys())[0]}"))

        prompt = f"""
        Ти медичний експерт із біохакінгу та антиейджингу. Інтерпретуй результати аналізів:
        {lab_results}
        Використовуй базові знання: {base_knowledge}
        Ручні вставки: {custom}
        Анти-ейджинг: {anti_aging}
        PubMed-дослідження: {pubmed_results}
        Дай рекомендації щодо БАДів, тренувань, дієт, процедур або аналізів. Формат: JSON з ключами 'supplements', 'training', 'diet', 'procedures', 'additional_tests'.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return eval(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error in get_recommendations: {str(e)}")
            return {"error": str(e)}
