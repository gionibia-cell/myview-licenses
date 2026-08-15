import json
import os
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.environ.get("LICENSE_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    print("❌ Variabile LICENSE_ENCRYPTION_KEY non impostata.")
    exit(1)

cipher = Fernet(ENCRYPTION_KEY.encode())

try:
    with open("license.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print("❌ File license.json non trovato.")
    exit(1)

json_str = json.dumps(data, indent=2)
encrypted = cipher.encrypt(json_str.encode('utf-8'))

with open("license.enc", "wb") as f:
    f.write(encrypted)

print("✅ File license.enc creato con successo.")