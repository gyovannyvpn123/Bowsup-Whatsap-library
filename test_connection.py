#!/usr/bin/env python3
"""
Script pentru testarea conexiunii la serverele WhatsApp.

Acest script folosește modulul bocksup pentru a testa conectarea la 
serverele WhatsApp reale și captează detaliile răspunsurilor pentru
dezvoltarea viitoare a bibliotecii.
"""

import asyncio
import logging
import json
import argparse
import os
from typing import Optional

# Configurarea logging-ului
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('connection_test')

async def test_connection(phone_number: Optional[str] = None, capture: bool = True):
    """
    Testează conexiunea la serverele WhatsApp.
    
    Args:
        phone_number: Număr de telefon pentru testarea codului de asociere (opțional)
        capture: Dacă să salveze răspunsurile într-un fișier pentru analiză
    """
    try:
        # Importarea modulelor necesare
        from bocksup import test_server_connection, WhatsAppConnection, __version__
        
        logger.info(f"Bocksup versiunea {__version__}")
        logger.info("Începerea testelor de conexiune...")
        
        # Testul principal
        results = await test_server_connection(phone_number)
        
        # Afișarea rezultatelor
        logger.info("===== REZULTATE TEST CONEXIUNE =====")
        logger.info(f"Conexiune: {'SUCCES' if results['connection'] else 'EȘEC'}")
        logger.info(f"Handshake: {'SUCCES' if results['handshake'] else 'EȘEC'}")
        
        if phone_number:
            logger.info(f"Challenge primit: {'DA' if results['challenge'] else 'NU'}")
            logger.info(f"Pairing code solicitat: {'DA' if results['pairing_code'] else 'NU'}")
        
        if 'errors' in results and results['errors']:
            logger.warning("Erori întâlnite:")
            for error in results['errors']:
                logger.warning(f"- {error}")
                
        # Salvarea rezultatelor
        if capture:
            capture_file = "whatsapp_connection_test_results.json"
            with open(capture_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Rezultatele au fost salvate în {capture_file}")
            
        return results
        
    except ImportError:
        logger.error("Nu s-a putut importa modulul bocksup. Asigură-te că este instalat corect.")
        return {"connection": False, "errors": ["Import error"]}
    except Exception as e:
        logger.error(f"Eroare la testarea conexiunii: {e}")
        return {"connection": False, "errors": [str(e)]}

async def test_websocket_internals():
    """
    Testează direct funcționalitatea WebSocket pentru a capta mai multe detalii.
    """
    try:
        import websockets
        import ssl
        import uuid
        import time
        
        # Simulează direct comportamentul WhatsApp Web
        USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        WEBSOCKET_URL = "wss://web.whatsapp.com/ws"
        
        logger.info("Testarea directă a conexiunii WebSocket...")
        
        # Configurare SSL
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        
        # Pregătire headers
        headers = {
            "User-Agent": USER_AGENT,
            "Origin": "https://web.whatsapp.com",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
        }
        
        # Conectare
        client_id = str(uuid.uuid4())
        logger.info(f"Client ID: {client_id}")
        logger.info(f"Conectare la {WEBSOCKET_URL}...")
        
        async with websockets.connect(
            WEBSOCKET_URL,
            ssl=ssl_context,
            extra_headers=headers,
            ping_interval=None,
            ping_timeout=None
        ) as websocket:
            logger.info("Conexiune stabilită!")
            
            # Creare mesaj handshake
            handshake_message = [
                "admin",
                "init",
                ["2.2409.6", "Windows", "Chrome", "10"],
                [USER_AGENT],
                client_id,
                True
            ]
            
            # Trimitere handshake
            logger.info("Trimitere handshake...")
            message_tag = str(int(time.time()))
            await websocket.send(f"{message_tag},{json.dumps(handshake_message)}")
            
            # Așteptare răspuns
            logger.info("Așteptare răspuns handshake...")
            response = await websocket.recv()
            logger.info(f"Răspuns primit: {response[:200]}...")
            
            # Captarea răspunsului
            with open("whatsapp_raw_handshake_response.txt", "w") as f:
                f.write(response)
            logger.info("Răspuns handshake salvat în 'whatsapp_raw_handshake_response.txt'")
            
            # Analiză răspuns
            try:
                resp_parts = response.split(",", 1)
                if len(resp_parts) > 1:
                    resp_tag, resp_data = resp_parts
                    resp_json = json.loads(resp_data)
                    logger.info(f"Tip răspuns: {resp_json.get('type', 'necunoscut')}")
                    
                    # Salvare răspuns JSON
                    with open("whatsapp_parsed_handshake_response.json", "w") as f:
                        json.dump(resp_json, f, indent=2)
                    logger.info("Răspuns JSON salvat în 'whatsapp_parsed_handshake_response.json'")
            except Exception as e:
                logger.error(f"Eroare la analiza răspunsului: {e}")
            
            # Așteptare scurt pentru eventuale mesaje adiționale
            logger.info("Așteptare mesaje adiționale (5 secunde)...")
            try:
                for i in range(5):
                    response = await asyncio.wait_for(websocket.recv(), timeout=1)
                    logger.info(f"Mesaj adițional primit ({i+1}): {response[:100]}...")
                    
                    # Salvare mesaj adițional
                    with open(f"whatsapp_additional_message_{i+1}.txt", "w") as f:
                        f.write(response)
            except asyncio.TimeoutError:
                logger.info("Nu s-au mai primit mesaje adiționale.")
            except Exception as e:
                logger.error(f"Eroare la primirea mesajelor adiționale: {e}")
            
            logger.info("Test WebSocket direct încheiat cu succes!")
            
    except ImportError:
        logger.error("Nu s-au putut importa modulele necesare. Asigură-te că 'websockets' este instalat.")
    except Exception as e:
        logger.error(f"Eroare la testul WebSocket direct: {e}")

async def main():
    """Funcția principală pentru testarea conexiunii."""
    parser = argparse.ArgumentParser(description="Test de conexiune la serverele WhatsApp")
    parser.add_argument("--phone", "-p", help="Număr de telefon pentru testarea pairing code", default=None)
    parser.add_argument("--direct", "-d", action="store_true", help="Testează direct WebSocket fără bocksup")
    parser.add_argument("--no-capture", "-n", action="store_true", help="Nu salva rezultatele în fișiere")
    args = parser.parse_args()
    
    # Test prin biblioteca bocksup
    if not args.direct:
        await test_connection(args.phone, not args.no_capture)
    
    # Test direct WebSocket
    if args.direct:
        await test_websocket_internals()

if __name__ == "__main__":
    asyncio.run(main())