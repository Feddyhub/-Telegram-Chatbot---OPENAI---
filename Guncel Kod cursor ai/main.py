import os
import openai
import telegram
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import asyncio
import uvicorn
from telegram import Update
from telegram.ext import Application
from telegram.error import TelegramError
import json

# Çevresel değişkenleri yükle
load_dotenv()

# Çevresel değişkenlerden API anahtarlarını al
openai_api_key = os.getenv("openai_api_key")
telegram_bot_key = os.getenv("telegram_bot_key")

# OpenAI API anahtarını ayarla
openai.api_key = openai_api_key

# FastAPI başlat
app = FastAPI()

# Webhook URL bileşenleri
WEBHOOK_HOST = "SUNUCU ADRESINI YAZ"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = None

# Telegram bot nesnesi
bot = None

async def initialize_bot():
    global bot
    try:
        bot = telegram.Bot(token=telegram_bot_key)
        await bot.get_me()  # Bot'un çalıştığını kontrol eder
        print("Bot başarıyla başlatıldı")
    except TelegramError as e:
        print(f"Bot başlatma hatası: {e}")
        raise HTTPException(status_code=500, detail="Bot başlatılamadı")

async def get_webhook_url():
    global WEBHOOK_URL
    WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"
    return WEBHOOK_URL

@app.get("/")
async def hello_world():
    return {"message": "Hello, World!"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
      
        update = Update.de_json(data, bot)

        
        message = update.message if update.message else update.edited_message
        if not message:
            raise HTTPException(status_code=400, detail="Geçersiz update verisi")
        
        chat_id = message.chat.id
        message_text = message.text

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message_text}]
            )
            response_content = response['choices'][0]['message']['content']
            await bot.send_message(chat_id=chat_id, text=response_content)
        except Exception as e:
            error_message = "Üzgünüm, bir hata oluştu."
            await bot.send_message(chat_id=chat_id, text=error_message)
            print(f"OpenAI veya Telegram hatası: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

        return {"status": "ok"}
    except Exception as e:
        print(f"Genel hata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def setup_webhook():
    try:
        if not WEBHOOK_URL:
            await get_webhook_url()
        
        application = Application.builder().token(telegram_bot_key).build()
        await application.bot.set_webhook(url=WEBHOOK_URL)
      #  print(f"Webhook başarıyla ayarlandı: {WEBHOOK_URL}")
    except Exception as e:
        print(f"Webhook kurulum hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook kurulamadı")

@app.on_event("startup")
async def startup_event():
    try:
       # print("Uygulama başlatılıyor...")
        await initialize_bot()
        await setup_webhook()
    except Exception as e:
        print(f"Startup hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Uygulama başlatılamadı")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)