# -*- coding: utf-8 -*-
"""
Usage :
 > python3 bsgs17.py -pfile /media/admin1/RMM/Ramy/1.txt -n 500000000000000

@author: RAMY
"""
import argparse
import sys
from eth_keys import keys  # Import the necessary class from eth-keys

parser = argparse.ArgumentParser(description='This tool performs a sequential search for Ethereum private keys in a given range',
                                 epilog='Enjoy the program! :)')
parser.version = '02012022'
parser.add_argument("-n", help="Total sequential search in 1 loop. Default=10000000000000000", action='store')
parser.add_argument("-pfile", "--pfile", help="File path containing public keys", action="store")

args = parser.parse_args()

seq = int(args.n) if args.n else 10000000000000000

# Read target addresses from file
def read_target_addresses(file_path):
    try:
        with open(file_path, 'r') as file:
            addresses = [line.strip() for line in file if line.startswith('0x')]
        return addresses
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        sys.exit(1)

# Main search function modified for sequential search
def seq_search_keys_for_ethereum(start, end, target_addresses):
    found_keys = []
    last_three_keys = []  # List to store the last 3 private keys generated
    try:
        for key_int in range(start, end):
            private_key = hex(key_int)[2:].zfill(64)  # Convert integer to 64-character hex string
            private_key_bytes = bytes.fromhex(private_key)
            private_key_obj = keys.PrivateKey(private_key_bytes)
            public_key_obj = private_key_obj.public_key
            address = public_key_obj.to_checksum_address()

            # Check if the address matches any target addresses
            if address in target_addresses:
                found_keys.append((address, private_key))
                print(f"Found matching private key for address {address}: {private_key}")
                # Add the private key to the last_three_keys list
                last_three_keys.append(private_key)
                # Keep only the last 3 private keys in the list
                last_three_keys = last_three_keys[-3:]

    except Exception as e:
        print(f"Error during sequential search: {e}")
        sys.exit(1)

    return found_keys, last_three_keys

# Main script starting below
start_range = int("8be35c148f9b2e9f30e490ad307273424fca03cd04635640c0b3adefc88d5c00", 16)
end_range = int("8ca35c148f9b2e9f30e490ad307273424fca03cd04635640c0b3adefc88d5c00", 16)

# Read target addresses from file
target_addresses = read_target_addresses(args.pfile)

el = start_range  # Set initial value for el to start_range

try:
    while el <= end_range:
        end = min(el + seq, end_range + 1)  # Ensure end doesn't go beyond end_range
        print("Searching Range: [{}, {}]".format(hex(el), hex(end - 1)))  # Comment to indicate the range being searched

        # Call the function to search for Ethereum private keys in the specified range
        found_keys, last_three_keys = seq_search_keys_for_ethereum(el, end, target_addresses)

        # Logic to handle found keys
        if found_keys:
            with open("founded.txt", "a") as f:
                for address, private_key in found_keys:
                    f.write(f"Address: {address}, Private Key: {private_key}\n")
                    print(f"Exported private key to founded.txt: Address {address}, Private Key {private_key}")

        el += seq  # Move el to the next range

    print("Search complete.")
except KeyboardInterrupt:
    print("Search interrupted by user.")
    # Export the last 3 private keys to founded.txt
    if last_three_keys:
        with open("founded.txt", "a") as f:
            f.write("Last 3 Private Keys:\n")
            for private_key in last_three_keys:
                f.write(f"Private Key: {private_key}\n")
    sys.exit(0)
except Exception as e:
    print(f"Error during search process: {e}")
    # Export the last 3 private keys to founded.txt
    if last_three_keys:
        with open("founded.txt", "a") as f:
            f.write("Last 3 Private Keys:\n")
            for private_key in last_three_keys:
                f.write(f"Private Key: {private_key}\n")
    sys.exit(1)

