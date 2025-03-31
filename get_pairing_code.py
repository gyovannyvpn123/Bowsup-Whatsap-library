#!/usr/bin/env python3
"""
Bocksup - Script pentru obținerea codului de asociere WhatsApp

Acest script demonstrează cum să folosiți biblioteca Bocksup pentru a obține
un cod de asociere WhatsApp pentru un număr de telefon specificat.
"""

import asyncio
import logging
import argparse
import sys
from typing import Optional

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("Bocksup-Web")

# Importați modulele Bocksup
from bocksup import create_client, test_server_connection
from bocksup.auth import Authenticator

async def get_pairing_code(phone_number: str) -> Optional[str]:
    """
    Obține un cod de asociere WhatsApp pentru numărul de telefon specificat.
    
    Args:
        phone_number: Numărul de telefon în format internațional (ex: 40712345678)
        
    Returns:
        Codul de asociere sau None dacă a eșuat
    """
    try:
        logger.info(f"Solicitare cod de asociere pentru numărul: {phone_number}")
        
        # Creați un autentificator (fără parolă pentru a forța solicitarea codului de asociere)
        authenticator = Authenticator(phone_number)
        
        # Autentificați și obțineți codul
        authenticated = await authenticator.authenticate()
        
        if authenticated and authenticator.pairing_code:
            logger.info(f"Cod de asociere obținut: {authenticator.pairing_code}")
            return authenticator.pairing_code
        else:
            logger.error("Nu s-a putut obține codul de asociere")
            return None
            
    except Exception as e:
        logger.error(f"Eroare la obținerea codului de asociere: {str(e)}")
        return None
    finally:
        # Asigurați-vă că se închide conexiunea
        if hasattr(authenticator, 'connection') and authenticator.connection:
            await authenticator.connection.disconnect()

async def test_connection(phone_number: Optional[str] = None) -> None:
    """
    Testează conexiunea la serverele WhatsApp.
    
    Args:
        phone_number: Opțional, număr de telefon pentru testarea codului de asociere
    """
    try:
        logger.info("Testare conexiune la serverele WhatsApp...")
        
        results = await test_server_connection(phone_number)
        
        logger.info(f"Rezultate test:")
        logger.info(f"- Conexiune: {'✓' if results['connection'] else '✗'}")
        logger.info(f"- Handshake: {'✓' if results['handshake'] else '✗'}")
        logger.info(f"- Challenge: {'✓' if results['challenge'] else '✗'}")
        
        if phone_number:
            logger.info(f"- Cod asociere: {'✓' if results['pairing_code'] else '✗'}")
        
        if results['errors']:
            logger.error("Erori întâlnite în timpul testului:")
            for error in results['errors']:
                logger.error(f"  - {error}")
    
    except Exception as e:
        logger.error(f"Eroare la testare: {str(e)}")

async def main(phone_number: str, test_only: bool = False) -> None:
    """
    Funcția principală care rulează testele sau obține codul de asociere.
    
    Args:
        phone_number: Numărul de telefon în format internațional
        test_only: Doar testare, fără solicitare cod de asociere
    """
    if test_only:
        await test_connection(phone_number if phone_number else None)
    else:
        if not phone_number:
            logger.error("Trebuie să specificați un număr de telefon pentru a obține un cod de asociere")
            return
        
        pairing_code = await get_pairing_code(phone_number)
        
        if pairing_code:
            # Formatăm codul de asociere pentru afișare
            logger.info(f"Codul de asociere pentru {phone_number}: {pairing_code}")
            logger.info(f"Introduceți acest cod în aplicația WhatsApp pentru a finaliza asocierea")
        else:
            logger.error("Nu s-a putut obține un cod de asociere. Verificați log-urile pentru detalii.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Obțineți un cod de asociere WhatsApp")
    parser.add_argument("--phone", type=str, help="Număr de telefon în format internațional (ex: 40712345678)")
    parser.add_argument("--test", action="store_true", help="Doar testare, fără solicitare cod de asociere")
    
    args = parser.parse_args()
    
    # Rulare în bucla asyncio
    asyncio.run(main(args.phone, args.test))