import sqlite3
import telebot
from datetime import datetime
import threading
import time
import requests
import os

TOKEN = ""
bot = telebot.TeleBot(TOKEN)

DATABASE = "tasks_weather.db"

# ---------------- TEXT TRANSLATIONS ----------------
TEXT = {
    "en": {
        "welcome": "Welcome! Use /add <city> <HH:MM>",
        "rain_yes": "🌧 Rain expected",
        "rain_no": "☀️ No rain expected",
        "forecast": "📅 Forecast for",
        "morning": "🌅 Morning",
        "day": "🌞 Day",
        "evening": "🌆 Evening",
        "night": "🌙 Night",
        "max": "⬆️ Max",
        "min": "⬇️ Min",
        "avg": "🌡 Avg",
    },
    "es": {
        "welcome": "¡Bienvenido! Usa /add <ciudad> <HH:MM>",
        "rain_yes": "🌧 Lluvia probable",
        "rain_no": "☀️ Sin lluvia",
        "forecast": "📅 Pronóstico para",
        "morning": "🌅 Mañana",
        "day": "🌞 Día",
        "evening": "🌆 Tarde",
        "night": "🌙 Noche",
        "max": "⬆️ Máx",
        "min": "⬇️ Mín",
        "avg": "🌡 Prom",
    },
    "fr": {
        "welcome": "Bienvenue ! Utilisez /add <ville> <HH:MM>",
        "rain_yes": "🌧 Pluie prévue",
        "rain_no": "☀️ Pas de pluie prévue",
        "forecast": "📅 Prévisions pour",
        "morning": "🌅 Matin",
        "day": "🌞 Journée",
        "evening": "🌆 Soirée",
        "night": "🌙 Nuit",
        "max": "⬆️ Max",
        "min": "⬇️ Min",
        "avg": "🌡 Moy",
    },
    "de": {
        "welcome": "Willkommen! Nutze /add <Stadt> <HH:MM>",
        "rain_yes": "🌧 Regen erwartet",
        "rain_no": "☀️ Kein Regen erwartet",
        "forecast": "📅 Vorhersage für",
        "morning": "🌅 Morgen",
        "day": "🌞 Tag",
        "evening": "🌆 Abend",
        "night": "🌙 Nacht",
        "max": "⬆️ Max",
        "min": "⬇️ Min",
        "avg": "🌡 Schn",
    },
    "it": {
        "welcome": "Benvenuto! Usa /add <città> <HH:MM>",
        "rain_yes": "🌧 Pioggia prevista",
        "rain_no": "☀️ Niente pioggia",
        "forecast": "📅 Meteo per",
        "morning": "🌅 Mattina",
        "day": "🌞 Giorno",
        "evening": "🌆 Sera",
        "night": "🌙 Notte",
        "max": "⬆️ Max",
        "min": "⬇️ Min",
        "avg": "🌡 Media",
    },
    "pt": {
        "welcome": "Bem-vindo! Use /add <cidade> <HH:MM>",
        "rain_yes": "🌧 Chuva esperada",
        "rain_no": "☀️ Sem chuva",
        "forecast": "📅 Previsão para",
        "morning": "🌅 Manhã",
        "day": "🌞 Dia",
        "evening": "🌆 Tarde",
        "night": "🌙 Noite",
        "max": "⬆️ Máx",
        "min": "⬇️ Mín",
        "avg": "🌡 Méd",
    },
    "ru": {
        "welcome": "Добро пожаловать! Используйте /add <город> <ЧЧ:ММ>",
        "rain_yes": "🌧 Ожидается дождь",
        "rain_no": "☀️ Без осадков",
        "forecast": "📅 Прогноз для",
        "morning": "🌅 Утро",
        "day": "🌞 День",
        "evening": "🌆 Вечер",
        "night": "🌙 Ночь",
        "max": "⬆️ Макс",
        "min": "⬇️ Мин",
        "avg": "🌡 Сред",
    },
    "ua": {
        "welcome": "Вітаємо! Використовуйте /add <місто> <ГГ:ХХ>",
        "rain_yes": "🌧 Очікується дощ",
        "rain_no": "☀️ Без опадів",
        "forecast": "📅 Прогноз для",
        "morning": "🌅 Ранок",
        "day": "🌞 День",
        "evening": "🌆 Вечір",
        "night": "🌙 Ніч",
        "max": "⬆️ Макс",
        "min": "⬇️ Мін",
        "avg": "🌡 Середня",
    }
}

# ---------------- DATABASE ----------------

def setup_database():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            city TEXT,
            time TEXT,
            lang TEXT DEFAULT 'en'
        )
        """)

def add_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))

def set_language(user_id, lang):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))

def get_user_lang(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
        r = cur.fetchone()
        return r[0] if r else "en"

def add_weather(user_id, city, time_str):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET city=?, time=? WHERE user_id=?", (city, time_str, user_id))

def get_all_users():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, city, time, lang FROM users WHERE city IS NOT NULL")
        return cur.fetchall()

# ---------------- WEATHER ----------------

def get_weather(city, lang="en"):
    try:
        t = TEXT.get(lang, TEXT["en"])
        # Adding a User-Agent helps avoid some blocks
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://wttr.in/{city}?format=j1&lang={lang}"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        
        # Check if the request actually succeeded
        if response.status_code != 200:
            return f"⚠️ Server Error: {response.status_code}"
        
        data = response.json()

        forecast = data["weather"][0]

        avg = forecast["avgtempC"]
        min_temp = forecast["mintempC"]
        max_temp = forecast["maxtempC"]
        desc = forecast["hourly"][4]["weatherDesc"][0]["value"]

        morning = forecast["hourly"][2]["tempC"]
        day = forecast["hourly"][4]["tempC"]
        evening = forecast["hourly"][6]["tempC"]
        night = forecast["hourly"][7]["tempC"]

        rain = forecast["hourly"][4]["chanceofrain"]
        rain_text = t["rain_yes"] if int(rain) > 50 else t["rain_no"]

        return (
            f"{t['forecast']} {city}\n"
            f"{rain_text}\n\n"
            f"{t['morning']}: {morning}°C\n"
            f"{t['day']}: {day}°C\n"
            f"{t['evening']}: {evening}°C\n"
            f"{t['night']}: {night}°C\n\n"
            f"{t['max']}: {max_temp}°C\n"
            f"{t['min']}: {min_temp}°C\n"
            f"{t['avg']}: {avg}°C\n"
            f"📝 {desc}"
        )
    except:
        return "⚠️ Weather error"

# ---------------- SCHEDULER ----------------

def scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")

        for user_id, city, user_time, lang in get_all_users():
            if user_time == now:
                try:
                    bot.send_message(user_id, get_weather(city, lang))
                except:
                    pass

        time.sleep(60 - datetime.now().second)

# ---------------- COMMANDS ----------------

@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.chat.id)

    user_lang = message.from_user.language_code
    if user_lang in TEXT:
        set_language(message.chat.id, user_lang)

    lang = get_user_lang(message.chat.id)
    bot.reply_to(message, TEXT[lang]["welcome"])

@bot.message_handler(commands=['lang'])
def language(message):
    try:
        lang = message.text.split()[1].lower()
        if lang not in TEXT:
            bot.reply_to(message, "Available: en, es")
            return
        set_language(message.chat.id, lang)
        bot.reply_to(message, f"Language set to {lang}")
    except:
        bot.reply_to(message, "Usage: /lang en")

@bot.message_handler(commands=['time'])
def add(message):
    try:
        _, city, time_str = message.text.split(maxsplit=2)
        datetime.strptime(time_str, "%H:%M")

        add_user(message.chat.id)
        add_weather(message.chat.id, city, time_str)

        bot.reply_to(message, f"Saved: {city} at {time_str}")
    except:
        bot.reply_to(message, "Usage: /time London 08:00")

@bot.message_handler(commands=['weather'])
def weather(message):
    text = message.text.split()

    if len(text) > 1:
        city = " ".join(text[1:])
        lang = get_user_lang(message.chat.id)
        bot.reply_to(message, get_weather(city, lang))
    else:
        bot.reply_to(message, "Example: /weather Paris")

# ---------------- MAIN ----------------

if __name__ == "__main__":
    setup_database()
    threading.Thread(target=scheduler, daemon=True).start()
    print("Bot running...")
    bot.polling(none_stop=True)
