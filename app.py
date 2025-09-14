from flask import Flask, jsonify, request
from flask_cors import cross_origin
from db import Database
from handlers import handlers_bp
from shop import shop_bp
from pay import pay_bp
from crm import crm_bp
from datetime import datetime
import logging
from bson import ObjectId
from utils.blockchain import BlockchainIntegrator

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфігурація
MONGO_URI = "mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0"
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
VIBER_BOT_TOKEN = "your_viber_bot_token"
TRON_WALLET = "TQeHa8VdwfyybxtioW4ggbnDC1rbWe8nFa"
OPENAI_API_KEY = "your_api_key_here"  # Placeholder
app.config.update({
    "MONGO_URI": MONGO_URI,
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "VIBER_BOT_TOKEN": VIBER_BOT_TOKEN,
    "TRON_WALLET": TRON_WALLET,
    "OPENAI_API_KEY": OPENAI_API_KEY
})

# Ініціалізація
db = Database(MONGO_URI)
blockchain = BlockchainIntegrator()

# Маппінг показників
TEST_MAPPING = {
    "АЛТ (аланінамінотрансфераза)": "alt",
    "АСТ (аспартатамінотрансфераза)": "ast",
    "Тестостерон загальний": "testosterone_total"
    # ... (повний список скорочено)
}

# Реєстрація Blueprint'ів
app.register_blueprint(handlers_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(pay_bp)
app.register_blueprint(crm_bp)

@app.route('/api/health/upload_lab_results', methods=['POST'])
@cross_origin()
def upload_lab_results():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        lab_type = data.get('lab_type')
        file_data = request.files.get('file')

        if not user_id or not lab_type or not file_data:
            return jsonify({"error": "Потрібні user_id, lab_type і файл"}), 400

        if lab_type not in ["esculab", "dila", "sinevo"]:
            return jsonify({"error": "Непідтримувана лабораторія"}), 400

        if not file_data.filename.lower().endswith((".pdf", ".jpg", ".jpeg")):
            return jsonify({"error": "Тільки PDF або JPG файли"}), 400

        results = {}
        if file_data.filename.lower().endswith((".pdf")):
            with pdfplumber.open(file_data) as pdf:
                tables = []
                for page in pdf.pages:
                    tables.extend(tabula.read_pdf(file_data, pages="all", lattice=True, multiple_tables=True, pandas_options={"header": [0]}))
                for table in tables:
                    for _, row in table.iterrows():
                        test_name = row.get("Показник", "").strip()
                        if test_name in TEST_MAPPING:
                            value = float(row.get("Результат", 0).replace(",", "."))
                            unit = row.get("Одиниці вимірювання", "").strip()
                            results[test_name] = {"value": value, "unit": unit}

        elif file_data.filename.lower().endswith((".jpg", ".jpeg")):
            image = Image.open(io.BytesIO(file_data.read()))
            text = pytesseract.image_to_string(image)
            lines = text.split("\n")
            current_test = None
            for line in lines:
                parts = line.strip().split()
                if not parts:
                    continue
                if any(test in line for test in TEST_MAPPING.keys()):
                    current_test = next((k for k, v in TEST_MAPPING.items() if k in line), None)
                elif current_test and len(parts) >= 2:
                    try:
                        value = float(parts[0].replace(",", "."))
                        unit = parts[1] if len(parts) > 1 else "г/л"
                        results[current_test] = {"value": value, "unit": unit}
                    except (IndexError, ValueError):
                        continue

        # Виклик handlers для аналізу
        response = handlers_bp.test_request_context().invoke(
            '/api/handlers/analyze_results',
            method='POST',
            json={"user_id": user_id, "results": results}
        ).get_response()

        return response

    except Exception as e:
        logger.error(f"Error in upload_lab_results: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@app.route('/api/health/diagram', methods=['POST'])
@cross_origin()
def health_diagram():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        diagram_type = data.get('diagram_type', 'radar')

        if not user_id:
            return jsonify({"error": "Потрібен user_id"}), 400

        lab_results = db.find_document("lab_results", {"user_id": user_id})
        if not lab_results:
            return jsonify({"error": "Дані аналізів не знайдено"}), 404

        results = lab_results.get("results", {})
        subscription_active = db.find_document("users", {"user_id": user_id, "subscription_active": True}) is not None

        chart_data = {"sex_hormones": 5, "liver": 5, "kidneys": 5, "gi_tract": 5, "cardiovascular": 5}
        reference_data = [8, 8, 8, 8, 8]

        if diagram_type == "radar":
            for category in chart_data:
                if category == "sex_hormones":
                    value = sum(1 for key in ["testosterone_total"] if key in results and 300 <= results[key]["value"] <= 1000) * 2
                    chart_data[category] = min(max(value, 0), 10)

            chart_config = {
                "type": "radar",
                "data": {
                    "labels": list(chart_data.keys()),
                    "datasets": [
                        {"label": "Твоє здоров’я", "data": list(chart_data.values()), "backgroundColor": "rgba(255, 99, 132, 0.2)", "borderColor": "#FF6384", "borderWidth": 2},
                        {"label": "Ідеальні значення", "data": reference_data, "backgroundColor": "rgba(59, 130, 246, 0.2)", "borderColor": "#3B82F6", "borderWidth": 2}
                    ]
                },
                "options": {"scales": {"r": {"beginAtZero": True, "suggestedMax": 10}}, "animation": {"duration": 1000}}
            }
            sales_message = "Твій тест здоров’я готовий!" if subscription_active else "Покращуй здоров’я — купи преміум!"

        db.insert_document("notifications", {"user_id": user_id, "type": "diagram_request", "message": f"Запит діаграми: {diagram_type}", "created_at": datetime.utcnow()})
        logger.info(f"Diagram generated for {user_id}, type: {diagram_type}")
        return jsonify({"status": "success", "chart_config": chart_config, "sales_message": sales_message})

    except Exception as e:
        logger.error(f"Error in health_diagram: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@app.route('/api/ai/consultation', methods=['POST'])
@cross_origin()
def ai_consultation():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        query = data.get('query')

        if not user_id or not query:
            return jsonify({"error": "Потрібні user_id і query"}), 400

        lab_results = db.find_document("lab_results", {"user_id": user_id})
        if not lab_results:
            return jsonify({"error": "Дані аналізів не знайдено"}), 404

        results = lab_results.get("results", {})
        prompt = f"Консультація для {user_id}. Аналізи: {results}. Запит: {query}. Дай рекомендації."
        response = handlers_bp.test_request_context().invoke(
            '/api/handlers/analyze_results',
            method='POST',
            json={"user_id": user_id, "results": results, "query": query}
        ).get_response()

        return response

    except Exception as e:
        logger.error(f"Error in ai_consultation: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@app.route('/api/nft/offer', methods=['POST'])
@cross_origin()
def offer_nft():
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "Потрібен user_id"}), 400

        message = "Ми створили твій тест здоров’я у вигляді цифрового паспорта! Отримай NFT або файл для відстеження прогресу."
        options = ["wallet", "file"]
        return jsonify({"user_id": user_id, "message": message, "options": options})

    except Exception as e:
        logger.error(f"Error in offer_nft: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@app.route('/api/nft/mint', methods=['POST'])
@cross_origin()
def mint_nft():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        option = data.get('option')
        chain = data.get('chain', 'solana')

        if not user_id or option not in ["wallet", "file"] or chain not in ["solana", "ton", "cedra"]:
            return jsonify({"error": "Неправильний вибір"}), 400

        if option == "wallet":
            result = blockchain.mint_nft(user_id, chain)
            nft_hash = f"nft_{user_id}_{chain}"
            db.insert_document("nft_data", {"user_id": user_id, "nft_id": nft_hash, "chain": chain, "created_at": datetime.utcnow()})
            return jsonify({"status": "coming soon", "message": f"NFT для {chain} створено! Збережіть ID: {nft_hash}.", **result})
        elif option == "file":
            nft_hash = f"nft_{user_id}_file_{chain}"
            db.insert_document("nft_data", {"user_id": user_id, "nft_id": nft_hash, "chain": chain, "created_at": datetime.utcnow()})
            return jsonify({"status": "coming soon", "message": f"Файл NFT створено! Збережіть ID: {nft_hash}.", "nft_id": nft_hash})

    except Exception as e:
        logger.error(f"Error in mint_nft: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@app.route('/api/nft/load', methods=['POST'])
@cross_origin()
def load_nft():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        nft_id = data.get('nft_id')

        if not user_id or not nft_id:
            return jsonify({"error": "Потрібні user_id і nft_id"}), 400

        old_data = db.find_document("nft_data", {"user_id": user_id, "nft_id": nft_id})
        if not old_data:
            return jsonify({"error": "NFT не знайдено"}), 404

        return jsonify({"status": "coming soon", "message": f"Вітаємо, {user_id}! Завантажено тест здоров’я {nft_id}. Додай нові аналізи."})

    except Exception as e:
        logger.error(f"Error in load_nft: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@app.route('/api/web3/placeholder', methods=['POST'])
@cross_origin()
def web3_placeholder():
    return jsonify({
        "status": "coming soon",
        "chains": ["solana", "ton", "cedra"],
        "nft": "ready for mint/load",
        "message": "Web3 для тесту здоров’я в розробці!"
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
