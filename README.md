# Bocksup - Biblioteca de Integrare WhatsApp

Bocksup este o bibliotecă Python modernă pentru integrarea cu WhatsApp, inspirată de biblioteca yowsup dar complet rescrisă pentru Python 3, cu suport îmbunătățit pentru protocolul actual WhatsApp și management mai bun al erorilor.

## Descriere

Biblioteca permite conectarea la serverele WhatsApp și oferă suport pentru:
- Autentificare prin cod de asociere (pairing code)
- Comunicare cu serverele WhatsApp prin WebSockets
- Criptare end-to-end folosind protocolul Signal
- Management complex al mesajelor și contactelor
- Suport pentru media și grupuri

## Caracteristici

- **Compatibilitate Python 3**: Codul este complet compatibil cu versiunile moderne de Python
- **Arhitectură modulară**: Structură bazată pe layere care facilitează extensibilitatea
- **Management optimizat al erorilor**: Gestionarea robustă a erorilor și excepțiilor
- **Interfață web de test**: Pentru testarea facilă a funcționalităților
- **Documentație detaliată**: În română cu exemple de implementare

## Instalare

```bash
pip install bocksup
```

## Utilizare Rapidă

```python
import asyncio
from bocksup import create_client

async def main():
    # Creare client WhatsApp
    client = create_client("4071234xxxx")  # înlocuiește cu numărul tău
    
    # Conectare la WhatsApp
    connected = await client.connect()
    
    if connected:
        # Trimitere mesaj text
        result = await client.send_text_message("4071234xxxx", "Salut de la Bocksup!")
        print(f"Mesaj trimis: {result}")
        
        # Deconectare
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Structură Cod

Codul este organizat în module specializate:
- `auth`: Module pentru autentificare și gestionarea credențialelor
- `messaging`: Funcționalități pentru trimiterea și primirea mesajelor
- `encryption`: Implementarea criptării pentru comunicații sigure
- `layers`: Structura pe straturi pentru comunicare (network, protocol, etc.)
- `media`: Suport pentru conținut multimedia (imagini, video, documente)
- `groups`: Gestionarea grupurilor WhatsApp
- `contacts`: Gestionarea contactelor și a listei de contacte

## Statut

Biblioteca este în stadiu alpha (versiunea 0.2.0) și este în continuă dezvoltare pentru a adăuga noi funcționalități și a îmbunătăți stabilitatea.

## Contribuții

Contribuțiile sunt binevenite! Pentru a contribui:
1. Fork repository-ul
2. Creează un branch pentru funcționalitatea nouă (`git checkout -b feature/amazing-feature`)
3. Commit schimbările (`git commit -m 'Add some amazing feature'`)
4. Push către branch (`git push origin feature/amazing-feature`)
5. Deschide un Pull Request

## Licență

Acest proiect este licențiat sub MIT License - vezi fișierul `LICENSE` pentru detalii.

## Mulțumiri

- Echipei yowsup pentru inspirație și cercetare inițială
- Comunității pentru testare și feedback

## Contact

Pentru întrebări și suport, vă rugăm să deschideți un issue pe GitHub.

---

**Notă**: Această bibliotecă este un proiect independent și nu este afiliată oficial cu WhatsApp sau Meta. Utilizați pe propria răspundere și în conformitate cu termenii și condițiile WhatsApp.

## Overview
Bocksup este o bibliotecă Python ce replică funcționalitatea yowsup pentru integrarea cu WhatsApp, dar cu îmbunătățiri semnificative în ceea ce privește stabilitatea, tratarea erorilor și compatibilitatea cu versiuni moderne de Python.

## Features
- **Authentication** - Autentificare completă folosind protocolul WebSocket actualizat
- **Messaging** - Trimitere și primire de mesaje text
- **Encryption** - Criptare end-to-end folosind Signal Protocol
- **Groups** - Suport pentru grupuri (în dezvoltare)
- **Media** - Suport pentru fișiere multimedia (în dezvoltare)
- **Registration** - Înregistrare simplificată cu cod de asociere

## Installation
```bash
# Clone repository
git clone https://github.com/username/bocksup.git
cd bocksup

# Install dependencies
pip install -e .
```

## Quick Start
```python
import asyncio
import bocksup

async def example():
    # Test connection to WhatsApp servers
    result = await bocksup.test_server_connection()
    print(f"Connection established: {'✓' if result.get('connection') else '✗'}")
    
    # Create a client with phone number
    phone_number = "123456789"  # Replace with your phone number
    client = bocksup.create_client(phone_number)
    
    # Use the client for more operations
    
# Run the async example
asyncio.run(example())
```

## Debugging
Aplicația web inclusă oferă o interfață simplă pentru testarea și depanarea bibliotecii:

1. Rulați `python main.py`
2. Deschideți un browser la `http://localhost:5000`
3. Folosiți pagina de debug pentru a testa conexiunea la serverele WhatsApp

## Documentation
Pentru mai multe detalii, consultați:
- [Documentația completă](docs/implementare_functionala.md)
- [Troubleshooting](docs/troubleshooting.md)

## Comparație cu yowsup
- **Stabilitate îmbunătățită** - Gestionare mai robustă a erorilor de rețea
- **Arhitectură modernă** - Utilizare de asyncio în loc de threads
- **Protocol actualizat** - Implementare bazată pe WebSocket pentru compatibilitate cu versiunile recente WhatsApp
- **Documentație extinsă** - Exemple și ghiduri detaliate

## Versiune curentă
Versiunea curentă este **0.2.0** (alpha) - Structura de bază este implementată, iar funcționalitatea completă este în dezvoltare.

## License
This project is licensed under the MIT License - see the LICENSE file for details.