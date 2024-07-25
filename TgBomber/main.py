import asyncio
from telethon import events
from config import bot_client, default_user_client, bot_token, allowed_ids, phone_number
from bot.handlers import start, callback, message


@bot_client.on(events.NewMessage(pattern="/start"))
async def handle_start(event):
    user_id = event.sender_id
    if user_id in allowed_ids:
        await start(event)
    else:
        await event.respond("У вас нет доступа к этому боту")  

@bot_client.on(events.CallbackQuery)
async def handle_callback(event):
    await callback(event)
@bot_client.on(events.NewMessage)
async def handle_message(event):
    await message(event)

async def main():
    await bot_client.start(bot_token=bot_token)
    '''
    await default_user_client.connect()
    if not await default_user_client.is_user_authorized():
        await default_user_client.send_code_request(phone_number)
        await default_user_client.sign_in(phone_number, input('Введите код из СМС: '))
    '''
    print("Бот запущен и готов к работе.")
    await bot_client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())