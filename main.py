import os
import openai
import telegram
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import asyncio
import uvicorn
from telegram import Update
from telegram.ext import Application

# Çevresel değişkenleri yükle
load_dotenv()

# Çevresel değişkenlerden API anahtarlarını al
openai_api_key = os.getenv("openai_api_key")
telegram_bot_key = os.getenv("telegram_bot_key")

# OpenAI API anahtarını ayarla
openai.api_key = openai_api_key

# Telegram bot objesi (Asenkron)
bot = telegram.Bot(token=telegram_bot_key)

# Webhook URL'sini Telegram'a bildiriyoruz
webhook_url = "kendi sunucunuzu girin /webhook unutmayin."

# FastAPI başlat
app = FastAPI()

@app.get("/")
async def hello_world():
    return {"message": "Hello, World!"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    chat_id = update.message.chat.id
    message_text = update.message.text

    try:
        # OpenAI GPT-3.5-turbo'ya istek
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message_text}]
        )

        response_content = response['choices'][0]['message']['content']
        
        # Yanıtı Telegram kullanıcısına gönder
        await bot.send_message(chat_id=chat_id, text=response_content)

    except Exception as e:
        # Hata durumunda Telegram'a hata mesajı gönder
        await bot.send_message(chat_id=chat_id, text="Üzgünüm, bir hata oluştu.")
        print(f"Hata: {e}")

    return {"status": "ok"}

async def setup_webhook():
    application = Application.builder().token(telegram_bot_key).build()
    await application.bot.set_webhook(url=webhook_url)
    print(f"Webhook başarıyla ayarlandı: {webhook_url}")

@app.on_event("startup")
async def startup_event():
    await setup_webhook()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
