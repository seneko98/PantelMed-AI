import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from db import Database
import datetime

# Налаштування логування
logger = logging.getLogger(__name__)

# Ініціалізація бота з твоїм MongoDB URI
mongo_uri = "mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0"
db = Database(mongo_uri)

# Вітальне повідомлення та інтро
WELCOME_MESSAGE = (
    "Не можеш схуднути, накачатися, почуватися впевнено чи енергійно? Тобі потрібен біохакінг! 👊\n\n"
    "Я — Влад Кравчук, експерт у біохакінгу, здоров’ї, нейробіології, БАДах, силовому спорті, єдиноборствах, фармакології та трансформаціях тіла й внутрішнього стану. 💪\n\n"
    "Що отримаєш на PantelMed:\n"
    "🧬 Корисні матеріали (як накачатися/схуднути, що їсти, які практики робити)\n"
    "✅ Перевірені інструменти для здоров’я та прогресу в спорті\n"
    "🚀 Доступ до платформи PantelMed\n\n"
    "Обери свій шлях ⬇️"
)

# Нагадування для неплатників
REMINDER_1_5H = "Не можеш схуднути чи накачатися? Біохакінг із PantelMed змінить твоє життя! Переходь на платформу та перевір своє здоров’я! 👉 [Перейти]"
REMINDER_5D = "Ще не спробував? Отримай доступ до аналізов і БАДів за 2.6 USDT! Не пропусти шанс покращити своє здоров’я! 👉 [Перейти]"
REMINDER_7D = "Безкоштовний чек-лист для твого прогресу! Завантаж і почни біохакінг сьогодні! 👉 [Завантажити]"

# Головне меню
MAIN_KEYBOARD = [
    [InlineKeyboardButton("🧬 Перевірити своє здоров’я", callback_data='check_health')],
    [InlineKeyboardButton("💊 Магазин БАДів", callback_data='shop_supplements')],
    [InlineKeyboardButton("📖 Лонгріди", callback_data='longreads')],
    [InlineKeyboardButton("👨‍⚕️ Консультація з експертом", callback_data='consultation')],
    [InlineKeyboardButton("ℹ️ Про PantelMed", callback_data='about')]
]

# Клавіатура для вітання
WELCOME_KEYBOARD = [
    [InlineKeyboardButton("Хочу трансформацію/Продовжити", callback_data='continue')],
    [InlineKeyboardButton("Мені не треба хороше здоров’я", callback_data='exit')]
]

class TelegramBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.job_queue.run_repeating(self.check_reminders, interval=3600)  # Перевірка щогодини

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Вітальне повідомлення з інтро та кнопками"""
        user = update.effective_user
        logger.info(f"New user: {user.id}, {user.username}, {datetime.datetime.utcnow()}")
        
        # Збереження даних у MongoDB
        user_data = {
            "telegram_id": str(user.id),
            "username": user.username,
            "subscription_active": False,
            "active_modules": [],
            "first_interaction": datetime.datetime.utcnow(),
            "interactions": []
        }
        db.insert_document("users", user_data)

        reply_markup = InlineKeyboardMarkup(WELCOME_KEYBOARD)
        await update.message.reply_text(WELCOME_MESSAGE, reply_markup=reply_markup)

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обробка натискань кнопок"""
        query = update.callback_query
        await query.answer()

        user_id = str(query.from_user.id)
        interaction = {"time": datetime.datetime.utcnow(), "action": query.data}
        db.update_document("users", {"telegram_id": user_id}, {"$push": {"interactions": interaction}})
        logger.info(f"User {user_id} clicked: {query.data}")

        if query.data == 'continue':
            reply_markup = InlineKeyboardMarkup(MAIN_KEYBOARD)
            await query.edit_message_text("Головне меню:", reply_markup=reply_markup)
        elif query.data == 'exit':
            await query.edit_message_text("Доки! Якщо передумаєш — повертайся! 👋")
        elif query.data == 'check_health':
            await query.edit_message_text("Переходь на PantelMed для аналізів здоров’я! 👉 [Посилання]")
        elif query.data == 'shop_supplements':
            await query.edit_message_text("Переходь до PantelMed Shop за БАДами! 👉 [Посилання]")
        elif query.data == 'longreads':
            await query.edit_message_text("Лонгріди: [Як накачатися] [СДУГ] 👉 [Посилання]")
        elif query.data == 'consultation':
            await query.edit_message_text("Запис на консультацію: [Посилання на твій Telegram]")
        elif query.data == 'about':
            await query.edit_message_text("PantelMed — твоя дорога до здоров’я та довголіття! Перейти на сайт 👉 [Посилання]")

    async def check_reminders(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Перевірка та відправка нагадувань для неплатників"""
        users = db.find_documents("users", {"subscription_active": False})
        for user in users:
            user_id = user["telegram_id"]
            first_interaction = user["first_interaction"]
            interactions = user.get("interactions", [])

            time_diff_1_5h = datetime.datetime.utcnow() - first_interaction > datetime.timedelta(hours=1.5)
            time_diff_5d = datetime.datetime.utcnow() - first_interaction > datetime.timedelta(days=5)
            time_diff_7d = datetime.datetime.utcnow() - first_interaction > datetime.timedelta(days=7)

            if time_diff_1_5h and not any("check_health" in str(i) or "shop_supplements" in str(i) for i in interactions):
                await context.bot.send_message(chat_id=user_id, text=REMINDER_1_5H)
                logger.info(f"Sent 1.5h reminder to {user_id}")
            elif time_diff_5d and not any("check_health" in str(i) or "shop_supplements" in str(i) for i in interactions):
                await context.bot.send_message(chat_id=user_id, text=REMINDER_5D)
                logger.info(f"Sent 5d reminder to {user_id}")
            elif time_diff_7d and not any("check_health" in str(i) or "shop_supplements" in str(i) for i in interactions):
                await context.bot.send_message(chat_id=user_id, text=REMINDER_7D)
                logger.info(f"Sent 7d reminder to {user_id}")

    def run(self):
        """Запуск бота"""
        logger.info("Starting Telegram Bot...")
        self.application.run_polling()

if __name__ == "__main__":
    # Заміни на твій токен пізніше
    bot = TelegramBot("YOUR_TELEGRAM_BOT_TOKEN")
    bot.run()
