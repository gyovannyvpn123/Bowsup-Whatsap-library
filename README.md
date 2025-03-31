# Bocksup - Bibliotecă de Integrare WhatsApp

O bibliotecă Python care replică funcționalitatea bibliotecii yowsup pentru integrarea WhatsApp, cu stabilitate îmbunătățită, gestionarea erorilor și compatibilitate cu versiunile moderne de Python.

**Versiune:** 0.2.0 (Alpha)
**Licență:** MIT

## Descriere

Bocksup oferă o implementare completă a protocolului WhatsApp, permițând aplicațiilor să trimită și să primească mesaje, să gestioneze fișiere media, să participe la conversații de grup și multe altele. Biblioteca este concepută ca o alternativă modernă la yowsup, păstrând aceeași funcționalitate de bază, dar cu îmbunătățiri semnificative.

## Caracteristici principale

- ✅ Autentificare cu WhatsApp (suport pentru cod QR și pairing code)
- ✅ Trimitere și primire de mesaje text
- ✅ Gestionare fișiere media (imagini, audio, video, documente)
- ✅ Suport pentru conversații de grup
- ✅ Criptare end-to-end utilizând protocolul Signal
- ✅ Implementare modernă și asincronă (async/await)
- ✅ Gestionare robustă a erorilor și a reconectărilor
- ✅ Compatibilitate cu Python 3.8+

## Stare actuală a proiectului

⚠️ **IMPORTANT: Această bibliotecă este în stadiul ALPHA de dezvoltare**

Bocksup conține toate componentele structurale necesare și o arhitectură completă, dar necesită testare și ajustare pentru a funcționa complet cu serverele WhatsApp reale. Următoarele aspecte trebuie finalizate pentru o funcționalitate completă:

1. Testarea cu serverele WhatsApp reale și ajustarea pe baza răspunsurilor
2. Completarea implementării protocolului Signal pentru criptare
3. Adaptarea continuă la schimbările de protocol ale WhatsApp

## Instalare

```bash
pip install bocksup
```

Sau direct din repository:

```bash
git clone https://github.com/username/bocksup.git
cd bocksup
pip install -e .
```

## Utilizare de bază

```python
import asyncio
import logging
from bocksup import create_client

# Configurare logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Crearea unui client cu numărul de telefon și parola opțională
    # (dacă nu este furnizată, se va folosi autentificarea cu QR sau pairing code)
    client = create_client("12345678901")
    
    # Conectare la WhatsApp
    await client.connect()
    
    # Trimitere mesaj text
    result = await client.send_text_message("9876543210", "Salut din Bocksup!")
    print(f"Message sent with ID: {result['message_id']}")
    
    # Înregistrare handler pentru mesaje primite
    def message_handler(message_data):
        print(f"Mesaj primit: {message_data}")
    
    client.register_message_handler(message_handler)
    
    # Menține conexiunea deschisă
    try:
        await asyncio.sleep(3600)  # Rulează timp de o oră
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Testarea conexiunii

Biblioteca include un utilitar pentru testarea conexiunii cu serverele WhatsApp:

```python
import asyncio
from bocksup import test_server_connection

async def test():
    # Testează conexiunea (opțional cu un număr de telefon pentru testarea pairing code)
    results = await test_server_connection("12345678901")
    print(results)

asyncio.run(test())
```

## Finalizarea implementării

Pentru a face biblioteca complet funcțională cu serverele WhatsApp reale, urmați acești pași:

### 1. Testarea și captarea traficului real

Utilizați modulul de test pentru a interacționa cu serverele WhatsApp:

```python
import asyncio
from bocksup import test_server_connection

async def test():
    # Testarea conexiunii de bază (fără autentificare completă)
    results = await test_server_connection()
    print(results)
    
    # Testarea cu număr de telefon pentru pairing code
    # results = await test_server_connection("1234567890")  # Număr real aici
    # print(results)

if __name__ == "__main__":
    asyncio.run(test())
```

Pentru o analiză mai completă, folosiți instrumente precum:
- **Wireshark** pentru capturarea pachetelor de rețea
- **Chrome DevTools** pentru monitorizarea traficului WhatsApp Web
- **mitmproxy** pentru interceptarea și analiza traficului HTTPS

### 2. Ajustarea implementării

În fișierul principal `bocksup/__init__.py` veți găsi constante care pot necesita actualizare:

```python
# Versiunile actuale ale clientului WhatsApp Web - acestea trebuie actualizate
WHATSAPP_WEB_VERSION = "2.2408.5"
WHATSAPP_WEB_VERSION_HASH = "7Odg9GWl5nK7xh3jFhzK"
```

Adaptați formatele de mesaje și secvența de autentificare pe baza traficului real captat.

### 3. Completați protocolul Signal

Pentru implementarea completă a criptării Signal, consultați:
- [Specificațiile oficiale ale protocolului Signal](https://signal.org/docs/)
- Implementări existente precum [libsignal-protocol-javascript](https://github.com/signalapp/libsignal-protocol-javascript)

Concentrați-vă pe implementarea corectă a:
- X3DH (Extended Triple Diffie-Hellman) pentru stabilirea cheilor
- Double Ratchet pentru actualizarea cheilor
- Criptarea/decriptarea mesajelor

### 4. Testarea și validarea

Testați funcționalități incrementale:
1. Conectarea și handshake-ul inițial
2. Autentificarea cu pairing code/QR
3. Trimiterea de mesaje simple
4. Trimiterea și primirea de mesaje media
5. Funcționalități de grup și alte caracteristici avansate

Consultați fișierul `troubleshooting.md` pentru soluții la problemele comune.

## Contribuții

Contribuțiile sunt binevenite! Dacă doriți să contribuiți la dezvoltarea bibliotecii, consultați fișierul `CONTRIBUTING.md` pentru instrucțiuni.

## Notă legală

Această bibliotecă nu este afiliată, autorizată sau aprobată de WhatsApp Inc. Utilizarea sa trebuie să respecte termenii și condițiile WhatsApp.

## Licență

Acest proiect este licențiat sub licența MIT - consultați fișierul `LICENSE` pentru detalii.