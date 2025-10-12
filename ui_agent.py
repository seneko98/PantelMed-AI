from typing import Dict
import logging

logger = logging.getLogger(__name__)

class UIAgent:
    def __init__(self):
        self.supported_languages = ["uk", "en"]

    def validate(self, text: str, language: str) -> Dict:
        """Валідує вхідний текст користувача."""
        if not text:
            logger.warning("Empty input text")
            return {"valid": False, "error": "Input text cannot be empty"}

        if language not in self.supported_languages:
            logger.warning(f"Unsupported language: {language}")
            return {"valid": False, "error": f"Language {language} not supported. Use: {', '.join(self.supported_languages)}"}

        # Перевірка на некоректні питання (можливо, про двох людей)
        suspicious_phrases = ["для друга", "для іншого", "для когось", "інша людина"]
        if any(phrase in text.lower() for phrase in suspicious_phrases):
            logger.warning(f"Suspicious input detected: {text}")
            return {
                "valid": False,
                "error": "Це питання може стосуватися іншої людини. Будь ласка, зверніться до лікаря або створіть окремий акаунт."
            }

        return {"valid": True, "text": text, "language": language}

    def format_response(self, response: str, language: str) -> Dict:
        """Форматує відповідь для користувача."""
        if response and language in self.supported_languages:
            return {"response": response, "language": language}
        logger.warning(f"Invalid response or language: {language}")
        return {"response": "Error formatting response", "language": language}
