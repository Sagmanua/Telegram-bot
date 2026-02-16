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
    # ... (Other languages from your original code)
    "ru": {
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

def get_weather(city, lang="en"):
    try:
        t = TEXT.get(lang, TEXT["en"])
        
        # 1. GEOCODING: Convert city name to Coordinates
        encoded_city = urllib.parse.quote(city)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language={lang}&format=json"
        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return "⚠️ City not found"

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        full_name = f"{location['name']}, {location.get('country', '')}"

        # 2. WEATHER: Fetch data using coordinates
        # We request daily max/min and hourly data for specific times
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&hourly=temperature_2m,precipitation_probability&timezone=auto"
        )
        
        weather_res = requests.get(weather_url, timeout=10)
        data = weather_res.json()

        # Extract Daily Info
        max_temp = data["daily"]["temperature_2m_max"][0]
        min_temp = data["daily"]["temperature_2m_min"][0]
        avg_temp = round((max_temp + min_temp) / 2, 1)
        rain_prob = data["daily"]["precipitation_probability_max"][0]

        # Extract Hourly Info (Indices: 8am, 1pm, 6pm, 11pm roughly)
        hourly_temps = data["hourly"]["temperature_2m"]
        morn = hourly_temps[8]
        day  = hourly_temps[13]
        eve  = hourly_temps[18]
        nite = hourly_temps[23]

        rain_text = t["rain_yes"] if rain_prob > 50 else t["rain_no"]

        return (
            f"{t['forecast']} {full_name}\n"
            f"{rain_text} ({rain_prob}%)\n\n"
            f"{t['morning']}: {morn}°C\n"
            f"{t['day']}: {day}°C\n"
            f"{t['evening']}: {eve}°C\n"
            f"{t['night']}: {nite}°C\n\n"
            f"{t['max']}: {max_temp}°C\n"
            f"{t['min']}: {min_temp}°C\n"
            f"{t['avg']}: {avg_temp}°C"
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

if __name__ == "__main__":
    setup_database()
    threading.Thread(target=scheduler, daemon=True).start()
    print("Bot running with Open-Meteo...")
    bot.polling(none_stop=True)