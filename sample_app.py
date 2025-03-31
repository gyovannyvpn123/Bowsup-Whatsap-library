#!/usr/bin/env python3
"""
Sample application for Bocksup library.

This app demonstrates how to use the main functionality of the Bocksup
library for WhatsApp integration.
"""

import asyncio
import logging
import os
import sys
from typing import Optional

import bocksup

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BocksupDemo")

# WhatsApp credentials
PHONE_NUMBER = os.environ.get("WHATSAPP_PHONE")
PASSWORD = os.environ.get("WHATSAPP_PASSWORD")


async def test_connection(phone_number: Optional[str] = None):
    """
    Test connection to WhatsApp servers.
    
    Args:
        phone_number: Optional phone number to test pairing code functionality
    """
    logger.info("Testing connection to WhatsApp servers...")
    result = await bocksup.test_server_connection(phone_number)
    
    logger.info(f"Connection test results:")
    logger.info(f"Connection established: {'✓' if result.get('connection') else '✗'}")
    logger.info(f"Handshake completed: {'✓' if result.get('handshake') else '✗'}")
    logger.info(f"Authentication challenge received: {'✓' if result.get('challenge') else '✗'}")
    
    if phone_number:
        logger.info(f"Pairing code requested: {'✓' if result.get('pairing_code') else '✗'}")
        
    if result.get('errors'):
        logger.error("Errors encountered:")
        for error in result['errors']:
            logger.error(f"- {error}")
            
    return result


async def create_and_test_client(phone_number: str, password: Optional[str] = None):
    """
    Create a WhatsApp client and test basic functionality.
    
    Args:
        phone_number: Phone number in international format
        password: Optional password or authentication token
    """
    logger.info(f"Creating WhatsApp client for {phone_number}...")
    
    try:
        client = bocksup.create_client(phone_number, password)
        
        # În versiunea actuală, client poate fi un dicționar sau un obiect MessagingClient
        if isinstance(client, dict):
            logger.info(f"Client creat cu următoarele componente:")
            for k, v in client.items():
                logger.info(f"- {k}: {v}")
        else:
            # Presupunem că este un obiect MessagingClient
            logger.info(f"Client creat: {client}")
            logger.info(f"Se încearcă conectarea...")
            
            # Încercăm o conectare simplă pentru a testa funcționalitatea
            try:
                connected = await client.connect()
                logger.info(f"Conectat: {'✓' if connected else '✗'}")
                
                if connected:
                    # Dacă suntem conectați, încearcă o operațiune simplă
                    logger.info("Se așteaptă câteva secunde pentru a primi notificări...")
                    await asyncio.sleep(5)
                    
                    # Deconectare
                    logger.info("Deconectare...")
                    await client.disconnect()
                
            except Exception as e:
                logger.error(f"Eroare la conectare: {e}")
        
        # In a complete implementation, we would connect and interact with WhatsApp here
        return client
    except Exception as e:
        logger.error(f"Eroare la crearea clientului: {e}")
        return None


async def main():
    """Main application function."""
    logger.info(f"Bocksup library version: {bocksup.__version__}")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = "info"
    
    if command == "info":
        logger.info("Informații despre biblioteca Bocksup:")
        logger.info(f"- Versiune: {bocksup.__version__ if hasattr(bocksup, '__version__') else 'necunoscută'}")
        
        # Liste modulele disponibile
        modules = [m for m in dir(bocksup) if not m.startswith('__')]
        logger.info(f"- Module disponibile: {', '.join(modules)}")
        
        # Verifică funcționalitățile cheie
        logger.info("Funcționalități cheie:")
        logger.info(f"- Autentificare: {'✓' if hasattr(bocksup, 'auth') else '✗'}")
        logger.info(f"- Mesagerie: {'✓' if hasattr(bocksup, 'messaging') else '✗'}")
        logger.info(f"- Criptare: {'✓' if hasattr(bocksup, 'encryption') else '✗'}")
        logger.info(f"- Grupuri: {'✓' if hasattr(bocksup, 'groups') else '✗'}")
        logger.info(f"- Media: {'✓' if hasattr(bocksup, 'media') else '✗'}")
        logger.info(f"- Înregistrare: {'✓' if hasattr(bocksup, 'registration') else '✗'}")
        
        # Informații despre versiunea protocol
        try:
            protocol_version = bocksup.PROTOCOL_VERSION if hasattr(bocksup, 'PROTOCOL_VERSION') else "0.4 (implicit)" 
            logger.info(f"- Versiune protocol WhatsApp: {protocol_version}")
        except:
            logger.info("- Versiune protocol WhatsApp: necunoscută")
        
    elif command == "test":
        phone_number = sys.argv[2] if len(sys.argv) > 2 else PHONE_NUMBER
        if not phone_number:
            logger.error("No phone number provided for testing.")
            logger.error("Use: python sample_app.py test +1234567890")
            return
            
        await test_connection(phone_number)
        
    elif command == "client":
        phone_number = sys.argv[2] if len(sys.argv) > 2 else PHONE_NUMBER
        password = sys.argv[3] if len(sys.argv) > 3 else PASSWORD
        
        if not phone_number:
            logger.error("No phone number provided for client creation.")
            logger.error("Use: python sample_app.py client +1234567890 [password]")
            return
            
        await create_and_test_client(phone_number, password)
        
    else:
        logger.error(f"Unknown command: {command}")
        logger.error("Available commands: info, test, client")
    
    
if __name__ == "__main__":
    asyncio.run(main())