#!/usr/bin/env python3
"""
Script pentru testarea conexiunii la serverele WhatsApp.
"""

import asyncio
import logging
from typing import Optional
import sys

# Configurare logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TestConexiune')

try:
    import bocksup
except ImportError as e:
    logger.error(f"Nu s-a putut importa biblioteca bocksup: {e}")
    sys.exit(1)

async def test_conectare(phone_number: Optional[str] = None):
    """
    Testează conexiunea la serverele WhatsApp.
    
    Args:
        phone_number: Opțional, pentru testarea cod asociere
    """
    logger.info("Se testează conexiunea la serverele WhatsApp...")
    try:
        result = await bocksup.test_server_connection(phone_number)
        
        logger.info("Rezultatele testului:")
        logger.info(f"Conexiune stabilită: {'✓' if result.get('connection') else '✗'}")
        logger.info(f"Handshake realizat: {'✓' if result.get('handshake') else '✗'}")
        logger.info(f"Challenge de autentificare primit: {'✓' if result.get('challenge') else '✗'}")
        
        if phone_number:
            logger.info(f"Cod de asociere solicitat: {'✓' if result.get('pairing_code') else '✗'}")
            
        if result.get('errors'):
            logger.error("Erori întâlnite:")
            for error in result.get('errors'):
                logger.error(f"- {error}")
                
        if result.get('messages'):
            logger.info(f"Număr de mesaje schimbate: {len(result.get('messages'))}")
            
        return result
    except Exception as e:
        logger.error(f"Eroare în timpul testării: {e}")
        return {"connection": False, "errors": [str(e)]}

async def main():
    """
    Funcția principală.
    """
    phone = None
    if len(sys.argv) > 1:
        phone = sys.argv[1]
        logger.info(f"Se folosește numărul de telefon: {phone}")
    
    await test_conectare(phone)

if __name__ == "__main__":
    asyncio.run(main())