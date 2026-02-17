import telebot
import feedparser
import schedule
import time
import threading
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


TOKEN = os.getenv("TEST_TOKEN")
bot = telebot.TeleBot(TOKEN)

bot = telebot.TeleBot(TOKEN)

# Store user schedules
user_schedules = {}


# ---------- NEWS FUNCTION ----------
def get_news(topic="WORLD"):
    topic_upper = topic.upper()

    # Official Google News topics
    valid_topics = [
        "WORLD", "NATION", "BUSINESS", "TECHNOLOGY",
        "ENTERTAINMENT", "SPORTS", "SCIENCE", "HEALTH"
    ]

    try:
        # If topic is official → use topic endpoint
        if topic_upper in valid_topics:
            url = f"https://news.google.com/rss/headlines/section/topic/{topic_upper}?hl=en-US&gl=US&ceid=US:en"
        else:
            # Otherwise → use search (works for Ukraine, Spain, AI, etc.)
            url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"

        feed = feedparser.parse(url)

        if not feed.entries:
            return f"❌ No news found for {topic}"

        report = f"📰 Top news about {topic}:\n\n"

        for entry in feed.entries[:5]:
            report += f"🔹 {entry.title}\n📅 {entry.published}\n🔗 {entry.link}\n\n"

        return report

    except Exception as e:
        return f"⚠️ Error: {e}"



# ---------- COMMANDS ----------

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 "👋 Hello!\n\n"
                 "Commands:\n"
                 "/news <topic> - get latest news\n"
                 "/time_news <topic> HH:MM - schedule daily news\n\n"
                 "Example:\n"
                 "/news World\n"
                 "/time_news Ukraine 09:20")


@bot.message_handler(commands=['news'])
def send_news(message):
    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, "❗ Usage: /news <topic>")
            return

        topic = parts[1]
        news = get_news(topic)

        bot.send_message(message.chat.id, news)

    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")


@bot.message_handler(commands=['time_news'])
def schedule_news(message):
    try:
        parts = message.text.split()

        if len(parts) < 3:
            bot.reply_to(message, "❗ Usage: /time_news <topic> HH:MM")
            return

        topic = parts[1]
        time_str = parts[2]

        # Validate time format
        datetime.strptime(time_str, "%H:%M")

        chat_id = message.chat.id

        # Save schedule
        if chat_id not in user_schedules:
            user_schedules[chat_id] = []

        user_schedules[chat_id].append((topic, time_str))

        # Schedule job
        schedule.every().day.at(time_str).do(send_scheduled_news, chat_id, topic)

        bot.reply_to(message, f"✅ Scheduled {topic} news at {time_str}")

    except ValueError:
        bot.reply_to(message, "❗ Time format must be HH:MM")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


# ---------- SCHEDULED TASK ----------

def send_scheduled_news(chat_id, topic):
    news = get_news(topic)
    bot.send_message(chat_id, news)


# ---------- SCHEDULER THREAD ----------

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


threading.Thread(target=run_scheduler, daemon=True).start()


# ---------- RUN BOT ----------

print("Bot is running...")
bot.infinity_polling()
