import os
import python_socks
import socks
import asyncio
import async_timeout
from telethon import TelegramClient, events, functions
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.sync import TelegramClient
from validation import ipv4_pattern, ipv6_pattern
from logger import logger
from config import bot_client, default_user_client, user_data


'''
async def parse_group_userid(group_link: str) -> str:
    group = await bot_client.get_entity(group_link)

    participants = []
    async for participant in bot_client.iter_participants(group):
        participants.append(participant.id)

    if participants:
        file_path = "group_members.txt"
        with open(file_path, "w") as file:
            for participant_id in participants:
                file.write(f"{participant_id}\n")
        return file_path
    else:
        return None
'''
async def parse_group_usernames(event, group_link: str) -> str:
    try:
        await default_user_client.connect()
        group = await default_user_client.get_entity(group_link)

        if group:
            await default_user_client(JoinChannelRequest(group))
        else:
            print("У этого канала нет обсуждения")
            await event.respond("У этого канала нет обсуждения, мониторинг остановлен") 
            return
            
        participants = []
        async for participant in default_user_client.iter_participants(group):
                participants.append(participant.username)

        await default_user_client.disconnect()

        if participants:
            file_path = os.path.join("bot", "downloads", "group_usernames.txt")
            with open(file_path, "w") as file:
                for username in participants:
                    file.write(f"{username}\n")
            return file_path
        else: 
            return None
    except Exception as e:
        print(f"Ошибка при парсинге группы: {e}")
        event.respond(f"Ошибка при парсинге группы: {e}")

async def handle_account_authorization(event, accounts_file: str, proxy_file: str, proxy_type: str):
    account_index = 0 
    proxy_index = 0  
    user_session_folder = await create_session_folder(event) 

    if accounts_file:
        accounts = await read_account(accounts_file)
    else:
        print("Файл с аккаунтами не найден")
        await event.respond("Файл с аккаунтами не найден, авторизация остановлена")
        return
        
    if proxy_file and proxy_type:
        proxy = await read_proxy(proxy_file, proxy_type)
    else:
        print("Файл с прокси не найден")
        proxy = None

    for account_index in range(len(accounts)):
        phone_number = accounts[account_index][2]
        print(f"Авторизация с аккаунтом {account_index} по номеру {phone_number}...")
        await event.respond(f"Авторизация с аккаунтом {account_index} по номеру {phone_number}...")
        await auto_autorization(event, accounts, proxy, account_index, proxy_index, user_session_folder)
                  
        if proxy:
            proxy_index = (proxy_index + 1) % len(proxy)
    
    print("Все аккаунты авторизованы")

async def auto_autorization(event, accounts: list, proxy: list, account_index: int, proxy_index: int, user_session_folder: str) -> TelegramClient:
    api_id, api_hash, phone_number = accounts[account_index] 
                         
    if not os.path.exists(user_session_folder):
        os.makedirs(user_session_folder)

    user_session_file = os.path.join(user_session_folder, f"session_{phone_number}")

    if proxy:
        proxy_addr, proxy_port, proxy_username, proxy_password, proxy_type = proxy[proxy_index]

        if proxy_type == "socks5":
            if proxy_username and proxy_password:
                proxy = (python_socks.ProxyType.SOCKS5, proxy_addr, proxy_port, True, proxy_username, proxy_password)
            else:
                proxy = (python_socks.ProxyType.SOCKS5, proxy_addr, proxy_port, True)
        elif proxy_type == "http":
            if proxy_username and proxy_password:
                proxy = (python_socks.ProxyType.HTTP, proxy_addr, proxy_port, True, proxy_username, proxy_password)
            else:
                proxy = (python_socks.ProxyType.HTTP, proxy_addr, proxy_port, True)
        else:
            raise ValueError("Неподдерживаемый тип прокси")

        user_client = TelegramClient(user_session_file, api_id, api_hash, proxy=proxy)
    else:
        user_client = TelegramClient(user_session_file, api_id, api_hash)
        
    if not user_client.is_connected():
        await user_client.connect()
        if not await user_client.is_user_authorized():
            print("Ожидание кода подтверждения...")
            await user_client.send_code_request(phone_number)
            await event.respond("Введите код для входа в Telegram через пробелы в таком формате '3 1 2 5 6 0': ")

            user_data[event.sender_id] = {"action": "awaiting_code"}
            action = user_data.get(event.sender_id, {}).get("action")

            @bot_client.on(events.NewMessage(incoming=True))
            async def handle_new_message(event): 
                if action == "awaiting_code": 
                    code = event.message.text.replace(" ", "").strip()
                try:
                    await user_client.sign_in(phone_number, code)
                    if await user_client.is_user_authorized():
                        print(f"Код подтверждения для {phone_number} введен, авторизация завершена!")
                        await event.respond(f"Авторизация для {phone_number} успешна!")
                        bot_client.remove_event_handler(handle_new_message)
                    else:
                        raise Exception("Неправильный код")
                except Exception as e:
                    print(f"Ошибка авторизации: {e}")
                    await event.respond(f"Ошибка авторизации: {e}. Попробуйте еще раз, введите код:")
            while not await user_client.is_user_authorized():
                await asyncio.sleep(2)  
        else:
            print("Клиент уже авторизован")
            await event.respond("Клиент уже авторизован")
                
    await user_client.disconnect()
    return user_client

async def auto_login(accounts: list, proxy: list, account_index: int, proxy_index: int, user_session_folder: str) -> TelegramClient:
    api_id, api_hash, phone_number = accounts[account_index]  
                       
    if not os.path.exists(user_session_folder):
        os.makedirs(user_session_folder)

    user_session_file = os.path.join(user_session_folder, f"session_{phone_number}")

    if proxy:
        proxy_addr, proxy_port, proxy_username, proxy_password, proxy_type = proxy[proxy_index]

        if proxy_type == "socks5":
            if proxy_username and proxy_password:
                proxy = (python_socks.ProxyType.SOCKS5, proxy_addr, proxy_port, True, proxy_username, proxy_password)
            else:
                proxy = (python_socks.ProxyType.SOCKS5, proxy_addr, proxy_port, True)
        elif proxy_type == "http":
            if proxy_username and proxy_password:
                proxy = (python_socks.ProxyType.HTTP, proxy_addr, proxy_port, True, proxy_username, proxy_password)
            else:
                proxy = (python_socks.ProxyType.HTTP, proxy_addr, proxy_port, True)
        else:
            raise ValueError("Неподдерживаемый тип прокси")

        user_client = TelegramClient(user_session_file, api_id, api_hash, proxy=proxy)
    else:
        user_client = TelegramClient(user_session_file, api_id, api_hash)
        
    return user_client

async def send_messages_auto(event, accounts_file: str, proxy_file: str, proxy_type: str, message_count: int, interval: int, message: str, group_link: str) -> None:
    user_session_folder = await create_session_folder(event)

    usernames_file = await parse_group_usernames(event, group_link)
    if usernames_file:
        usernames = await read_usernames(usernames_file)
    else:
        print("В чате нет участников или участники не имеют username")
        await event.respond("В чате нет участников или участники не имеют username")
        return
    
    user_client = None  
    account_index = 0  
    proxy_index = 0

    if accounts_file:
        accounts = await read_account(accounts_file)
    else:
        print("Файл с аккаунтами не найден")
        await event.respond("Файл с аккаунтами не найден, рассылка остановлена")
        return
    
    if proxy_file and proxy_type:
        proxy = await read_proxy(proxy_file, proxy_type)
    else:
        print("Файл с прокси не найден")
        proxy = None
  
    try:
        for i, username in enumerate(usernames):
            try:
                if user_client is None or not user_client.is_connected():
                    user_client = await auto_login(accounts, proxy, account_index, proxy_index, user_session_folder)     
                    await user_client.connect() 
                await user_client.send_message(username, message, parse_mode="html")
                print(f"Сообщение отправлено пользователю с никнеймом {username}")
                await asyncio.sleep(interval)  
            
                if (i + 1) % message_count == 0:
                    await user_client.disconnect()
                    account_index = (account_index + 1) % len(accounts) 
                    if proxy:
                        proxy_index = (proxy_index + 1) % len(proxy)  
                    user_client = await auto_login(accounts, proxy, account_index, proxy_index, user_session_folder)
                    await user_client.connect()
                    print(f"Перелогинились после отправки {message_count} сообщений")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {username}: {e}")
    finally:
        if user_client:
            await user_client.disconnect()
        if isinstance(usernames_file, str):
            os.remove(usernames_file)
        else:
            print(f"Неверный тип usernames_file: {type(usernames_file)}")
'''
async def send_messages_auto_id(accounts_file: str, proxy_file: str, message_count: int, interval: int, message: str, group_link: str) -> None:
    file_path = await parse_group_members(group_link)
    print(f"Тип file_path после parse_group_members: {type(file_path)}")  

    user_ids = await read_user_ids(file_path)
    print(f"Тип user_ids после read_user_ids: {type(user_ids)}")  
    
    if not user_ids:
        print("Список пользователей пуст или файл не существует.")
        return
    
    user_client = None  
    
    try:
        for i, user_id in enumerate(user_ids):
            try:
                if user_client is None or not user_client.is_connected():
                    user_client = await auto_login(accounts_file, proxy_file)
                
                await user_client.send_message(int(user_id), message)
                print(f"Сообщение отправлено пользователю с ID {user_id}")
                await asyncio.sleep(interval)  
        
                if (i + 1) % message_count == 0:
                    await user_client.disconnect()
                    user_client = await auto_login(accounts_file, proxy_file)
                    print(f"Перелогинились после отправки {message_count} сообщений")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
    finally:
        if user_client:
            await user_client.disconnect()
        print(f"Тип file_path в finally: {type(file_path)}")  
        if isinstance(file_path, str):
            os.remove(file_path)
        else:
            print(f"Неверный тип file_path: {type(file_path)}")
'''

async def monitor_channel(event, accounts_file: str, proxy_file: str, proxy_type: str, message_count: int, interval: int, message: str, channel_link: str):
    user_session_folder = await create_session_folder(event)

    if accounts_file:
        accounts = await read_account(accounts_file)
    else:
        print("Файл с аккаунтами не найден")
        await event.respond("Файл с аккаунтами не найден, мониторинг остановлен")
        return
    
    if proxy_file and proxy_type:
        proxy = await read_proxy(proxy_file, proxy_type)
    else:
        print("Файл с прокси не найден")
        proxy = None
        
    account_index = 0
    proxy_index = 0
    messages_sent = 0

    try:
        await default_user_client.connect()
        discussion_group = await get_channel_group(default_user_client, channel_link)
        user_client = await auto_login(accounts, proxy, account_index, proxy_index, user_session_folder)
        await user_client.connect()
        discussion_group = await get_channel_group(user_client, channel_link)

        if discussion_group:
            await default_user_client(JoinChannelRequest(discussion_group))
            await user_client(JoinChannelRequest(discussion_group))
        else:
            print("У этого канала нет обсуждения")
            await event.respond("У этого канала нет обсуждения, мониторинг остановлен") 
            return

        @default_user_client.on(events.NewMessage(chats=channel_link))
        async def new_post_listener(event):
            nonlocal messages_sent, account_index, proxy_index, user_client
            await asyncio.sleep(interval)
            await send_comment(user_client, message, event.chat)
            messages_sent += 1

            if messages_sent >= message_count:
                await user_client.disconnect()
                account_index = (account_index + 1) % len(accounts)
                if proxy:
                    proxy_index = (proxy_index + 1) % len(proxy)  
                user_client = await auto_login(accounts, proxy, account_index, proxy_index, user_session_folder)
                await user_client.connect()
                discussion_group = await get_channel_group(user_client, channel_link)
                await user_client(JoinChannelRequest(discussion_group))
                messages_sent = 0
                print(f"Перелогинились после отправки {message_count} сообщений")

        print("Начинаю мониторинг канала...")
        
        while True:
            await asyncio.sleep(1)
            if user_data["stop_monitoring"]:
                break
        
        default_user_client.remove_event_handler(new_post_listener)
        
    except Exception as e:
        print(f"Ошибка при отправке сообщений или мониторинге: {e}")
        event.respond(f"Ошибка при отправке сообщений или мониторинге: {e}")
        
    await user_client.disconnect()
    await default_user_client.disconnect()
    print("Остановлен мониторинг канала")

async def create_session_folder(event):
    user_id = event.sender_id
    user_session_folder = os.path.join("bot", "session", f"user_{user_id}")  
    return user_session_folder

async def get_channel_group(client, channel_link):
    await client(JoinChannelRequest(channel_link))
    full = await client(functions.channels.GetFullChannelRequest(channel_link))
    full_channel = full.full_chat
    discussion_group = full_channel.linked_chat_id

    return discussion_group

async def send_comment(user_client, message, chat_link):
    try:
        chat = await user_client.get_entity(chat_link)
        if not chat:
            print("Канал не найден")
            return

        async for post in user_client.iter_messages(chat, limit=1):
            await user_client.send_message(entity=chat, message=message, parse_mode='html', comment_to=post.id)
            print("Сообщение отправлено к последнему посту")
            break
        else:
            print("История сообщений пуста")
    except Exception as e:
        print(f"Ошибка: {e}")

async def send_text_message(user_client, chat_link, message):
    try:
        chat = await user_client.get_entity(chat_link)
        if not chat:
            print("Канал не найден")
            return

        await user_client.send_message(chat_link, message, parse_mode='html')
        print("Сообщение отправлено")
    except Exception as e:
        print(f"Ошибка: {e}")

async def send_photo(user_client, chat_link, photo_path, caption):
    try:
        channel = await user_client.get_entity(chat_link)
        if not channel:
            print("Канал не найден")
            return

        await user_client.send_file(channel, photo_path, caption=caption, parse_mode='html')
        print("Фото отправлено")
    except Exception as e:
        print(f"Ошибка: {e}")

async def send_video(user_client, chat_link, video_path, caption):
    try:
        chat = await user_client.get_entity(chat_link)
        if not chat:
            print("Канал не найден")
            return

        await user_client.send_file(user_client, chat_link, video_path, caption=caption, parse_mode='html')
        print("Видео отправлено")
    except Exception as e:
        print(f"Ошибка: {e}")

async def save_file(event, file_name: str):
    if event.message.file:
        file_path = os.path.join("bot", "downloads", file_name)
        print(f"Тип file_path в save_file перед созданием директории: {type(file_path)}")  

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
     
        await event.message.download_media(file_path)
        print(f"Тип file_path в save_file после скачивания файла: {type(file_path)}") 
        return file_path
    else:
        return None
    
async def read_account(file_path: str):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        accounts = []
        with open(file_path, 'r') as file:
            lines = [line.strip() for line in file if line.strip()]  
            for i in range(0, len(lines), 3):
                api_id = lines[i]
                api_hash = lines[i+1]
                phone_number = lines[i+2]
                accounts.append((api_id, api_hash, phone_number))
        return accounts
    else:
        return None

async def read_proxy(file_path: str, proxy_type: str):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        proxy = []
        with open(file_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                ipv6_match = ipv6_pattern.match(line)
                ipv4_match = ipv4_pattern.match(line)

                if ipv6_match:
                    proxy_addr, proxy_port, proxy_username, proxy_password = ipv6_match.groups()
                elif ipv4_match:
                    proxy_addr, proxy_port, proxy_username, proxy_password = ipv4_match.groups()
                else:
                    print(f"Неверный формат прокси: {line}")
                    continue
                    
                proxy.append((proxy_addr, int(proxy_port), proxy_username, proxy_password, proxy_type))
        return proxy
    else:
        return None

async def read_usernames(file_path: str) -> list:
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r") as file:
            usernames = file.readlines()
        return [username.strip() for username in usernames if username.strip()] 
    else:
        return None
'''
async def read_user_ids(file_path: str) -> list:
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r") as file:
            user_ids = file.readlines()
        return [user_id.strip() for user_id in user_ids]
    else:
        return None
'''


