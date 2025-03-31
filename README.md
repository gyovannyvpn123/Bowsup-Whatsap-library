# Bocksup - WhatsApp Integration Library

Bocksup este o bibliotecă Python care replică funcționalitatea bibliotecii yowsup pentru integrarea cu WhatsApp, cu stabilitate îmbunătățită, tratare mai bună a erorilor și compatibilitate cu versiunile moderne de Python.

## Stare actuală

**Status: Alpha**

Biblioteca este în faza de dezvoltare activă și încă nu este complet funcțională pentru comunicarea cu serverele WhatsApp. Implementarea actuală oferă o bază solidă pentru a construi o alternativă la yowsup, dar necesită contribuții suplimentare pentru a deveni complet operațională.

### Funcționalități implementate:

- ✅ Structura și arhitectura modular completă a bibliotecii
- ✅ Implementarea protocoalelor WebSocket pentru WhatsApp Web
- ✅ Suport pentru autentificare prin pairing code și WebSocket
- ✅ Module pentru serializarea și parsarea mesajelor
- ✅ Client pentru înregistrarea numerelor noi
- ✅ Implementarea protocolului Signal pentru criptare end-to-end
- ✅ Modul pentru testare și integrare cu serverele WhatsApp reale

### Ghiduri pentru implementare completă:

Biblioteca include documentație detaliată despre cum să se facă pe deplin funcțională cu serverele WhatsApp reale:

- [Ghid de implementare funcțională](bocksup/docs/implementare_functionala.md) - Pași pentru a face biblioteca complet funcțională
- [Troubleshooting](bocksup/docs/troubleshooting.md) - Diagnosticarea și rezolvarea problemelor comune

## Instalare

```bash
pip install bocksup  # când va fi disponibil pe PyPI
```

Pentru a instala din sursă:

```bash
git clone https://github.com/username/bocksup.git
cd bocksup
pip install -e .
```

## Utilizare de bază

```python
import asyncio
from bocksup import create_stack

async def main():
    # Creează stack-ul cu credențialele WhatsApp
    credentials = ('phone_number', 'password')  # sau token-ul generat anterior
    stack = create_stack(credentials)
    
    # Conectare și autentificare
    await stack.connect()
    
    # Trimiterea unui mesaj
    await stack.send_message('123456789@s.whatsapp.net', 'Salut din Bocksup!')
    
    # Așteptarea și procesarea mesajelor primite
    async for message in stack.messages():
        print(f"Mesaj de la {message['from']}: {message['body']}")
    
    # Deconectare
    await stack.disconnect()

asyncio.run(main())
```

## Înregistrarea unui număr nou

```python
import asyncio
from bocksup.registration import RegistrationClient

async def main():
    # Creează client de înregistrare
    client = RegistrationClient()
    
    # Solicită cod de verificare prin SMS
    phone_number = '123456789'  # fără + la început
    result = await client.request_code(phone_number, method='sms')
    
    if result['success']:
        # Așteaptă primirea codului de verificare pe telefon
        verification_code = input('Introdu codul primit prin SMS: ')
        
        # Înregistrează numărul cu codul primit
        reg_result = await client.register_code(phone_number, verification_code)
        
        if reg_result['success']:
            print(f"Înregistrare reușită! Password: {reg_result['password']}")
            print("Folosește această parolă pentru autentificare")
        else:
            print(f"Eroare la înregistrare: {reg_result['reason']}")
    else:
        print(f"Eroare la solicitarea codului: {result['reason']}")

asyncio.run(main())
```

## Autentificare cu Pairing Code

```python
import asyncio
from bocksup.auth import Authenticator

async def main():
    # Creează autentificator
    auth = Authenticator('123456789', 'password')
    
    # Autentifică folosind metoda WebSocket care suportă pairing code
    success = await auth.authenticate()
    
    if success:
        print("Autentificare reușită!")
    else:
        print("Autentificare eșuată!")

asyncio.run(main())
```

## Contribuții

Contribuțiile sunt binevenite! Biblioteca este în faza de dezvoltare și are nevoie de contribuții în următoarele domenii:

1. Implementarea completă a protocolului de comunicare WhatsApp
2. Implementarea criptării end-to-end (Signal Protocol)
3. Suport pentru gestionarea grupurilor
4. Manipularea media (imagini, video, audio)
5. Teste și documentație

## Licență

MIT License

## Mulțumiri

- Proiectului yowsup pentru inspirație și înțelegerea protocolului WhatsApp
- Comunității pentru contribuții și raportarea bug-urilor