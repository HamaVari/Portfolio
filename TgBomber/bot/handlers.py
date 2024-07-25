import os
from telethon import Button
from config import bot_client, default_user_client, user_data
from bot.utils import save_file, parse_group_usernames, handle_account_authorization, send_messages_auto, monitor_channel
from validation import validate_file_extension, validate_message_extension, validate_accounts_file_content, validate_proxy_file_content

async def start(event) -> None:
    user_id = event.sender_id
    welcome_message = f"Привет! Я бот для парсинга и рассылки\n\nВаш user id: {user_id}"
    buttons = [
        [Button.inline("Спарсить участников группы", b"parse_group")],
        [Button.inline("Спарсить участников канала(Скоро)", b"parse_channel")],
        [Button.inline("Рассылка участникам группы", b"start_group")],
        [Button.inline("Рассылка комментаторам канала(Скоро)", b"start_comment")],
        [Button.inline("Рассылка + мониторинг в посты канала или группы", b"start_post")],
    ]
    await event.respond(welcome_message, buttons=buttons)

async def callback(event):
    data = event.data.decode("utf-8")
    if data == "parse_group":
        await event.edit("Пришлите пожалуйста ссылку на группу или чат: ")
        user_data[event.sender_id] = {"action": "parse_group"}
    elif data == "parse_channel":
        await event.edit("Пока что данная функция недоступна")
        user_data[event.sender_id] = {"action": "parse_channel"}
    elif data == "start_group":
        await event.edit("Пришлите txt файл с аккаунтами Telegram (api_id, api_hash, телефон) в формате по очереди с новой строки:\n\n48291736\nb7d5f9a2c3e4d6b8f7g9h1j2k3l4m5n6\n+380965321289")
        user_data["initial_action"] = "start_group"
        user_data[event.sender_id] = {"action": "receive_accounts"}
    elif data == "start_comment":   
        await event.edit("Пока что данная функция недоступна")
        user_data[event.sender_id] = {"action": "start_channel"}
    elif data == "start_post":
        await event.edit("Пришлите txt файл с аккаунтами Telegram (api_id, api_hash, телефон) в формате по очереди с новой строки:\n\n48291736\nb7d5f9a2c3e4d6b8f7g9h1j2k3l4m5n6\n+380965321289")
        user_data["initial_action"] = "start_post"
        user_data["stop_monitoring"] = False       
        user_data[event.sender_id] = {"action": "receive_accounts"}
    elif data == "single_message":
        await event.edit("Введите сообщение для рассылки: \n\n!Если у вас присуствует форматирование текста, то оберните форматируемый текст в нужные теги html!")
        user_data[event.sender_id] = {"action": "single_message"}
    elif data == "multiple_messages":
        await event.edit('Пока что данная функция недоступна')
        user_data[event.sender_id] = {"action": None}
        '''
        await event.edit('Введите сообщения для рассылки по очереди, отправляйте каждое сообщение отдельно. Введите "end" для завершения ввода: ')
        user_data[event.sender_id] = {"action": "multiple_messages", "messages": []}
        '''
    elif data == "socks5":
        await event.edit("Выбран SOCKS5 proxy.\n\nПришлите .txt файл с адресами прокси в формате по очереди с новой строки:\n\n192.168.1.1:8080:username:password\n203.0.113.5:3128:username:password\n[2001:db8::ff00:42:8329]:1081:username:password\n или \n192.168.1.1:8080\n203.0.113.5:3128\n[2001:db8::ff00:42:8329]:1081\n")
        user_data["proxy_type"] = "socks5"
        user_data[event.sender_id] = {"action": "receive_proxy"}
    elif data == "http":
        await event.edit('Пока что данная функция недоступна')
        user_data[event.sender_id] = {"action": None}
        '''
        await event.edit("Выбран HTTP proxy.\n\nПришлите .txt файл с адресами прокси в формате по очереди с новой строки:\n\n192.168.1.1:8080:username:password\n203.0.113.5:3128:username:password\n[2001:db8::ff00:42:8329]:1081:username:password\n или \n192.168.1.1:8080\n203.0.113.5:3128\n[2001:db8::ff00:42:8329]:1081\n")
        user_data["proxy_type"] = "http"
        user_data[event.sender_id] = {"action": "receive_proxy"}
        '''
    elif data == "no_proxy":
        await event.edit("Прокси не выбран.\n\nДля авторизации в аккаунтах, которые вы передали через файл .txt, отправляйте по очереди код для входа в Telegram.")
        user_data["proxy_type"] = None
        user_data["proxy"] = None
        accounts_file = user_data.get('accounts')  
        await handle_account_authorization(event, accounts_file, None, None)   
        await event.respond("Все аккаунты авторизованы, введите интервал через сколько сообщений должна быть переавторизация аккаунта: ")
        user_data[event.sender_id]["action"] = "set_message_count"        

async def message(event):
    action = user_data.get(event.sender_id, {}).get("action")
    if action == "parse_group":
        if not validate_message_extension(event):
            if event.message.message:
                group_link = event.message.message
                await event.respond(f"Получена ссылка на группу: {group_link}. Начинаю парсинг участников...")
                file_path = await parse_group_usernames(event, group_link)
                await bot_client.send_file(event.sender_id,file_path, caption="Парсинг завершен. Вот список участников группы\n\nВведите новую ссылку на группу или введите '/start' чтобы вернуться в главное меню: ")
                os.remove(file_path)
            else: 
                await event.respond("Неправильный формат сообщения или неправильная команда, введите ссылку на группу или введите '/start:' ")

    elif action == "receive_accounts":
        if not validate_message_extension(event):
            if validate_file_extension(event):
                accounts_file = await save_file(event, "accounts.txt")
                if await validate_accounts_file_content(accounts_file):
                    user_data["accounts"] = accounts_file
                    buttons = [
                        [Button.inline("SOCKS5", b"socks5"), Button.inline("HTTP", b"http")],
                        [Button.inline("Без прокси", b"no_proxy")]
                    ]
                    await event.respond("Файл с аккаунтами получен. Выберите тип прокси:", buttons=buttons)
                    user_data[event.sender_id]["action"] = None
                else:
                    if os.path.exists(accounts_file):
                        os.remove(accounts_file)
                    await event.respond("Ошибка при обработке файла с аккаунтами. Неверный формат аккаунтов внутри файла, скиньте файл .txt с правильным форматом аккаунтов внутри файла: ")
            else:
                await event.respond("Неверный формат файла или команда. Пожалуйста, загрузите файл с расширением .txt: ")

    elif action == "receive_proxy":
        if not validate_message_extension(event):
            if validate_file_extension(event):
                proxy_file = await save_file(event, "proxy.txt")
                if await validate_proxy_file_content(proxy_file):
                    user_data["proxy"] = proxy_file 
                    proxy_type = user_data.get('proxy_type')
                    accounts_file = user_data.get('accounts')    
                    await event.respond("Файл с прокси получен. Для авторизации в аккаунтах, которые вы передали через файл .txt, отправляйте по очереди код для входа в Telegram")
                    await handle_account_authorization(event, accounts_file, proxy_file, proxy_type)
                    await event.respond("Все аккаунты авторизованы, введите интервал через сколько сообщений должна быть переавторизация аккаунта: ")
                    user_data[event.sender_id]["action"] = "set_message_count"
                else:
                    if os.path.exists(proxy_file):
                        os.remove(proxy_file)
                    await event.respond("Ошибка при обработке файла с прокси. Неверный формат прокси внутри файла, скиньте файл .txt с правильным форматом прокси внутри файла: ")
            else:
                await event.respond("Неверный формат файла или команда. Пожалуйста, загрузите файл с расширением .txt: ")
        
    elif action == "set_message_count":
        if not validate_message_extension(event):
            message_count = event.message.message.strip()
            if message_count.lower() == "random":
                await event.respond("Пока что данная функция недоступна")
                return
                '''
                user_data["message_count"] = "random"
                '''
            else:
                try:
                    user_data["message_count"] = int(message_count)
                except ValueError:
                    await event.respond("Ошибка: сообщение не является допустимым числом. Пожалуйста, введите число или 'random': ")
                    return
                await event.respond("Введите интервал между отправкой сообщений в секундах или напишите 'random': ")
                user_data[event.sender_id]['action'] = "set_message_interval"

    elif action == "set_message_interval":
        if not validate_message_extension(event):
            interval = event.message.message.strip()
            if interval.lower() == "random":
                await event.respond("Пока что данная функция недоступна")
                return
                '''
                user_data["interval"] = "random"
                '''
            else:
                try:
                    user_data["interval"] = int(interval)
                except ValueError:
                    await event.respond("Ошибка: сообщение не является допустимым числом. Пожалуйста, введите число или 'random': ")
                    return
                buttons = [
                    [Button.inline("Рассылка одним сообщением", b"single_message")],
                    [Button.inline("Рассылка несколькими сообщениями", b"multiple_messages")],
                ]
                await event.respond("Выберите тип рассылки", buttons=buttons)
                user_data[event.sender_id]["action"] = None

    elif action == "single_message":
        if not validate_message_extension(event):
            initial_action = user_data.get('initial_action')
            message = event.message.message
            user_data["message"] = message
            if initial_action == "start_group":
                await event.respond("Сообщение сохранено. Пожалуйста, введите ссылку на группу: ")
            elif initial_action == "start_post":
                await event.respond("Сообщение сохранено. Пожалуйста, введите ссылку на канал: ")
            user_data[event.sender_id]["action"] = "single_message_send"
        
    elif action == "multiple_messages":
        if not validate_message_extension(event):
            message = event.message.message
            if message.lower() == "end":
                await event.respond("Пожалуйста, введите ссылку на группу: ")
                user_data[event.sender_id]["action"] = "multiple_messages_send"
            else:
                user_data["messages"].append(message)
                await event.respond("Сообщение сохранено.")
            
    elif action == "single_message_send":
        if not validate_message_extension(event):
            user_data["stop_monitoring"] = False  
            group_link = event.message.message     
            accounts_file = user_data.get('accounts')
            message_count = user_data.get('message_count')
            interval = user_data.get('interval')
            message = user_data.get('message')
            initial_action = user_data.get('initial_action')
            proxy_file = user_data.get('proxy')
            proxy_type = user_data.get('proxy_type')

            if (group_link is not None and accounts_file is not None and message_count is not None and interval is not None and message is not None and (proxy_type is None or proxy_file is not None)):            
                if initial_action == "start_group":
                    await event.respond(f"Начинаю рассылку по группе: {group_link}...")
                    await send_messages_auto(event, accounts_file, proxy_file, proxy_type, message_count, interval, message, group_link)
                    await event.respond(f"Рассылка закончена\n\nВведите новую ссылку на группу или введите '/start' чтобы вернуться в главное меню: ")
                elif initial_action == "start_post":
                    await event.respond(f"Начинаю мониторинг и рассылку в последний пост канала {group_link}...\n\nВведите 'stop' для окончания мониторинга: ")
                    user_data[event.sender_id]["action"] = "monitor_channel"
                    await monitor_channel(event, accounts_file, proxy_file, proxy_type, message_count, interval, message, group_link)
            else:  
                missing_data = []
    
                if group_link is None:
                    missing_data.append("group_ link")
                if accounts_file is None:
                    missing_data.append("accounts")
                if message_count is None:
                    missing_data.append("message_count")
                if interval is None:
                    missing_data.append("interval")
                if message is None:
                    missing_data.append("message")
                if proxy_type is not None and proxy_file is None:
                    missing_data.append("proxy")

                await event.respond(f"Ошибка: данные {', '.join(missing_data)} не найдены.")
                user_data["action"] = None

    elif action == "multiple_messages_send":
        group_link = event.message.message
        if "accounts" in user_data[event.sender_id] and "proxy" in user_data[event.sender_id]:
            await event.respond(f"Начинаю рассылку по группе: {group_link}...")
            await send_messages_auto(user_data["accounts"], user_data["proxy"], user_data["message_count"], user_data["interval"], user_data["messages"], group_link)
        else:
            await event.respond("Ошибка: данные аккаунтов или прокси не найдены.")
            user_data["action"] = None

    elif action == "monitor_channel":
        if validate_message_extension(event):
            user_data["stop_monitoring"] = True   
            await event.respond("Остановлен мониторинг канала")
            user_data[event.sender_id]["action"] = None
        elif event.message.message.lower() == "stop":
            user_data["stop_monitoring"] = True    
            await event.respond("Остановлен мониторинг канала\n\nВведите новую ссылку на канал или '/start' чтобы вернуться в главное меню: ") 
            user_data[event.sender_id]["action"] = "single_message_send"
        else:
            await event.respond("Неизвестная команда. Введите 'stop' чтобы остановить мониторинг канала или '/start' чтобы остановить мониторинг канала и вернуться в главное меню: ") 