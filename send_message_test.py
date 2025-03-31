#!/usr/bin/env python3
"""
Script pentru trimiterea unui mesaj WhatsApp folosind biblioteca Bocksup.
"""

import asyncio
import logging
import bocksup
from bocksup.messaging.client import MessagingClient

# Configurare logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SendMessage")

# Configurare detalii mesaj
NUMAR_EXPEDITOR = "40748427351"  # Numărul tău
NUMAR_DESTINATAR = "40756469325"  # Numărul către care trimiți mesajul
MESAJ = "Acesta este un test de la biblioteca Bocksup!"

async def get_pairing_code(phone_number):
    """
    Solicită și afișează un cod de asociere pentru numărul de telefon specificat.
    
    Args:
        phone_number: Numărul de telefon pentru care se solicită codul
        
    Returns:
        Codul de asociere sau None dacă solicitarea eșuează
    """
    logger.info(f"Solicitare cod de asociere pentru numărul {phone_number}...")
    
    try:
        # Apelăm funcția de test cu numărul de telefon
        result = await bocksup.test_server_connection(phone_number)
        
        if result.get('pairing_code', False):
            pairing_code = None
            for msg in result.get('messages', []):
                if 'pairing_code' in str(msg):
                    # Încercăm să extragem codul de asociere din mesaj
                    import re
                    match = re.search(r'pairing_code.*?(\d{6})', str(msg))
                    if match:
                        pairing_code = match.group(1)
            
            if pairing_code:
                logger.info(f"✅ Cod de asociere primit: {pairing_code}")
                return pairing_code
            else:
                logger.info("✅ Solicitare cod de asociere reușită! Verificați telefonul pentru cod.")
                pairing_code = input("Introduceți codul de asociere afișat pe telefon: ")
                return pairing_code
        else:
            logger.error("❌ Solicitare cod de asociere eșuată!")
            return None
            
    except Exception as e:
        logger.error(f"Eroare la solicitarea codului de asociere: {e}")
        return None

async def send_message():
    """
    Trimite un mesaj WhatsApp folosind biblioteca Bocksup.
    """
    logger.info(f"Pregătire pentru trimiterea unui mesaj de la {NUMAR_EXPEDITOR} către {NUMAR_DESTINATAR}")
    
    # Solicită un cod de asociere
    pairing_code = await get_pairing_code(NUMAR_EXPEDITOR)
    
    if not pairing_code:
        logger.error("Nu s-a putut obține codul de asociere. Trimiterea mesajului este imposibilă.")
        return
    
    logger.info(f"Autentificare cu codul de asociere: {pairing_code}")
    
    try:
        # Creare client de mesagerie (fără parolă, doar cu număr de telefon)
        client = MessagingClient(NUMAR_EXPEDITOR)
        
        # Autentificare și conectare
        logger.info("Conectare la WhatsApp...")
        connect_result = await client.connect()
        
        if not connect_result:
            logger.error("Conectare eșuată!")
            return
        
        logger.info("Conectare reușită! Trimitere mesaj...")
        
        # Trimitere mesaj
        result = await client.send_text_message(NUMAR_DESTINATAR, MESAJ)
        logger.info(f"Rezultat trimitere: {result}")
        
        # Deconectare
        await client.disconnect()
        logger.info("Mesaj trimis și deconectat.")
        
    except Exception as e:
        logger.error(f"Eroare la trimiterea mesajului: {e}")

async def main():
    """Funcția principală."""
    logger.info("Începere test trimitere mesaj...")
    await send_message()
    logger.info("Test finalizat!")

if __name__ == "__main__":
    asyncio.run(main())