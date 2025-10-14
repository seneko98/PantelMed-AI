import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class LoggerAgent:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, filename="pantelmed.log", filemode="a",
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.token_usage_per_request = 10000  # Заглушка для витрат токенів OpenAI

    def log_request(self, user_id: str, endpoint: str, tokens_used: float):
        """Логує запит користувача та витрачені токени/платежі."""
        logger.info(f"User {user_id} accessed {endpoint}, tokens/paid amount: {tokens_used}")

    def get_token_usage(self, user_id: str) -> Dict:
        """Повертає статистику витрат токенів (заглушка)."""
        return {
            "user_id": user_id,
            "total_tokens_used": self.token_usage_per_request * 10,  # Приклад
            "last_request": datetime.utcnow().isoformat()
        }
