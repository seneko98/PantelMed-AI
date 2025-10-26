from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from ui_agent import UIAgent
from orchestrator import Orchestrator
from former_user import FormerUser
from clinical_agent import ClinicalAgent
from security_agent import SecurityAgent
from steroids import SteroidAgent
from logger_agent import LoggerAgent
from subscription_manager import SubscriptionManager
from pay import create_payment, check_payment_status
from products import ProductsDatabase
from blood_interpreter import BloodInterpreter
from telegram import TelegramBot
from womens_health_protocol import get_womens_health_protocol
from nutrition import get_nutrition_protocol
from antifitness import get_antifitness_protocol
from cosmetology import get_skin_protocol
import openai
import datetime

app = FastAPI()
ui_agent = UIAgent()
orchestrator = Orchestrator()
former_user = FormerUser()
clinical_agent = ClinicalAgent()
security_agent = SecurityAgent()
steroid_agent = SteroidAgent()
logger_agent = LoggerAgent()
subscription_manager = SubscriptionManager()
products_db = ProductsDatabase()
blood_interpreter = BloodInterpreter()
telegram_bot = TelegramBot("8116552220:AAHiOZdROOQKtj09ZDvLRYZw2FNKPQrmMV4")

openai.api_key = "your-openai-api-key-here"

# Моделі даних
class UserInput(BaseModel):
    text: str
    language: str = "uk"
    user_id: str = None

class TestInput(BaseModel):
    answers: dict
    user_id: str
    language: str = "uk"

class TestResultsInput(BaseModel):
    user_id: str
    language: str = "uk"

class CourseSelection(BaseModel):
    course_name: str
    action: str
    supplements: List[str] = None
    user_id: str

class SupplementStackInput(BaseModel):
    user_id: str
    supplement_ids: List[str]

class ProfileUpdate(BaseModel):
    weight: float
    user_id: str
    goals: dict = {}
    gender: Optional[str] = None

class NotificationSubscription(BaseModel):
    user_id: str
    supplements: list
    telegram_id: str

class ProgressInput(BaseModel):
    user_id: str
    rating: str

class AnalysisInput(BaseModel):
    user_id: str
    analyses: list
    symptoms: List[str] = None

class PaymentInput(BaseModel):
    user_id: str
    item: str
    item_id: str | None = None
    amount: int
    usdt_address: str

class PaymentCheckInput(BaseModel):
    user_id: str
    payment_id: str

class CartItem(BaseModel):
    product_id: str
    quantity: int

class CartInput(BaseModel):
    user_id: str
    items: List[CartItem]

class CheckoutInput(BaseModel):
    user_id: str
    cart_id: str
    usdt_address: str

# === АУТЕНТИФІКАЦІЯ ===
@app.post("/api/auth/register")
async def register(user_id: str, email: str, gender: str = None):
    former_user.update_user_data(user_id, {
        "email": email,
        "gender": gender,
        "subscription_start": datetime.datetime.utcnow().isoformat(),
        "subscription_end": (datetime.datetime.utcnow() + datetime.timedelta(days=150)).isoformat()
    })
    return {"message": f"Користувач {user_id} зареєстрований", "token": "jwt-placeholder"}

@app.post("/api/auth/login")
async def login(user_id: str, email: str):
    return {"message": f"Користувач {user_id} увійшов", "token": "jwt-placeholder"}

# === ТЕСТ НА ЗДОРОВ'Я ===
@app.post("/api/test")
async def handle_test(test_input: TestInput):
    if not test_input.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")
    
    security_agent.check_user(test_input.user_id)
    prompt = f"Аналізуй відповіді тесту: {json.dumps(test_input.answers)}. Пропонуй цілі та рекомендації."
    response = clinical_agent.analyze(prompt, former_user.get_user_data(test_input.user_id).get("history", []))
    
    former_user.update_user_data(test_input.user_id, {
        "test_results": test_input.answers,
        "test_timestamp": datetime.datetime.utcnow().isoformat(),
        "history": [{"input": test_input.answers, "response": response, "type": "test"}]
    })
    return ui_agent.format_response(response, test_input.language)

@app.post("/api/test/results")
async def get_test_results(test_input: TestResultsInput):
    if not test_input.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")
    
    security_agent.check_user(test_input.user_id)
    user_data = former_user.get_user_data(test_input.user_id)
    
    if not user_data.get("test_results"):
        raise HTTPException(status_code=404, detail="Результати тесту не знайдено")
    
    # Перевірка підписки
    is_subscribed = subscription_manager.check_subscription(test_input.user_id)
    if not is_subscribed:
        return {"message": "Оформіть підписку для детальних результатів"}
    
    # Перевірка ліміту повторного тесту (5-6 місяців)
    test_timestamp = user_data.get("test_timestamp")
    if test_timestamp:
        last_test = datetime.datetime.fromisoformat(test_timestamp)
        if (datetime.datetime.utcnow() - last_test).days < 150:
            raise HTTPException(status_code=429, detail="Повторний тест доступний через 5-6 місяців")
    
    # Форматування результатів
    results = {
        "answers": user_data["test_results"],
        "formatted": [
            {
                "question": q,
                "selected_answer": a,
                "unselected_answers": ["Інший варіант"]  # Заглушка для невибраних
            } for q, a in user_data["test_results"].items()
        ]
    }
    return {"results": results}

# === AI-ЛІКАР ===
@app.post("/api/ai_doctor")
async def ai_doctor(user_input: UserInput):
    if not user_input.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")
    
    security_agent.check_user(user_input.user_id)
    subscription_manager.check_interaction_limit(user_input.user_id)
    
    validated_input = ui_agent.validate(user_input.text, user_input.language)
    if not validated_input["valid"]:
        raise HTTPException(status_code=400, detail=validated_input["error"])
    
    user_data = former_user.get_user_data(user_input.user_id)
    validated_input["history"] = user_data.get("history", [])
    validated_input["user_id"] = user_input.user_id
    
    response = orchestrator.process(validated_input)
    logger_agent.log_request(user_input.user_id, "/api/ai_doctor", logger_agent.token_usage_per_request)
    
    former_user.update_user_data(user_input.user_id, {
        "history": validated_input["history"] + [{"input": user_input.text, "response": response, "type": "ai_doctor"}]
    })
    
    return ui_agent.format_response(response, user_input.language)

# === АНТИЕЙДЖИНГ ===
@app.post("/api/antiaging")
async def antiaging(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    security_agent.check_user(user_id)
    subscription_manager.check_interaction_limit(user_id)
    
    # Тимчасово: базові рекомендації
    protocol = {
        "supplements": ["Колаген 10г", "Вітамін C 1г", "Ресвератрол 500мг"],
        "lifestyle": ["Сон 7-8 годин", "SPF 50 щоденно"],
        "generated_at": datetime.datetime.utcnow().isoformat()
    }
    return {"protocol": protocol}

# === ЛУКСМАКСИНГ-КОСМЕТОЛОГІЯ ===
@app.post("/api/cosmetology")
async def cosmetology(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    security_agent.check_user(user_id)
    subscription_manager.check_interaction_limit(user_id)
    
    return {"protocol": await get_skin_protocol(user_id, payment_confirmed=False)}

# === PANTELMED SHOP ===
@app.post("/api/shop/cart")
async def manage_cart(cart: CartInput):
    if not cart.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    security_agent.check_user(cart.user_id)
    subscription_manager.check_interaction_limit(cart.user_id)

    cart_id = str(former_user.get_user_data(cart.user_id).get("cart_id", datetime.datetime.utcnow().isoformat()))
    cart_items = [{"product_id": item.product_id, "quantity": item.quantity} for item in cart.items]
    total_price = sum(products_db.get_product(item["product_id"]).price_usd * item["quantity"] for item in cart.items)
    
    former_user.update_user_data(cart.user_id, {
        "cart_id": cart_id,
        "cart_items": cart_items,
        "cart_total": total_price
    })
    
    logger_agent.log_request(cart.user_id, "/api/shop/cart", logger_agent.token_usage_per_request)
    return {"cart_id": cart_id, "items": cart_items, "total_price": total_price}

@app.post("/api/shop/checkout")
async def checkout(checkout: CheckoutInput):
    if not checkout.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    security_agent.check_user(checkout.user_id)
    subscription_manager.check_interaction_limit(checkout.user_id)

    user_data = former_user.get_user_data(checkout.user_id)
    cart = user_data.get("cart_items", [])
    if not cart:
        raise HTTPException(status_code=400, detail="Кошик порожній")

    payment = await create_payment(PaymentInput(
        user_id=checkout.user_id,
        item="supplement_purchase",
        item_id=checkout.cart_id,
        amount=len(cart),
        usdt_address=checkout.usdt_address
    ))

    if payment.get("status") == "success":
        supplement_ids = [item["product_id"] for item in cart]
        steroid_agent.start_supplement_stack(checkout.user_id, supplement_ids)
        former_user.update_user_data(checkout.user_id, {"cart_items": [], "cart_total": 0})
    
    logger_agent.log_subscription_event(checkout.user_id, "shop_checkout", f"Checkout completed for cart {checkout.cart_id}")
    return payment

@app.get("/api/shop/products")
async def get_products(category: str = None):
    products = products_db.get_products(category)
    return {"products": [p.__dict__ for p in products]}

@app.post("/api/shop/connect_messenger")
async def connect_messenger(data: Dict):
    user_id = data.get("user_id")
    messenger = data.get("messenger")  # 'telegram' або 'viber'
    messenger_id = data.get("messenger_id")

    if not all([user_id, messenger, messenger_id]):
        raise HTTPException(status_code=400, detail="Потрібні user_id, messenger і messenger_id")

    security_agent.check_user(user_id)

    updates = {"updated_at": datetime.datetime.utcnow().isoformat()}
    if messenger == "telegram":
        updates["telegram_id"] = messenger_id
    elif messenger == "viber":
        updates["viber_id"] = messenger_id
    former_user.update_user_data(user_id, updates)

    logger_agent.log_request(user_id, "/api/shop/connect_messenger", 0)
    return {"status": "success", "message": f"Підключено {messenger} для {user_id}"}

# === ОСОБИСТИЙ КАБІНЕТ ===
@app.post("/api/profile")
async def update_profile(profile: ProfileUpdate):
    if not profile.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")

    security_agent.check_weight(profile.user_id, profile.weight)
    security_agent.check_goal_change(profile.user_id, profile.goals)

    user_data = former_user.get_user_data(profile.user_id)
    if not user_data:
        return {"message": "Новий користувач. Пройдіть тест для створення профілю."}

    updates = {
        "weight": profile.weight,
        "goals": {
            "short_term": profile.goals.get("short_term", []),
            "mid_term": profile.goals.get("mid_term", []),
            "long_term": profile.goals.get("long_term", [])
        },
        "history": user_data.get("history", []) + [{"input": {"weight": profile.weight, "goals": profile.goals}, "response": "Profile updated", "type": "profile"}]
    }
    if profile.gender:
        updates["gender"] = profile.gender

    former_user.update_user_data(profile.user_id, updates)
    return {"profile": former_user.get_user_data(profile.user_id)}

@app.get("/api/profile")
async def get_profile(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")

    security_agent.check_user(user_id)
    user_data = former_user.get_user_data(user_id)
    if not user_data:
        return {"message": "Новий користувач. Пройдіть тест для створення профілю."}
    
    return {"profile": user_data}

# === СПОВІЩЕННЯ ===
@app.post("/api/subscribe_notifications")
async def subscribe_notifications(subscription: NotificationSubscription):
    if not subscription.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")

    security_agent.check_user(subscription.user_id)

    former_user.update_user_data(subscription.user_id, {
        "notifications": {"supplements": subscription.supplements, "telegram_id": subscription.telegram_id}
    })
    return {"message": f"Підписка на сповіщення для {subscription.supplements} активована через Telegram."}

# === ПРОГРЕС ===
@app.post("/api/check_progress")
async def check_progress(progress: ProgressInput):
    if not progress.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")

    security_agent.check_user(progress.user_id)

    user_data = former_user.get_user_data(progress.user_id)
    response = steroid_agent.check_progress(progress.user_id, user_data, progress.rating)
    return response

# === АНАЛІЗИ ===
@app.post("/api/analyses")
async def upload_analyses(analysis: AnalysisInput):
    if not analysis.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")

    security_agent.check_user(analysis.user_id)
    subscription_manager.check_analysis_limit(analysis.user_id)

    results = []
    for item in analysis.analyses:
        result = blood_interpreter.interpret_analysis(analysis.user_id, item, analysis.symptoms)
        results.append(result)

    return {"message": "Аналіз оброблено", "results": results}

# === ПЛАТЕЖІ ===
@app.get("/api/balance")
async def get_balance(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")

    security_agent.check_user(user_id)
    return subscription_manager.get_balance(user_id)

@app.post("/api/payments")
async def process_payment(payment: PaymentInput):
    if not payment.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")

    security_agent.check_user(payment.user_id)
    return await create_payment(payment)

@app.post("/api/payments/check")
async def check_payment(check: PaymentCheckInput):
    if not check.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")

    security_agent.check_user(check.user_id)
    return await check_payment_status(check)

# === АДМІН ===
@app.post("/api/reset_limits")
async def reset_limits(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id")

    security_agent.check_user(user_id)
    subscription_manager.reset_interaction_limit(user_id)
    return {"message": f"Ліміти скинуто для {user_id}"}

# === WEB3 ===
@app.get("/api/web3_login")
async def web3_login():
    return {"message": "Web3 логін ще не реалізований"}

# === НОСИМІ ПРИСТРОЇ ===
@app.get("/api/wearable")
async def wearable_data():
    return {"message": "Інтеграція з носимими пристроями ще не реалізована"}

# === HEALTH CHECK ===
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
