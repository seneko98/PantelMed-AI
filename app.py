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
import pdfplumber
import tabula
import pytesseract
from PIL import Image
import io
from openai import OpenAI
from medical_knowledge import MedicalCore
from utils.blockchain import BlockchainIntegrator
from ai_recommendations import AIRecommendations

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфігурація
MONGO_URI = "mongodb+srv://Vlad:manreds7@cluster0.d0qnz.mongodb.net/pantelmed?retryWrites=true&w=majority&appName=Cluster0"
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TRON_WALLET = "TQeHa8VdwfyybxtioW4ggbnDC1rbWe8nFa"
OPENAI_API_KEY = "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"
app.config.update({
    "MONGO_URI": MONGO_URI,
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "TRON_WALLET": TRON_WALLET,
    "OPENAI_API_KEY": OPENAI_API_KEY
})

# Ініціалізація
db = Database(MONGO_URI)
blockchain = BlockchainIntegrator()
openai_client = OpenAI(api_key=app.config["OPENAI_API_KEY"])
medical_knowledge = MedicalCore
ai_recommendations = AIRecommendations(
    api_key=app.config["OPENAI_API_KEY"],
    pubmed_api_keys=["2a81afc10a118457d5ba72991d041368e408", "0cc440a547446348b9472fe709029f6ba608"]
)

# Маппінг показників
TEST_MAPPING = {
    "АЛТ (аланінамінотрансфераза)": "alt",
    "АСТ (аспартатамінотрансфераза)": "ast",
    "Білірубін загальний": "bilirubin_total",
    "Білірубін прямий": "bilirubin_direct",
    "ГГТ (гамма-глутамілтрансфераза)": "ggt",
    "Лужна фосфатаза": "alkaline_phosphatase",
    # ... (додай повний список за потреби)
}

# Реєстрація Blueprint'ів
app.register_blueprint(handlers_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(pay_bp)
app.register_blueprint(crm_bp)

@app.route('/api/upload_lab_results', methods=['POST'])
@cross_origin()
def upload_lab_results():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Файл не знайдено"}), 400
        file = request.files['file']
        user_id = request.form.get('user_id')

        if file.filename.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                results = parse_lab_results(text)
        elif file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img = Image.open(io.BytesIO(file.read()))
            text = pytesseract.image_to_string(img)
            results = parse_lab_results(text)
        else:
            return jsonify({"error": "Непідтримуваний формат"}), 400

        if user_id:
            db.insert_document("lab_results", {"user_id": user_id, "results": results, "uploaded_at": datetime.utcnow()})
        recommendations = ai_recommendations.get_recommendations(results)
        pubmed_research = asyncio.run(ai_recommendations.research_pubmed(f"health recommendations {list(results.keys())[0]}"))

        return jsonify({
            "status": "success",
            "results": results,
            "recommendations": recommendations,
            "pubmed_research": pubmed_research
        })

    except Exception as e:
        logger.error(f"Error in upload_lab_results: {str(e)}")
        return jsonify({"error": f"Помилка: {str(e)}"}), 500

@app.route('/api/nft/mint', methods=['POST'])
@cross_origin()
def mint_nft():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        option = data.get('option')  # "wallet" або "file"
        chain = data.get('chain', 'solana')  # За замовчуванням Solana

        if not user_id or not option:
            return jsonify({"error": "Потрібні user_id і option"}), 400
        if option not in ["wallet", "file"] or chain not in ["solana", "ton", "cedra"]:
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
