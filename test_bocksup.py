#!/usr/bin/env python3
"""
Script pentru testarea bibliotecii Bocksup.
Acest script verifică conexiunea cu serverele WhatsApp și funcționalitatea de bază.
"""

import asyncio
import logging
import bocksup

# Setarea nivelului de logging pentru a vedea detalii ale procesului
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BocksupTest")

async def test_server_connection():
    """Testează conexiunea cu serverele WhatsApp."""
    logger.info("Test de conexiune cu serverele WhatsApp...")
    
    # Apelăm funcția de test a conexiunii
    result = await bocksup.test_server_connection()
    
    logger.info(f"Rezultat: {result}")
    
    # Verificăm dacă conexiunea a reușit
    if result.get('connection', False):
        logger.info("✅ Conexiune reușită!")
    else:
        logger.error("❌ Conexiune eșuată!")
        
    # Verificăm handshake-ul
    if result.get('handshake', False):
        logger.info("✅ Handshake reușit!")
    else:
        logger.error("❌ Handshake eșuat!")
    
    return result

async def test_phone_connection(phone_number):
    """Testează solicitarea unui cod de asociere pentru un număr de telefon dat."""
    logger.info(f"Test solicitare cod de asociere pentru numărul {phone_number}...")
    
    # Apelăm funcția de test cu numărul de telefon
    result = await bocksup.test_server_connection(phone_number)
    
    logger.info(f"Rezultat: {result}")
    
    # Verificăm dacă a fost solicitat un cod de asociere
    if result.get('pairing_code', False):
        logger.info("✅ Solicitare cod de asociere reușită!")
    else:
        logger.error("❌ Solicitare cod de asociere eșuată!")
    
    return result

async def main():
    """Funcția principală care execută testele."""
    logger.info("Începere teste Bocksup...")
    
    # Test de conexiune de bază
    connection_result = await test_server_connection()
    
    # Opțional: test cu un număr de telefon real
    # Decomentați liniile următoare și înlocuiți cu un număr real
    # pentru a testa solicitarea unui cod de asociere
    
    # phone_number = "40712345678"  # Înlocuiți cu numărul dvs. real
    # phone_result = await test_phone_connection(phone_number)
    
    logger.info("Teste Bocksup finalizate!")

if __name__ == "__main__":
    asyncio.run(main())