import sqlite3
import telebot
from telebot import types
from datetime import datetime, timedelta
import threading
import time

# Database Configuration
DATABASE = "tasks.db"

# Telegram Configuration
TOKEN = ""
bot = telebot.TeleBot(TOKEN)

# ---------------- Database Setup ----------------
def setup_database():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            description TEXT,
            due_date TEXT,
            completed BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        conn.commit()


def add_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()


def add_task(user_id, description, due_date):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (user_id, description, due_date, completed) VALUES (?, ?, ?, 0)",
                    (user_id, description, due_date))
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


def get_tasks(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT task_id, description, due_date, completed FROM tasks WHERE user_id=?", (user_id,))
        return cur.fetchall()


def get_upcoming_tasks():
    """Return tasks due tomorrow that are not completed."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, description FROM tasks WHERE due_date=? AND completed=0", (tomorrow,))
        return cur.fetchall()


# ---------------- Telegram Bot Handlers ----------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.chat.id)
    bot.reply_to(
        message,
        "Welcome to the Task Manager Bot!\n"
        "Use /add <task> <YYYY-MM-DD> to add a task with due date.\n"
        "Use /list to list tasks, /delete <task_id> to delete."
    )


@bot.message_handler(commands=['add'])
def add_task_command(message):
    try:
        _, *task_parts, due_date = message.text.split()

        task = " ".join(task_parts)

        # Validate date format
        datetime.strptime(due_date, "%Y-%m-%d")

        add_task(message.chat.id, task, due_date)
        bot.reply_to(message, f"Task '{task}' added with due date {due_date}!")

    except ValueError:
        bot.reply_to(message, "Invalid date format. Use YYYY-MM-DD")
    except Exception:
        bot.reply_to(
            message,
            "Usage: /add <task description> <YYYY-MM-DD>\n"
            "Example: /add Prepare documento of IPE 2026-02-02"
        )



@bot.message_handler(commands=['list'])
def list_tasks_command(message):
    tasks = get_tasks(message.chat.id)
    if not tasks:
        bot.send_message(message.chat.id, "You have no tasks.")
        return

    for task in tasks:
        task_id, description, due_date, completed = task
        status = "✅" if completed else "❌"

        markup = types.InlineKeyboardMarkup()
        button_text = "Mark as Done" if not completed else "Already Done"
        callback_data = f"done_{task_id}" if not completed else "noop"
        markup.add(types.InlineKeyboardButton(text=button_text, callback_data=callback_data))

        bot.send_message(message.chat.id, f"{task_id}. {status} {description} (Due: {due_date})", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
def callback_mark_done(call):
    task_id = int(call.data.split("_")[1])
    mark_completed(task_id)
    bot.answer_callback_query(call.id, "Task marked as done!")
    bot.edit_message_text("✅ Task completed!", call.message.chat.id, call.message.message_id)


@bot.message_handler(commands=['delete'])
def delete_task_command(message):
    task_id = int(message.text.split(' ', 1)[1])
    delete_task(task_id)
    bot.reply_to(message, f"Task {task_id} deleted!")


# ---------------- Reminder Scheduler ----------------

def send_reminders():
    while True:
        upcoming_tasks = get_upcoming_tasks()
        for user_id, description in upcoming_tasks:
            bot.send_message(user_id, f"Reminder: You need to do '{description}' tomorrow!")
        time.sleep(3600)  # Check every hour


# ---------------- Main ----------------
setup_database()

# Start reminder thread
threading.Thread(target=send_reminders, daemon=True).start()

# Start the bot
bot.polling(none_stop=True)
