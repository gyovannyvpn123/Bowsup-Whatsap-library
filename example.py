"""
Exemplu simplu de utilizare a bibliotecii Bocksup pentru WhatsApp.

Acest exemplu demonstrează operațiuni de bază: conectare, trimitere de mesaje,
și primire de mesaje folosind biblioteca Bocksup.
"""

import asyncio
import logging
import os
import sys

# Adăugăm directorul curent în path pentru a importa bocksup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bocksup

# Configurarea logging-ului
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bocksup_example')

async def main():
    """
    Funcție principală pentru a demonstra utilizarea bibliotecii Bocksup.
    """
    logger.info("Inițializarea exemplului Bocksup")
    
    # Obțineți numărul de telefon din argumentele liniei de comandă sau utilizați unul de test
    phone_number = sys.argv[1] if len(sys.argv) > 1 else None
    recipient = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not phone_number:
        logger.warning("Nu s-a specificat niciun număr de telefon. Rulați cu: python example.py număr_telefon [destinatar]")
        logger.info("Se execută testul de conexiune pentru diagnosticare...")
        
        # Testăm conexiunea la serverele WhatsApp pentru diagnosticare
        try:
            results = await bocksup.test_server_connection()
            
            logger.info("Rezultate test de conexiune:")
            logger.info(f"- Conexiune: {'SUCCES' if results.get('connection') else 'EȘEC'}")
            logger.info(f"- Handshake: {'SUCCES' if results.get('handshake') else 'EȘEC'}")
            
            if results.get('errors'):
                logger.warning("Erori întâlnite:")
                for error in results.get('errors', []):
                    logger.warning(f"  - {error}")
            
            return
        except Exception as e:
            logger.error(f"Eroare la testarea conexiunii: {e}")
            return
    
    # Crearea clientului WhatsApp (fără parolă pentru autentificare QR/pairing code)
    logger.info(f"Crearea clientului WhatsApp pentru numărul {phone_number}")
    client = bocksup.create_client(phone_number)
    
    # Handler pentru mesaje primite
    async def message_handler(message_data):
        logger.info(f"Mesaj primit: {message_data}")
        
        # Răspunde automat la mesaje text (un simplu echo bot)
        if message_data.get('type') == 'chat' and 'content' in message_data:
            sender = message_data.get('from')
            content = message_data.get('content')
            
            if sender and content:
                response = f"Ai trimis: {content}"
                logger.info(f"Trimitere răspuns către {sender}: {response}")
                
                try:
                    await client.send_text_message(sender, response)
                except Exception as e:
                    logger.error(f"Eroare la trimiterea răspunsului: {e}")
    
    # Handler pentru confirmări de primire
    async def receipt_handler(receipt_data):
        logger.info(f"Confirmare primită: {receipt_data}")
    
    # Handler pentru actualizări de prezență
    async def presence_handler(presence_data):
        logger.info(f"Actualizare de prezență: {presence_data}")
    
    # Înregistrarea handler-elor
    client.register_message_handler(message_handler)
    client.register_receipt_handler(receipt_handler)
    client.register_presence_handler(presence_handler)
    
    try:
        # Conectare la WhatsApp
        logger.info("Conectare la serverele WhatsApp...")
        connected = await client.connect()
        
        if not connected:
            logger.error("Conectare eșuată")
            return
        
        logger.info("Conectare reușită")
        
        # Trimitere mesaj de test dacă s-a specificat un destinatar
        if recipient:
            try:
                logger.info(f"Trimitere mesaj de test către {recipient}")
                result = await client.send_text_message(
                    recipient, 
                    "Acesta este un mesaj de test trimis de biblioteca Bocksup!"
                )
                logger.info(f"Mesaj trimis cu ID: {result.get('message_id')}")
            except Exception as e:
                logger.error(f"Eroare la trimiterea mesajului: {e}")
        
        # Menține conexiunea activă și procesează mesajele primite
        logger.info("Așteptare mesaje (apăsați Ctrl+C pentru a ieși)...")
        
        # În mod normal am folosi un event loop continuu, dar pentru exemplu punem o limită
        await asyncio.sleep(3600)  # Rulează timp de o oră
        
    except KeyboardInterrupt:
        logger.info("Oprire solicitată de utilizator")
    except Exception as e:
        logger.error(f"Eroare: {e}")
    finally:
        # Deconectare
        if client:
            logger.info("Deconectare de la WhatsApp")
            await client.disconnect()
    
    logger.info("Exemplu finalizat")

if __name__ == "__main__":
    # Rulare loop asincron
    asyncio.run(main())