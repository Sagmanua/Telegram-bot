import sqlite3
import telebot
from telebot import types
from datetime import datetime, timedelta
import threading
import time
import requests
import os

from dotenv import load_dotenv

load_dotenv()


TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Database Configuration
DATABASE = "tasks_weather.db"


def setup_database():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            city TEXT,
            time TEXT

        )''')

def add_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def add_weather(user_id, city, date):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("""
        UPDATE users
        SET city = ?, time = ?
        WHERE user_id = ?
        """, (city, date, user_id))

def get_all_users():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, city, time FROM users WHERE city IS NOT NULL")
        return cur.fetchall()

def scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")

        users = get_all_users()

        for user_id, city, user_time in users:
            if user_time == now:
                weather = get_weather(city)
                try:
                    bot.send_message(user_id, f"🌅 Daily weather for {city}\n{weather}")
                except:
                    pass

        time.sleep(60)  # check every minute


# Telegram Configuration


def get_weather(city):
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url, timeout=10)
    data = response.json()

    temp = data['current_condition'][0]['temp_C']
    desc = data['current_condition'][0]['weatherDesc'][0]['value']

    return f"🌤 It is currently {temp}°C in {city} with {desc}."



@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.chat.id)
    bot.reply_to(message, "Welcome to the Task Weather Bot!\nUse /weather <City>")


@bot.message_handler(commands=['add'])
def set_city(message):
    try:
        _, city, time_str = message.text.split(maxsplit=2)

        # validate time format
        datetime.strptime(time_str, "%H:%M")

        add_user(message.chat.id)
        add_weather(message.chat.id, city, time_str)

        bot.reply_to(message, f"📍 City: {city}\n⏰ Daily at: {time_str}")

    except:
        bot.reply_to(message,
        "Usage:\n/add London 08:00\nTime format: HH:MM (24h)")



@bot.message_handler(commands=['weather'])
def send_welcome(message):
    text = message.text.split()

    if len(text) > 1:
        city = " ".join(text[1:]) # Join in case the city has spaces like "New York"
        report = get_weather(city)
        bot.reply_to(message, report)
    else:
        bot.reply_to(message, "Please provide a city name. Example: `/weather Paris`")

if __name__ == "__main__":
    setup_database()

    threading.Thread(target=scheduler, daemon=True).start()

    print("Bot is running...")
    bot.polling(none_stop=True)


