# Bocksup - WhatsApp Integration Library

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