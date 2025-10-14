from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ui_agent import UIAgent
from orchestrator import Orchestrator
from former_user import FormerUser
from clinical_agent import ClinicalAgent
from security_agent import SecurityAgent
from steroids import SteroidAgent
from logger_agent import LoggerAgent
from subscription_manager import SubscriptionManager
import openai
import json
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

# Налаштування OpenAI (ключ із .env у майбутньому)
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
    action: str  # "select" або "start"

class ProfileUpdate(BaseModel):
    weight: float
    user_id: str
    goals: dict = {}  # Структура: short_term, mid_term, long_term

class NotificationSubscription(BaseModel):
    user_id: str
    supplements: list
    telegram_id: str

class ProgressInput(BaseModel):
    user_id: str
    rating: str  # "позитивна", "середня", "негативна"

class AnalysisInput(BaseModel):
    user_id: str
    analyses: list  # Список: [{"type": "testosterone", "value": 300, "date": "2025-10-12"}]

class PaymentInput(BaseModel):
    user_id: str
    item: str  # "interaction" або "analysis"
    amount: int  # Кількість пакетів (1 пакет = 30 запитів/аналізів)
    usdt_address: str  # Адреса для оплати USDT

@app.post("/api/auth/register")
async def register(user_id: str, email: str):
    former_user.update_user_data(user_id, {
        "email": email,
        "subscription_start": datetime.datetime.utcnow().isoformat(),
        "subscription_end": (datetime.datetime.utcnow() + datetime.timedelta(days=150)).isoformat()
    })
    return {"message": f"User {user_id} registered with email {email}", "token": "jwt-placeholder"}

@app.post("/api/auth/login")
async def login(user_id: str, email: str):
    return {"message": f"User {user_id} logged in", "token": "jwt-placeholder"}

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
    prompt = f"На основі історії {json.dumps(user_data.get('history', []))} сформуй рекомендації. Якщо користувач не дотримувався рекомендацій, додай: 'БАДи працюють, коли ганяєш кров — почни з тренувань і дієти.'"
    response = clinical_agent.analyze(prompt, user_data.get("history", []))
    logger_agent.log_request(user_input.user_id, "/api/recommendations", logger_agent.token_usage_per_request)

    return ui_agent.format_response(response, user_input.language)

@app.post("/api/course")
async def select_course(course: CourseSelection, user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_id)

    if course.action == "select":
        result = former_user.record_course(user_id, course.course_name, "select")
        return {"message": result["message"]}
    elif course.action == "start":
        result = former_user.record_course(user_id, course.course_name, "start")
        recommendations = steroid_agent.get_recommendations(course.course_name)
        return {"message": result["message"], "recommendations": recommendations}
    raise HTTPException(status_code=400, detail="Invalid action")

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

@app.post("/api/subscribe_notifications")
async def subscribe_notifications(subscription: NotificationSubscription):
    if not subscription.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(subscription.user_id)

    former_user.update_user_data(subscription.user_id, {
        "notifications": {"supplements": subscription.supplements, "telegram_id": subscription.telegram_id}
    })
    return {"message": f"Підписка на сповіщення для {subscription.supplements} активована через Telegram."}

@app.post("/api/check_progress")
async def check_progress(progress: ProgressInput):
    if not progress.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(progress.user_id)

    user_data = former_user.get_user_data(progress.user_id)
    response = steroid_agent.check_progress(progress.user_id, user_data, progress.rating)
    return response

@app.post("/api/analyses")
async def upload_analyses(analysis: AnalysisInput):
    if not analysis.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(analysis.user_id)
    subscription_manager.check_analysis_limit(analysis.user_id)

    for item in analysis.analyses:
        former_user.add_analysis(analysis.user_id, item["type"], item["value"], item["date"])

    return {"message": "Analyses uploaded successfully"}

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

    if payment.item not in ["interaction", "analysis"]:
        raise HTTPException(status_code=400, detail="Invalid item: must be 'interaction' or 'analysis'")
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Заглушка для onramper: 1 пакет = 30 запитів/аналізів за 2.6 USDT
    package_size = 30
    payment_amount = payment.amount * 2.6  # Загальна сума в USDT
    logger_agent.log_request(payment.user_id, "/api/payments", payment_amount)

    # Оновлення лімітів через subscription_manager
    subscription_manager.update_limits(payment.user_id, payment.item, payment.amount * package_size)

    former_user.update_user_data(payment.user_id, {
        "payments": former_user.get_user_data(payment.user_id).get("payments", []) + [{
            "item": payment.item,
            "amount": payment.amount * package_size,
            "usdt_address": payment.usdt_address,
            "date": datetime.datetime.utcnow().isoformat()
        }]
    })

    return {"message": f"Payment of {payment_amount} USDT for {payment.amount * package_size} {payment.item}(s) processed successfully."}

@app.post("/api/reset_limits")
async def reset_limits(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_id)
    subscription_manager.reset_interaction_limit(user_id)
    return {"message": f"Interaction limit reset for user {user_id}"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/wearable")
async def wearable_data():
    return {"message": "Wearable integration not implemented yet."}

@app.get("/api/web3_login")
async def web3_login():
    return {"message": "Web3 login not implemented yet."}
