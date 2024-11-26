import os
import time
from bip_utils import (
    Bip44,
    Bip49,
    Bip84,
    Bip44Coins,
    Bip39SeedGenerator,
    Bip39MnemonicGenerator,
    Bip44Changes
)
from pybloom_live import BloomFilter
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading

# Конфигурация
RICH_FILE = "puzzle.txt"
FOUND_FILE = "found.txt"
MNEMONIC_SIZE = 12  # Количество слов в мнемонике
ADDRESS_COUNT = 5000  # Количество адресов на мнемоник
BATCH_SIZE = 100  # Размер батча для проверки

# Глобальные переменные
term = threading.Lock()
log_queue = Queue()
z = 0  # Счётчик сгенерированных мнемоников
w = 0  # Счётчик совпадений


def get_time():
    """Получить текущее время."""
    return time.strftime('%Y-%m-%d %H:%M:%S')


def generate_addresses(mnemonic):
    """Генерация адресов всех типов на основе мнемоника."""
    seed = Bip39SeedGenerator(mnemonic).Generate()

    # Кошельки для разных типов адресов
    bip44_wallet = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)  # P2PKH
    bip49_wallet = Bip49.FromSeed(seed, Bip44Coins.BITCOIN)  # P2SH
    bip84_wallet = Bip84.FromSeed(seed, Bip44Coins.BITCOIN)  # Bech32 (P2WPKH)

    addresses = []

    # Генерация адресов для каждого типа
    for i in range(ADDRESS_COUNT):
        p2pkh = (
            bip44_wallet
            .Purpose()
            .Coin()
            .Account(0)
            .Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(i)
            .PublicKey()
            .ToAddress()
        )
        p2sh = (
            bip49_wallet
            .Purpose()
            .Coin()
            .Account(0)
            .Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(i)
            .PublicKey()
            .ToAddress()
        )
        bech32 = (
            bip84_wallet
            .Purpose()
            .Coin()
            .Account(0)
            .Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(i)
            .PublicKey()
            .ToAddress()
        )

        addresses.extend([p2pkh, p2sh, bech32])

    return addresses


def data_export():
    """Генерация мнемоника и всех адресов."""
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(MNEMONIC_SIZE)
    addresses = generate_addresses(mnemonic)
    return addresses, mnemonic


def handle_data(data, richAddresses):
    """Обработка данных и проверка совпадений."""
    global z, w
    addresses, mnemonic = data
    z += 1

    found = [addr for addr in addresses if addr in richAddresses]

    if found:
        w += len(found)
        log_queue.put(f"Found addresses: {', '.join(found)}\nMnemonic: {mnemonic}\n")

    # Обновление прогресса в терминале
    if z % 500 == 0:  # Обновление каждые 500 итераций
        with term:
            print(f"[{get_time()}] Generated: {z} | Matches Found: {w}")


def read_addresses_from_file(file_path):
    """Чтение богатых адресов в Bloom Filter."""
    bloom = BloomFilter(capacity=5000000, error_rate=0.0001)
    with open(file_path, "r") as file:
        for line in file:
            bloom.add(line.strip())
    return bloom


def log_worker():
    """Асинхронное логирование результатов."""
    buffer = []
    buffer_size = 100
    with open(FOUND_FILE, "a") as file:
        while True:
            log_string = log_queue.get()
            if log_string == "STOP":
                break
            buffer.append(log_string)
            if len(buffer) >= buffer_size:
                file.writelines(buffer)
                buffer.clear()
            log_queue.task_done()
        if buffer:
            file.writelines(buffer)


def worker_thread():
    """Основная функция для генерации и проверки."""
    core_total = os.cpu_count() or 4
    print(f"Using {core_total} threads for processing.")

    richAddresses = read_addresses_from_file(RICH_FILE)
    print(f"Loaded ~{len(richAddresses)} addresses into Bloom Filter.")

    with ThreadPoolExecutor(max_workers=core_total) as executor:
        futures = [executor.submit(data_export) for _ in range(core_total * 100)]
        for future in as_completed(futures):
            try:
                data = future.result()
                handle_data(data, richAddresses)
            except Exception as exc:
                print(f"Error: {exc}")


if __name__ == "__main__":
    try:
        # Логирование
        log_thread = threading.Thread(target=log_worker, daemon=True)
        log_thread.start()

        # Основной процесс
        worker_thread()

    except KeyboardInterrupt:
        print("Process interrupted by user.")
        log_queue.put("STOP")
        log_queue.join()