import os
import random
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, send_from_directory
from flask import send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Завантажуємо дані з .env (переконайся, що файл .env лежить поруч)
load_dotenv()

app = Flask(__name__)
# Налаштовуємо CORS, щоб браузер дозволяв запити
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Дані з твого .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_CHAT_ID")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")

DATA_FILE = 'products.json'
auth_codes = {}

def send_email_code(target_email, code):
    """Відправка коду через Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = target_email
        msg['Subject'] = "Код підтвердження LUNXET"

        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; text-align: center;">
                <h2 style="color: #111;">Ваш код входу в LUNXET MART</h2>
                <div style="font-size: 32px; font-weight: bold; color: #cdef2e; background: #111; padding: 20px; display: inline-block; border-radius: 10px;">
                    {code}
                </div>
                <p style="color: #666; margin-top: 20px;">Якщо ви не запитували цей код, просто ігноруйте цей лист.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, target_email, msg.as_string())
        return True
    except Exception as e:
        print(f"❌ Помилка Email: {e}")
        return False

@app.route('/')
def index():
    return send_from_directory('static', 'sitr.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/api/products', methods=['GET'])
def get_products():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return jsonify(json.load(f))
            except:
                return jsonify([])
    return jsonify([])

# ГОЛОВНИЙ МАРШРУТ АВТОРИЗАЦІЇ (ВИПРАВЛЕНО)
@app.route('/api/auth/request', methods=['POST', 'OPTIONS'])
def send_auth_code():
    if request.method == 'OPTIONS':
        return jsonify({"success": True}), 200
        
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
        
    contact = data.get('contact', '').strip()
    if not contact:
        return jsonify({"success": False, "message": "Вкажіть контакт"}), 400
        
    code = str(random.randint(1000, 9999))
    auth_codes[contact] = code
    
    print(f"--- НОВИЙ ЗАПИТ ---")
    print(f"Контакт: {contact} | Код: {code}")

    # Перевірка: пошта чи телефон/логін
    if "@" in contact:
        if send_email_code(contact, code):
            print(f"✅ Код надіслано на Email: {contact}")
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Помилка відправки Email"}), 500
    else:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            msg = f"🔑 Код LUNXET: {code}\n👤 Користувач: {contact}"
            requests.post(url, json={"chat_id": ADMIN_ID, "text": msg})
            print(f"✅ Код надіслано в Telegram")
            return jsonify({"success": True})
        except Exception as e:
            print(f"❌ Помилка TG: {e}")
            return jsonify({"success": False, "message": "Помилка Telegram-бота"}), 500

@app.route('/api/auth/verify', methods=['POST', 'OPTIONS'])
def verify_auth_code():
    if request.method == 'OPTIONS':
        return jsonify({"success": True}), 200
        
    data = request.json
    contact = data.get('contact', '').strip()
    code = data.get('code', '').strip()
    
    print(f"--- ПЕРЕВІРКА ---")
    print(f"Спроба входу: {contact} з кодом {code}")

    if contact in auth_codes and str(auth_codes[contact]) == str(code):
        del auth_codes[contact] # Видаляємо код після успішного входу
        return jsonify({"success": True})
    
    return jsonify({"success": False, "message": "Невірний код"}), 401

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    # Запускаємо на 5000 порту
    app.run(debug=True, port=5000)