import os
from telethon import TelegramClient


# DefaultSettings
bot_token = #Ваш_бот_токен
api_id = #Ваш api_id
api_hash = #Ваш api_hash
phone_number = #Ваш phone_number
bot_session_file = os.path.join("bot", "session", "bot_session_file.session")
default_user_session_file = os.path.join("bot", "session", "default_session_file.session")
bot_client = TelegramClient(bot_session_file, api_id, api_hash)
default_user_client = TelegramClient(default_user_session_file, api_id, api_hash)
user_data = {}
allowed_ids = #Права доступа к боту по user_id
