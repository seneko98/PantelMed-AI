from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
import openai
import json
import datetime

app = FastAPI()

# Додавання CORS для фронтенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Додай продакшн URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class UserInput(BaseModel):
    text: str
    language: str = "uk"
    user_id: str = None

class TestInput(BaseModel):
    answers: dict
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

# Оновлення цін у products_db
products_db.update_product("ashwagandha", {"price_usd": 1.3})
products_db.update_product("magnesium", {"price_usd": 1.3})
products_db.update_product("retinol_serum", {"price_usd": 1.3})

# Core
@app.post("/api/auth/register")
async def register(user_id: str, email: str):
    former_user.update_user_data(user_id, {
        "email": email,
        "subscription_start": datetime.datetime.utcnow().isoformat(),
        "subscription_end": (datetime.datetime.utcnow() + datetime.timedelta(days=150)).isoformat()
    })
    return {"message": f"Користувач {user_id} зареєстрований з email {email}", "token": "jwt-placeholder"}

@app.post("/api/auth/login")
async def login(user_id: str, email: str):
    return {"message": f"Користувач {user_id} увійшов", "token": "jwt-placeholder"}

# AI / Agents
@app.post("/api/user_input")
async def handle_user_input(user_input: UserInput):
    if not user_input.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_input.user_id)
    subscription_manager.check_interaction_limit(user_input.user_id)

    validated_input = ui_agent.validate(user_input.text, user_input.language)
    if not validated_input["valid"]:
        raise HTTPException(status_code=400, detail=validated_input["error"])

    user_data = former_user.get_user_data(user_input.user_id)
    if user_data:
        validated_input["history"] = user_data.get("history", [])
        validated_input["user_id"] = user_input.user_id

    response = orchestrator.process(validated_input)
    logger_agent.log_request(user_input.user_id, "/api/user_input", logger_agent.token_usage_per_request)

    former_user.update_user_data(user_input.user_id, {
        "history": validated_input["history"] + [{"input": user_input.text, "response": response, "type": "query"}]
    })

    return ui_agent.format_response(response, user_input.language)

@app.post("/api/test")
async def handle_test(test_input: TestInput):
    if not test_input.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(test_input.user_id)

    prompt = f"Аналізуй відповіді тесту: {json.dumps(test_input.answers)}. Пропонуй цілі та рекомендації."
    response = clinical_agent.analyze(prompt, former_user.get_user_data(test_input.user_id).get("history", []))
    
    former_user.update_user_data(test_input.user_id, {
        "history": [{"input": test_input.answers, "response": response, "type": "test"}]
    })

    return ui_agent.format_response(response, test_input.language)

@app.post("/api/recommendations")
async def get_recommendations(user_input: UserInput):
    if not user_input.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_input.user_id)
    subscription_manager.check_interaction_limit(user_input.user_id)

    user_data = former_user.get_user_data(user_input.user_id)
    validated_input = {
        "text": user_input.text,
        "history": user_data.get("history", []),
        "user_id": user_input.user_id
    }

    response = orchestrator.process(validated_input)
    logger_agent.log_request(user_input.user_id, "/api/recommendations", logger_agent.token_usage_per_request)

    return ui_agent.format_response(response, user_input.language)

# Steroids
@app.post("/api/course")
async def select_course(course: CourseSelection):
    if not course.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(course.user_id)

    if course.action == "select":
        result = former_user.record_course(course.user_id, course.course_name, "select")
        return {"message": result["message"]}
    elif course.action == "start":
        result = steroid_agent.start_course(course.user_id, course.course_name, course.supplements)
        return {"message": result["message"]}
    raise HTTPException(status_code=400, detail="Невалідна дія")

@app.post("/api/supplements")
async def start_supplement_stack(stack: SupplementStackInput):
    if not stack.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(stack.user_id)
    subscription_manager.check_supplement_plan_limit(stack.user_id)

    result = steroid_agent.start_supplement_stack(stack.user_id, stack.supplement_ids)
    return {"message": result["message"]}

@app.get("/api/cycles/catalog")
async def get_cycles_catalog(user_id: str, category: str = "all", administration: str = None, experience_level: str = None, price_range: str = None, side_effects: List[str] = None):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_id)
    subscription_manager.check_interaction_limit(user_id)

    user_data = former_user.get_user_data(user_id)
    cycles = steroid_agent.get_recommendations("", user_id).get("cycles", [])
    
    # Фільтрація за параметрами
    if administration:
        cycles = [c for c in cycles if c["administration"] == administration]
    if experience_level:
        cycles = [c for c in cycles if c["experience_level"] == experience_level]
    if price_range:
        if price_range == "budget":
            cycles = [c for c in cycles if c["cost_usd"] < 100]
        elif price_range == "mid":
            cycles = [c for c in cycles if 100 <= c["cost_usd"] <= 200]
        elif price_range == "premium":
            cycles = [c for c in cycles if c["cost_usd"] > 200]
    if side_effects:
        cycles = [c for c in cycles if all(se in c["side_effects"] for se in side_effects)]

    catalog = {
        "short_cycles": [c for c in cycles if c["duration"] in ["6 weeks", "8 weeks"]],
        "medium_cycles": [c for c in cycles if c["duration"] in ["10 weeks", "12 weeks"]],
        "long_cycles": [c for c in cycles if c["duration"] in ["16 weeks"]],
        "user_recommendations": cycles,
        "filters_available": ["duration", "goal", "experience_level", "budget", "compounds", "administration", "side_effects"],
        "sorting_options": [
            {"value": "recommended", "label": "Рекомендовано для вас"},
            {"value": "price_low", "label": "Спочатку дешевші"},
            {"value": "price_high", "label": "Спочатку дорожчі"},
            {"value": "duration", "label": "За тривалістю"}
        ]
    }

    logger_agent.log_request(user_id, "/api/cycles/catalog", logger_agent.token_usage_per_request)
    return {"catalog": catalog}

# Shop
@app.post("/api/shop/cart")
async def manage_cart(cart: CartInput):
    if not cart.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(cart.user_id)
    subscription_manager.check_interaction_limit(cart.user_id)

    cart_id = str(former_user.get_user_data(cart.user_id).get("cart_id", datetime.datetime.utcnow().isoformat()))
    cart_items = [{"product_id": item.product_id, "quantity": item.quantity} for item in cart.items]
    total_price = sum(products_db.get_product(item["product_id"]).price_usd * item["quantity"] for item in cart_items)
    
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
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

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
    messenger = data.get("messenger")
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

# Profile
@app.post("/api/profile")
async def update_profile(profile: ProfileUpdate):
    if not profile.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_weight(profile.user_id, profile.weight)
    security_agent.check_goal_change(profile.user_id, profile.goals)

    user_data = former_user.get_user_data(profile.user_id)
    if not user_data:
        return {"message": "Новий користувач. Пройдіть тест для створення профілю."}

    former_user.update_user_data(profile.user_id, {
        "weight": profile.weight,
        "goals": {
            "short_term": profile.goals.get("short_term", []),
            "mid_term": profile.goals.get("mid_term", []),
            "long_term": profile.goals.get("long_term", [])
        },
        "history": user_data.get("history", []) + [{"input": {"weight": profile.weight, "goals": profile.goals}, "response": "Profile updated", "type": "profile"}]
    })
    return {"profile": former_user.get_user_data(profile.user_id)}

@app.get("/api/profile")
async def get_profile(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_id)

    user_data = former_user.get_user_data(user_id)
    if not user_data:
        return {"message": "Новий користувач. Пройдіть тест для створення профілю."}
    
    return {"profile": user_data}

# Notifications
@app.post("/api/subscribe_notifications")
async def subscribe_notifications(subscription: NotificationSubscription):
    if not subscription.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(subscription.user_id)

    former_user.update_user_data(subscription.user_id, {
        "notifications": {"supplements": subscription.supplements, "telegram_id": subscription.telegram_id}
    })
    return {"message": f"Підписка на сповіщення для {subscription.supplements} активована через Telegram."}

# Progress
@app.post("/api/check_progress")
async def check_progress(progress: ProgressInput):
    if not progress.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(progress.user_id)

    user_data = former_user.get_user_data(progress.user_id)
    response = steroid_agent.check_progress(progress.user_id, user_data, progress.rating)
    return response

# Analyses
@app.post("/api/analyses")
async def upload_analyses(analysis: AnalysisInput):
    if not analysis.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(analysis.user_id)
    subscription_manager.check_analysis_limit(analysis.user_id)

    results = []
    for item in analysis.analyses:
        result = blood_interpreter.interpret_analysis(analysis.user_id, item, analysis.symptoms)
        results.append(result)

    return {"message": "Аналіз оброблено успішно", "results": results}

# Payments
@app.get("/api/balance")
async def get_balance(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_id)
    return subscription_manager.get_balance(user_id)

@app.post("/api/payments")
async def process_payment(payment: PaymentInput):
    if not payment.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(payment.user_id)
    return await create_payment(payment)

@app.post("/api/payments/check")
async def check_payment(check: PaymentCheckInput):
    if not check.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(check.user_id)
    return await check_payment_status(check)

# Admin
@app.post("/api/reset_limits")
async def reset_limits(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_id)
    subscription_manager.reset_interaction_limit(user_id)
    return {"message": f"Ліміти скинуто для користувача {user_id}"}

# Health Check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Wearables
@app.get("/api/wearable")
async def wearable_data():
    return {"message": "Інтеграція з носимими пристроями ще не реалізована."}

# Web3
@app.get("/api/web3_login")
async def web3_login():
    return {"message": "Web3 логін ще не реалізований."}

# Нові розділи (заглушки)
@app.get("/api/womens_health")
async def womens_health(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")
    return {"message": "Розділ жіночого здоров’я в розробці (гормональний баланс, ПМС, менопауза, ПКЯ)." }

@app.get("/api/diets")
async def diets(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")
    return {"message": "Розділ дієт в розробці (кето, палео, веган, інтервальне голодування)." }

@app.get("/api/antifitness")
async def antifitness(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")
    return {"message": "Розділ антифітнесу в розробці (відновлення, йога, пілатес)." }

@app.get("/api/cosmetology")
async def cosmetology(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")
    return {"message": "Розділ косметології та луксмаксингу в розробці (догляд за шкірою, ін’єкції, лазери)." }

@app.get("/api/pharma")
async def pharma(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")
    return {"message": "Розділ фармакології в розробці (ААС, гормони, пептиди)." }
