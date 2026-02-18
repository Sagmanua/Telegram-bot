import sqlite3
import telebot
from datetime import datetime
import threading
import time
import requests
import os
import urllib.parse  # Added for safe city name encoding
from dotenv import load_dotenv

load_dotenv()


TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

DATABASE = "tasks_weather.db"

# ---------------- TEXT TRANSLATIONS ----------------
TEXT = {
    "en": {
        "welcome": "Welcome! Use:\n/weather London\n/time London 09:20\n/week London",
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
        "welcome": "¡Bienvenido! Usa:\n/weather Madrid\n/time Madrid 09:20\n/week Madrid",
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
        "welcome": "Bienvenue ! Utilisez :\n/weather Paris\n/time Paris 09:20\n/week Paris",
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
        "welcome": "Willkommen! Nutze:\n/weather Berlin\n/time Berlin 09:20\n/week Berlin",
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
        "welcome": "Benvenuto! Usa:\n/weather Roma\n/time Roma 09:20\n/week Roma",
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
        "welcome": "Bem-vindo! Use:\n/weather Lisboa\n/time Lisboa 09:20\n/week Lisboa",
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
        "welcome": "Добро пожаловать! Используйте:\n/weather Киев\n/time Киев 09:20\n/week Киев",
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
        "welcome": "Вітаємо! Використовуйте:\n/weather Київ\n/time Київ 09:20\n/week Київ",
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
# (Keep all your existing database functions exactly as they are)
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

# ---------------- WEATHER (OPEN-METEO) ----------------

# ---------------- WEATHER (OPEN-METEO) ----------------

def get_weather(city, lang="en", weekly=False):
    try:
        t = TEXT.get(lang, TEXT["en"])
        
        # 1. GEOCODING
        encoded_city = urllib.parse.quote(city)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language={lang}&format=json"
        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return "⚠️ City not found"

        location = geo_data["results"][0]
        lat, lon = location["latitude"], location["longitude"]
        full_name = f"{location['name']}, {location.get('country', '')}"

        # 2. WEATHER API CALL
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode"
            f"&hourly=temperature_2m&timezone=auto"
        )
        
        data = requests.get(weather_url, timeout=10).json()
        daily = data["daily"]

        if weekly:
            # Generate 7-day forecast string
            forecast_msg = f"📅 **7-Day Forecast: {full_name}**\n\n"
            for i in range(7):
                date_obj = datetime.strptime(daily["time"][i], "%Y-%m-%d")
                date_str = date_obj.strftime("%a %d/%m") # e.g., Mon 15/05
                max_t = daily["temperature_2m_max"][i]
                min_t = daily["temperature_2m_min"][i]
                prob = daily["precipitation_probability_max"][i]
                
                emoji = "☀️" if prob < 20 else "☁️" if prob < 50 else "🌧"
                forecast_msg += f"{date_str}: {emoji} {max_t}° / {min_t}°C ({prob}%)\n"
            return forecast_msg

        # Standard daily logic (Keep your original daily formatting here)
        max_temp = daily["temperature_2m_max"][0]
        min_temp = daily["temperature_2m_min"][0]
        rain_prob = daily["precipitation_probability_max"][0]
        
        # Hourly indices for today
        hourly_temps = data["hourly"]["temperature_2m"]
        rain_text = t["rain_yes"] if rain_prob > 50 else t["rain_no"]

        return (
            f"{t['forecast']} {full_name}\n"
            f"{rain_text} ({rain_prob}%)\n\n"
            f"{t['morning']}: {hourly_temps[8]}°C\n"
            f"{t['day']}: {hourly_temps[13]}°C\n"
            f"{t['evening']}: {hourly_temps[18]}°C\n"
            f"{t['night']}: {hourly_temps[23]}°C\n\n"
            f"{t['max']}: {max_temp}°C | {t['min']}: {min_temp}°C"
        )
    except Exception as e:
        print(f"Weather Error: {e}")
        return "⚠️ Weather error"

# ---------------- SCHEDULER & COMMANDS ----------------
# (Keep all your existing scheduler and command handlers exactly as they are)

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
            bot.reply_to(message, "Available: en, es, fr, de, it, pt, ru, ua")
            return
        set_language(message.chat.id, lang)
        bot.reply_to(message, f"Language set to {lang}")
    except:
        bot.reply_to(message, "Usage: /lang en")

@bot.message_handler(commands=['time'])
def add(message):
    try:
        parts = message.text.split(maxsplit=2)
        city, time_str = parts[1], parts[2]
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


@bot.message_handler(commands=['week'])
def weekly_forecast(message):
    text = message.text.split()
    if len(text) > 1:
        city = " ".join(text[1:])
        lang = get_user_lang(message.chat.id)
        # Call get_weather with weekly=True
        bot.reply_to(message, get_weather(city, lang, weekly=True), parse_mode="Markdown")
    else:
        bot.reply_to(message, "Usage: /week Paris")

if __name__ == "__main__":
    setup_database()
    threading.Thread(target=scheduler, daemon=True).start()
    print("Bot running with Open-Meteo...")
    bot.polling(none_stop=True)