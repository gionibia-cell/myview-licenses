import json
import hmac
import hashlib
import sys
import os
from datetime import datetime
from cryptography.fernet import Fernet   # <-- AGGIUNTO PER LA CIFRATURA

LICENSE_FILE = "license.enc"             # <-- MODIFICATO: ora usa file cifrato
HMAC_KEY = b"MyHMACSecretKey2025!"

# LEGGI LA CHIAVE DI CIFRATURA DALLA VARIABILE D'AMBIENTE
ENCRYPTION_KEY = os.environ.get("LICENSE_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    print("❌ ERRORE: variabile d'ambiente LICENSE_ENCRYPTION_KEY non impostata.")
    print("   Imposta la variabile e riavvia lo script.")
    sys.exit(1)
cipher = Fernet(ENCRYPTION_KEY.encode())

def clear_screen():
    """Pulisce lo schermo (Windows: cls, Unix: clear)"""
    os.system('cls' if os.name == 'nt' else 'clear')

def load_licenses():
    """Carica il file cifrato e lo decifra"""
    if not os.path.exists(LICENSE_FILE):
        return {"devices": {}}
    with open(LICENSE_FILE, "rb") as f:   # <-- lettura binaria
        encrypted_data = f.read()
    try:
        decrypted_data = cipher.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode('utf-8'))
    except Exception as e:
        print(f"❌ Errore nella decifratura: {e}")
        print("   Controlla che la chiave sia corretta.")
        return {"devices": {}}

def save_licenses(data):
    """Cifra e salva il file"""
    json_str = json.dumps(data, indent=2)
    encrypted_data = cipher.encrypt(json_str.encode('utf-8'))
    with open(LICENSE_FILE, "wb") as f:   # <-- scrittura binaria
        f.write(encrypted_data)

def list_licenses(data):
    devices = data.get("devices", {})
    if not devices:
        print("📭 Nessuna licenza presente.")
        return
    print("\n" + "=" * 70)
    print(f"{'Device ID':<20} {'Alias':<25} {'Scadenza':<12} {'Stato':<8}")
    print("=" * 70)
    for device_id, info in devices.items():
        alias = info.get("alias", "N/D")[:25]
        expiry = info.get("expiry", "N/D")
        active = "✅" if info.get("active", False) else "❌"
        print(f"{device_id:<20} {alias:<25} {expiry:<12} {active:<8}")
    print("=" * 70)

def add_license(data):
    print("\n" + "=" * 50)
    print("➕ AGGIUNTA LICENZA")
    print("=" * 50)
    device_id = input("🆔 Device ID (16 caratteri esadecimali): ").strip()
    if len(device_id) != 16 or not all(c in "0123456789abcdef" for c in device_id.lower()):
        print("❌ Device ID non valido. Deve essere 16 caratteri esadecimali.")
        input("\nPremi INVIO per continuare...")
        return
    if device_id in data["devices"]:
        print(f"⚠️ Il dispositivo {device_id} esiste già. Usa la modifica.")
        input("\nPremi INVIO per continuare...")
        return
    alias = input("📛 Alias (nome descrittivo): ").strip()
    if not alias:
        alias = device_id[:8]
    expiry = input("📅 Data scadenza (YYYY-MM-DD): ").strip()
    try:
        datetime.strptime(expiry, "%Y-%m-%d")
    except ValueError:
        print("❌ Data non valida. Usa il formato YYYY-MM-DD.")
        input("\nPremi INVIO per continuare...")
        return
    data["devices"][device_id] = {
        "alias": alias,
        "expiry": expiry,
        "active": True,
        "created": datetime.now().strftime("%Y-%m-%d")
    }
    save_licenses(data)
    print(f"✅ Licenza aggiunta per {alias} ({device_id})")
    input("\nPremi INVIO per continuare...")

def edit_license(data):
    print("\n" + "=" * 50)
    print("✏️ MODIFICA LICENZA")
    print("=" * 50)
    device_id = input("🆔 Device ID da modificare: ").strip()
    if device_id not in data["devices"]:
        print("❌ Device ID non trovato.")
        input("\nPremi INVIO per continuare...")
        return
    info = data["devices"][device_id]
    print(f"\n📝 Modifica licenza per {info.get('alias', device_id)}")
    new_alias = input(f"   Alias [{info.get('alias', 'N/D')}]: ").strip()
    if new_alias:
        info["alias"] = new_alias
    new_expiry = input(f"   Scadenza [{info.get('expiry', 'N/D')}]: ").strip()
    if new_expiry:
        try:
            datetime.strptime(new_expiry, "%Y-%m-%d")
            info["expiry"] = new_expiry
        except ValueError:
            print("❌ Data non valida. Lasciata invariata.")
    active_input = input(f"   Attivo? (s/n) [{info.get('active', False)}]: ").strip().lower()
    if active_input in ["s", "si", "y", "yes"]:
        info["active"] = True
    elif active_input in ["n", "no"]:
        info["active"] = False
    save_licenses(data)
    print("✅ Licenza aggiornata.")
    input("\nPremi INVIO per continuare...")

def delete_license(data):
    print("\n" + "=" * 50)
    print("🗑️ ELIMINA LICENZA")
    print("=" * 50)
    device_id = input("🆔 Device ID da eliminare: ").strip()
    if device_id not in data["devices"]:
        print("❌ Device ID non trovato.")
        input("\nPremi INVIO per continuare...")
        return
    alias = data['devices'][device_id].get('alias', device_id)
    confirm = input(f"⚠️ Eliminare '{alias}'? (s/n): ").strip().lower()
    if confirm in ["s", "si", "y", "yes"]:
        del data["devices"][device_id]
        save_licenses(data)
        print("✅ Licenza eliminata.")
    else:
        print("❌ Operazione annullata.")
    input("\nPremi INVIO per continuare...")

def generate_code(data):
    print("\n" + "=" * 50)
    print("🔑 GENERAZIONE CODICE")
    print("=" * 50)
    device_id = input("🆔 Device ID: ").strip()
    if device_id not in data["devices"]:
        print("❌ Device ID non trovato.")
        input("\nPremi INVIO per continuare...")
        return
    info = data["devices"][device_id]
    expiry = info.get("expiry", "")
    if not expiry:
        print("❌ Il dispositivo non ha una data di scadenza.")
        input("\nPremi INVIO per continuare...")
        return
    code_data = f"{device_id}|{expiry}"
    h = hmac.new(HMAC_KEY, code_data.encode(), hashlib.sha256)
    hmac_hex = h.hexdigest()
    code = f"{expiry}|{hmac_hex}"
    print("\n" + "=" * 60)
    print(f"🔑 Codice di attivazione per {info.get('alias', device_id)}")
    print("=" * 60)
    print(f"Device ID : {device_id}")
    print(f"Scadenza  : {expiry}")
    print(f"Codice    : {code}")
    print("=" * 60)
    input("\nPremi INVIO per continuare...")

def main():
    data = load_licenses()
    while True:
        clear_screen()
        print("=" * 50)
        print("📋 GESTIONE LICENZE MyViewIPTV")
        print("=" * 50)
        print("1. 📋 Lista licenze")
        print("2. ➕ Aggiungi licenza")
        print("3. ✏️ Modifica licenza")
        print("4. 🗑️ Elimina licenza")
        print("5. 🔑 Genera codice attivazione")
        print("6. 🚪 Esci")
        choice = input("\nScegli un'opzione (1-6): ").strip()
        if choice == "1":
            list_licenses(data)
            input("\nPremi INVIO per continuare...")
        elif choice == "2":
            add_license(data)
        elif choice == "3":
            edit_license(data)
        elif choice == "4":
            delete_license(data)
        elif choice == "5":
            generate_code(data)
        elif choice == "6":
            print("Arrivederci!")
            break
        else:
            print("❌ Opzione non valida.")
            input("\nPremi INVIO per continuare...")

if __name__ == "__main__":
    main()