import secrets
from bit import Key
import asyncio
from concurrent.futures import ThreadPoolExecutor


# Генерация приватного ключа и соответствующего Bitcoin-адреса
def generate_btc_address():
    private_key = secrets.token_hex(32)  # Генерация 256-битного приватного ключа
    key = Key.from_hex(private_key)  # Создание ключа через библиотеку bit
    return private_key, key.address


# Проверка адреса в сете
def check_address(address, address_set):
    return address in address_set


# Асинхронная обработка чанков
async def process_chunk(chunk_size, address_set, matches_file):
    for _ in range(chunk_size):
        # Генерация приватного ключа и адреса
        private_key, btc_address = generate_btc_address()

        # Проверка адреса на совпадение
        if check_address(btc_address, address_set):
            print(f"[MATCH FOUND] Address: {btc_address} | Private Key: {private_key}")
            with open(matches_file, "a") as f:
                f.write(f"Address: {btc_address} | Private Key: {private_key}\n")


# Асинхронная основная функция
async def main():
    # Загрузка адресов из файла
    addresses_file = "puzzle.txt"
    matches_file = "btc_matches.txt"

    print("[INFO] Loading BTC addresses...")
    with open(addresses_file, "r") as f:
        address_set = set(line.strip() for line in f.readlines())
    print(f"[INFO] Loaded {len(address_set)} Bitcoin addresses.")

    # Размер чанка
    chunk_size = 100

    # Многопоточность для повышения производительности
    with ThreadPoolExecutor() as executor:
        tasks = []
        for _ in range(10):  # Одновременная обработка 10 чанков
            tasks.append(asyncio.get_event_loop().run_in_executor(
                executor, process_chunk, chunk_size, address_set, matches_file
            ))

        # Ожидание завершения всех задач
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())