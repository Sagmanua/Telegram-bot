import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = "8182839317:AAGXpUkF752N2Ap-01HBgiU_Im-Wq__P6YI"  
OLLAMA_URL = "https://superadaptably-arrowless-leann.ngrok-free.dev"
MODEL = "llama3:latest"

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Task Manager Bot\n"
        "Use:\n"
        "/Questing your message"
    )

async def questing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Please write text after /Questing")
        return

    text = " ".join(context.args)

    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": text}],
            "stream": False
        },
        timeout=60
    )

    answer = r.json()["message"]["content"]
    await update.message.reply_text(answer)

# ===== APP =====
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("Questing", questing))

print("Bot running...")
app.run_polling()
