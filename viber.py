from viberbot import BotConfiguration, Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import TextMessage
from viberbot.api.viber_requests import ViberMessageRequest, ViberSubscribedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from db import Database
import logging
import datetime

logger = logging.getLogger(__name__)

# Ініціалізація Viber бота з твоїм MongoDB URI
mongo_uri = "mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0"
db = Database(mongo_uri)

# Налаштування бота (токен вставиш пізніше)
viber_config = BotConfiguration(
    name="PantelMed",
    avatar="",
    auth_token="YOUR_VIBER_AUTH_TOKEN"
)
viber = Api(viber_config)

# Повідомлення
ORDER_CONFIRMATION = "Твоє замовлення БАДів прийнято! Очікуй підтвердження відправки. 👉 [Посилання]"
SHIPPING_UPDATE = "Твоє замовлення відправлено! Трек-номер: [номер]. Доставка 2-3 дні."
REMINDER = "Онови аналізи для кращих результатів! Переходь на PantelMed 👉 [Посилання]"

class ViberBot:
    def __init__(self):
        self.viber = viber
        self.setup_webhook()

    def setup_webhook(self):
        # Вставиш URL пізніше
        self.viber.set_webhook("YOUR_WEBHOOK_URL")

    async def connect_messenger(self, user_id: str, messenger_id: str, messenger_type: str):
        """Збереження Viber/Telegram ID при підключенні через віджет"""
        user_data = db.find_document("users", {"user_id": user_id})
        if user_data:
            update_data = {
                f"{messenger_type}_id": messenger_id,
                "updated_at": datetime.datetime.utcnow()
            }
            db.update_document("users", {"user_id": user_id}, {"$set": update_data})
            logger.info(f"Connected {messenger_type} ID {messenger_id} for user {user_id}")
        else:
            logger.error(f"User {user_id} not found")

    async def send_order_confirmation(self, user_id: str, order_id: str):
        """Підтвердження замовлення"""
        user = db.find_document("users", {"user_id": user_id})
        if user and "viber_id" in user:
            self.viber.send_messages(user["viber_id"], [TextMessage(text=ORDER_CONFIRMATION.format(order_id=order_id))])
            logger.info(f"Sent order confirmation to Viber ID {user['viber_id']}")

    async def send_shipping_update(self, user_id: str, tracking_number: str):
        """Сповіщення про відправку"""
        user = db.find_document("users", {"user_id": user_id})
        if user and "viber_id" in user:
            self.viber.send_messages(user["viber_id"], [TextMessage(text=SHIPPING_UPDATE.format(tracking_number=tracking_number))])
            logger.info(f"Sent shipping update to Viber ID {user['viber_id']}")

    async def send_reminder(self, user_id: str):
        """Нагадування про аналізи"""
        user = db.find_document("users", {"user_id": user_id})
        if user and "viber_id" in user:
            self.viber.send_messages(user["viber_id"], [TextMessage(text=REMINDER)])
            logger.info(f"Sent reminder to Viber ID {user['viber_id']}")

    def handle_request(self, request):
        """Обробка вхідних запитів від Viber"""
        if isinstance(request, ViberMessageRequest):
            logger.info(f"Received message from {request.sender.id}")
        elif isinstance(request, ViberSubscribedRequest):
            logger.info(f"User {request.user.id} subscribed")
        elif isinstance(request, ViberFailedRequest):
            logger.error(f"Failed request: {request}")

    def run(self):
        """Запуск бота (заміни на твій вебхук)"""
        logger.info("Starting Viber Bot...")
        # Логіка вебхука — вставиш пізніше
        pass

if __name__ == "__main__":
    bot = ViberBot()
    bot.run()
