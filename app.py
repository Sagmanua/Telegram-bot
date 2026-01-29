import sqlite3
import telebot
from telebot import types
from datetime import datetime, timedelta
import threading
import time

# ================= CONFIG =================

DATABASE = "tasks.db"
TOKEN = "8325482995:AAG4oTfmOCZjSGXbhgwL5EoTgCvZzFocP5Q"

# Admin Telegram user IDs
ADMIN_IDS = {1083670850}  # <-- REPLACE WITH REAL IDS

bot = telebot.TeleBot(TOKEN)

# ================= DATABASE =================

def setup_database():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            role TEXT DEFAULT 'user'
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            created_by INTEGER
        )
        """)
        conn.commit()

def add_user(user_id):
    role = "admin" if user_id in ADMIN_IDS else "user"
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users (user_id, role) VALUES (?, ?)",
            (user_id, role)
        )
        conn.commit()

def is_admin(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return row and row[0] == "admin"

# ================= TASK FUNCTIONS =================

def add_task(description, due_date, created_by):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (description, due_date, completed, created_by) VALUES (?, ?, 0, ?)",
            (description, due_date, created_by)
        )
        conn.commit()

def delete_task(task_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
        conn.commit()

def mark_completed(task_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET completed=1 WHERE task_id=?", (task_id,))
        conn.commit()

def get_all_tasks():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT task_id, description, due_date, completed
            FROM tasks
            ORDER BY due_date
        """)
        return cur.fetchall()

def get_upcoming_tasks():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT description FROM tasks
            WHERE due_date=? AND completed=0
        """, (tomorrow,))
        return cur.fetchall()

# ================= BOT COMMANDS =================

@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.chat.id)
    # Using simple text or escaping symbols avoids the "can't parse" error
    text = (
        "📋 *Shared Task Manager*\n\n"
        "/list – View all tasks\n"
        "/add task date – (admins only)\n"
        "/delete id – (admins only)"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_task_command(message):
    if not is_admin(message.chat.id):
        bot.reply_to(message, "⛔ Only admins can add tasks.")
        return

    try:
        _, *task_parts, due_date = message.text.split()
        description = " ".join(task_parts)
        datetime.strptime(due_date, "%Y-%m-%d")

        add_task(description, due_date, message.chat.id)
        bot.reply_to(message, f"✅ Task added:\n{description}\nDue: {due_date}")

    except ValueError:
        bot.reply_to(message, "❌ Invalid date. Use YYYY-MM-DD")
    except Exception:
        bot.reply_to(
            message,
            "Usage:\n/add <task description> <YYYY-MM-DD>\n"
            "Example:\n/add Prepare report 2026-02-02"
        )

@bot.message_handler(commands=['list'])
def list_tasks(message):
    tasks = get_all_tasks()
    if not tasks:
        bot.send_message(message.chat.id, "📭 No tasks yet.")
        return

    for task_id, desc, due, completed in tasks:
        status = "✅" if completed else "❌"
        text = f"{task_id}. {status} {desc}\n📅 Due: {due}"

        markup = None
        if not completed and is_admin(message.chat.id):
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "Mark as done",
                    callback_data=f"done_{task_id}"
                )
            )

        bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("done_"))
def mark_done_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ Admins only")
        return

    task_id = int(call.data.split("_")[1])
    mark_completed(task_id)

    bot.answer_callback_query(call.id, "✅ Task completed")
    bot.edit_message_text(
        "✅ Task completed",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(commands=['delete'])
def delete_task_command(message):
    if not is_admin(message.chat.id):
        bot.reply_to(message, "⛔ Only admins can delete tasks.")
        return

    try:
        task_id = int(message.text.split()[1])
        delete_task(task_id)
        bot.reply_to(message, f"🗑 Task {task_id} deleted.")
    except:
        bot.reply_to(message, "Usage: /delete <task_id>")

# ================= REMINDERS =================

def send_reminders():
    while True:
        tasks = get_upcoming_tasks()
        for (description,) in tasks:
            for admin_id in ADMIN_IDS:
                bot.send_message(
                    admin_id,
                    f"⏰ Reminder: '{description}' is due tomorrow!"
                )
        time.sleep(3600)

# ================= MAIN =================

setup_database()
threading.Thread(target=send_reminders, daemon=True).start()
bot.polling(none_stop=True)
