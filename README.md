# Telegram Task Manager Bot Setup

This guide will help you set up your Telegram Task Manager Bot using Python.  

---

## 1. Create a Bot on Telegram

1. Open Telegram and search for **[BotFather](https://t.me/BotFather)**.
2. Start a chat with BotFather and run the command:
```
/newbot
```
3. Follow the instructions:
- **Name your bot**: Example: `Task Manager`
- **Create a username**: Must end with `_bot`. Example: `Task_manager_sagman_bot`
4. After creating the bot, BotFather will provide you with an **HTTP API token**. Example:  
```
8325482995:AAE0ni6AgfcsRBz7AeRWU_Ll3FElnOkxeTU
```
Keep this token safe — you will need it in the next step.

---

## 2. Configure Your Bot in Python

1. Open the file `bot_telegram_task_manager_admin.py`.
2. Replace the `TOKEN` variable with your bot’s HTTP API token:
```python
TOKEN = "YOUR_HTTP_API_TOKEN_HERE"
```


## 3. Set Up Admin Users

To manage the bot, you need to define admin users.

1. Replace the ADMINS set with your Telegram user ID(s):
```
ADMINS = {1083670850}  # <-- replace with your Telegram user_id
```

2. How to find your user ID:

Desktop: Open your Telegram web client, search for your username, click your profile, and copy the link. The last number is your ID.
Example: https://web.telegram.org/a/#1083670850 → 1083670850

Mobile: Use the bot @RawDataBot
 to get your user ID. The bot will return data like:
``` 
"chat": {
  "id": 1083670850,
  "first_name": "Picachu",
  "username": "Sagmanua",
  "type": "private"
}
```
## 4. Test Your Bot

1. Run the Python script:
```
python bot_telegram_task_manager_admin.py
```

2. Open Telegram and try sending commands to your bot.

3. If everything works, you are ready to deploy.


##5. Deploy the Bot to a Server (Optional)

For continuous operation, deploy your bot to a server. Recommended options include:

* PythonAnywhere: Free and beginner-friendly.

[Watch Tutorial here](https://www.youtube.com/watch?v=2TI-tCVhe9k) 




