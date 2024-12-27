import os
import hashlib
import base58
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ecdsa import SigningKey, SECP256k1


# Генерация приватного ключа
def generate_private_key():
    return os.urandom(32).hex()


# Генерация публичного ключа из приватного
def private_key_to_public_key(private_key):
    key = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
    public_key = key.verifying_key.to_string()
    return b'\x04' + public_key  # Добавляем префикс для полного публичного ключа


# Генерация Bitcoin-адреса из публичного ключа (формат P2PKH)
def public_key_to_btc_address(public_key):
    # SHA-256 хэш от публичного ключа
    sha256_hash = hashlib.sha256(public_key).digest()

    # RIPEMD-160 хэш
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()

    # Добавляем версионный байт (0x00 для Bitcoin)
    versioned_payload = b'\x00' + ripemd160_hash

    # Добавляем контрольную сумму (4 байта от двойного SHA-256)
    checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]

    # Кодируем в Base58
    return base58.b58encode(versioned_payload + checksum).decode()


# Проверка адреса в сете
def check_address(address, address_set):
    return address in address_set


# Асинхронная обработка чанков
async def process_chunk(chunk_size, address_set, matches_file):
    for _ in range(chunk_size):
        # Генерация приватного ключа, публичного ключа и адреса
        private_key = generate_private_key()
        public_key = private_key_to_public_key(private_key)
        btc_address = public_key_to_btc_address(public_key)

        # Проверка на совпадение
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