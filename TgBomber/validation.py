import re
import aiofiles

def validate_file_extension(event) -> bool:
    return event.message.file and event.message.file.name.endswith('.txt')

def validate_message_extension(event) -> bool:
    return event.message.message and event.message.message.lower() == "/start"

digit_pattern = re.compile(r"^\d+$")
hex_pattern = re.compile(r"^[a-f0-9]{32}$")
phone_pattern = re.compile(r"^\+\d+$")
ipv4_pattern = re.compile(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)(?::([^:]*):([^:]*))?$")
ipv6_pattern = re.compile(r"^\[([0-9a-fA-F:]+)\]:(\d+)(?::([^:]*):([^:]*))?$")

async def validate_accounts_file_content(file_path: str) -> bool:
    async with aiofiles.open(file_path, "r") as f:
        content = await f.read()
        lines = [line.replace(" ", "") for line in content.split("\n") if line.strip()]

        if not lines: 
            print("Файл пустой")
            return False
        
        print(f"Количество строк (без пустых): {len(lines)}")
        
        if len(lines) % 3 != 0:
            print("Количество строк не кратно 3")
            return False
        
        for i in range(0, len(lines), 3):
            line1 = lines[i]
            line2 = lines[i + 1]
            line3 = lines[i + 2]
            if not digit_pattern.match(line1):
                print(f"Ошибка в строке {i+1}: {line1}")
                return False
            if not hex_pattern.match(line2):
                print(f"Ошибка в строке {i+2}: {line2}")
                return False
            if not phone_pattern.match(line3):
                print(f"Ошибка в строке {i+3}: {line3}")
                return False
    return True

async def validate_proxy_file_content(file_path: str) -> bool:
    async with aiofiles.open(file_path, "r") as f:
        content = await f.read()
        lines = [line.replace(" ", "") for line in content.split("\n") if line.strip()]

        if not lines: 
            print("Файл пустой")
            return False
        
        print(f"Количество строк (без пустых): {len(lines)}")

        for line in lines:
            if not (ipv4_pattern.match(line) or ipv6_pattern.match(line)):
                print(f"Ошибка в строке: {line}")
                return False
    return True
