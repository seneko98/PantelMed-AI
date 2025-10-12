from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ui_agent import UIAgent
from orchestrator import Orchestrator
from former_user import FormerUser
from clinical_agent import ClinicalAgent
from security_agent import SecurityAgent
from steroids import SteroidAgent
from logger_agent import LoggerAgent
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
    goals: dict = {}  # Структура short_term, mid_term, long_term

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
    item: str  # "interaction_package_30" або "analysis_package_30"
    amount: int = 1  # Кількість пакетів

class ResetLimits(BaseModel):
    user_id: str

@app.post("/api/auth/register")
async def register(user_id: str, email: str):
    return {"message": f"User {user_id} registered with email {email}", "token": "jwt-placeholder"}

@app.post("/api/auth/login")
async def login(user_id: str, email: str):
    return {"message": f"User {user_id} logged in", "token": "jwt-placeholder"}

@app.post("/api/user_input")
async def handle_user_input(user_input: UserInput):
    if not user_input.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_input.user_id)

    # Перевірка ліміту AI-запитів
    interactions = former_user.get_interaction_count(user_input.user_id)
    user_data = former_user.get_user_data(user_input.user_id)
    subscription_end = user_data.get("subscription_end", datetime.datetime.utcnow().isoformat())
    if interactions >= 40 and (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(subscription_end)).days < 150:
        raise HTTPException(status_code=402, detail="Interaction limit exceeded (40/month). Upgrade your plan via /api/payments.")
    elif interactions >= 15:
        raise HTTPException(status_code=402, detail="Interaction limit exceeded (15/month after initial 40). Upgrade your plan via /api/payments.")

    validated_input = ui_agent.validate(user_input.text, user_input.language)
    if not validated_input["valid"]:
        raise HTTPException(status_code=400, detail=validated_input["error"])

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

    # Перевірка ліміту AI-запитів
    interactions = former_user.get_interaction_count(user_input.user_id)
    user_data = former_user.get_user_data(user_input.user_id)
    subscription_end = user_data.get("subscription_end", datetime.datetime.utcnow().isoformat())
    if interactions >= 40 and (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(subscription_end)).days < 150:
        raise HTTPException(status_code=402, detail="Interaction limit exceeded (40/month). Upgrade your plan via /api/payments.")
    elif interactions >= 15:
        raise HTTPException(status_code=402, detail="Interaction limit exceeded (15/month after initial 40). Upgrade your plan via /api/payments.")

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

    for item in analysis.analyses:
        result = former_user.add_analysis(analysis.user_id, item["type"], item["value"], item["date"])
        if "error" in result:
            raise HTTPException(status_code=402, detail=result["error"])

    return {"message": "Analyses uploaded successfully"}

@app.post("/api/payments")
async def process_payment(payment: PaymentInput):
    if not payment.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(payment.user_id)

    # Заглушка для onramper (2.6 USDT за пакет 30 запитів)
    payment_amount = payment.amount * 2.6  # 2.6 USDT за пакет
    logger_agent.log_request(payment.user_id, "/api/payments", payment_amount)

    # Оновлення лімітів
    user_data = former_user.get_user_data(payment.user_id)
    update_data = {
        "payments": user_data.get("payments", []) + [{
            "item": payment.item,
            "amount": payment.amount,
            "usdt_address": payment.usdt_address,
            "date": datetime.datetime.utcnow().isoformat()
        }]
    }
    if payment.item == "interaction_package_30":
        update_data["interaction_limit"] = user_data.get("interaction_limit", 40) + payment.amount * 30
    elif payment.item == "analysis_package_30":
        update_data["analysis_limit"] = user_data.get("analysis_limit", 5) + payment.amount * 30

    former_user.update_user_data(payment.user_id, update_data)

    return {"message": f"Payment of {payment_amount} USDT for {payment.amount} package(s) of 30 {payment.item} processed successfully."}

@app.get("/api/balance")
async def get_balance(user_id: str):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(user_id)

    user_data = former_user.get_user_data(user_id)
    interactions = former_user.get_interaction_count(user_id)
    analyses = former_user.get_analysis_count(user_id)
    subscription_end = user_data.get("subscription_end", datetime.datetime.utcnow().isoformat())
    remaining_interactions = 40 if (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(subscription_end)).days < 150 else 15
    remaining_interactions = max(0, remaining_interactions - interactions)
    remaining_analyses = max(0, 5 - analyses)

    return {
        "interactions": {
            "used": interactions,
            "remaining": remaining_interactions,
            "limit": 40 if (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(subscription_end)).days < 150 else 15
        },
        "analyses": {
            "used": analyses,
            "remaining": remaining_analyses,
            "limit": 5
        }
    }

@app.post("/api/reset_limits")
async def reset_limits(reset: ResetLimits):
    if not reset.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Provide user_id or login")

    security_agent.check_user(reset.user_id)

    user_data = former_user.get_user_data(reset.user_id)
    interaction_limit = user_data.get("interaction_limit", 40)
    analysis_limit = user_data.get("analysis_limit", 5)
    used_interactions = former_user.get_interaction_count(reset.user_id)
    used_analyses = former_user.get_analysis_count(reset.user_id)

    # Додаємо залишок до балансу (якщо не використав)
    new_interaction_limit = (interaction_limit - used_interactions) + 15
    new_analysis_limit = (analysis_limit - used_analyses) + 1  # 1/місяць, але накопичується
    former_user.update_user_data(reset.user_id, {
        "interaction_limit": new_interaction_limit,
        "analysis_limit": new_analysis_limit
    })

    return {"message": "Limits reset successfully"}
