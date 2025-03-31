#!/usr/bin/env python3
"""
Script pentru obținerea unui cod de asociere pentru autentificare WhatsApp.
"""

import asyncio
import logging
import bocksup

# Setarea nivelului de logging pentru a vedea detalii ale procesului
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PairingCode")

# Numărul de telefon pentru care solicităm codul de asociere
PHONE_NUMBER = "40748427351"

async def get_pairing_code():
    """Obține codul de asociere pentru numărul de telefon specificat."""
    logger.info(f"Solicitare cod de asociere pentru numărul {PHONE_NUMBER}...")
    
    try:
        # Apelăm funcția test_server_connection cu numărul de telefon pentru a solicita un cod de asociere
        result = await bocksup.test_server_connection(PHONE_NUMBER)
        
        # Afișăm rezultatul complet pentru a vedea toate detaliile
        logger.info(f"Rezultat complet: {result}")
        
        # Verificăm dacă a fost solicitat un cod de asociere
        if result.get('pairing_code', False):
            logger.info("✅ Solicitare cod de asociere reușită!")
            
            # Încercăm să extragem codul de asociere din mesaje
            for msg in result.get('messages', []):
                logger.info(f"Mesaj: {msg}")
                if isinstance(msg, dict) and 'content' in msg:
                    content = msg['content']
                    if isinstance(content, dict) and 'pairingCode' in content:
                        code = content['pairingCode']
                        logger.info(f"✅ Cod de asociere găsit: {code}")
                        return code
            
            logger.info("Codul de asociere ar trebui să se afișeze pe telefonul dvs.")
            logger.info("Verificați telefonul și introduceți codul când apare.")
        else:
            logger.error("❌ Solicitare cod de asociere eșuată!")
            
    except Exception as e:
        logger.error(f"Eroare la solicitarea codului de asociere: {e}")
    
    return None

async def main():
    """Funcția principală."""
    logger.info("Începere proces obținere cod de asociere...")
    
    # Obținem codul de asociere
    pairing_code = await get_pairing_code()
    
    if pairing_code:
        logger.info(f"Cod de asociere obținut: {pairing_code}")
        logger.info("Folosiți acest cod pentru a autentifica aplicația pe telefonul dvs.")
    else:
        logger.info("Nu s-a putut obține codul de asociere automat.")
        logger.info("Verificați telefonul pentru a vedea dacă a apărut un cod de asociere.")
    
    logger.info("Proces finalizat!")

if __name__ == "__main__":
    asyncio.run(main())