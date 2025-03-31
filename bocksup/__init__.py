"""
Bocksup - Bibliotecă Python pentru integrare WhatsApp

Această bibliotecă oferă o interfață simplă pentru integrarea cu WhatsApp,
permițând autentificarea, trimiterea și primirea de mesaje, și gestionarea
media prin protocoalele WhatsApp Web.

Inspirată din yowsup, dar rescrisă pentru compatibilitate cu versiunile 
moderne ale protocolului WhatsApp și Python 3.8+.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional, Union, Callable

# Configurarea logging-ului implicit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Versiunea bibliotecii
__version__ = "0.1.0"
__author__ = "Bocksup Team"

# Importuri pentru expunerea API-ului public
from .messaging.client import MessagingClient
from .auth.authenticator import Authenticator

def create_client(phone_number: str, password: Optional[str] = None) -> MessagingClient:
    """
    Creează un client de mesagerie WhatsApp.
    
    Args:
        phone_number: Numărul de telefon în format internațional (ex: 40712345678)
        password: Parola sau token-ul de autentificare (opțional pentru autentificare cu cod QR)
        
    Returns:
        Instanță de MessagingClient gata pentru conectare
    """
    return MessagingClient(phone_number, password)

async def test_server_connection(phone_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Testează conectivitatea cu serverele WhatsApp.
    
    Acest test verifică dacă biblioteca poate:
    1. Deschide o conexiune WebSocket cu serverele WhatsApp
    2. Efectua un handshake inițial
    3. Primi și procesa un challenge de la server
    4. (Opțional) Solicita un cod de asociere pentru un număr de telefon
    
    Args:
        phone_number: Opțional, număr de telefon pentru testarea codului de asociere
        
    Returns:
        Dict cu rezultatele testelor și mesajele schimbate
    """
    from .layers.network.connection import WhatsAppConnection
    
    results = {
        "connection": False,
        "handshake": False,
        "challenge": False,
        "pairing_code": None,
        "messages": [],
        "errors": []
    }
    
    connection = None
    
    try:
        # Creați o conexiune
        connection_id = "test_connection"
        connection = WhatsAppConnection(connection_id)
        
        # Înregistrați callback pentru challenge
        challenge_received = False
        
        async def on_challenge(challenge_data):
            nonlocal challenge_received
            challenge_received = True
            results["messages"].append({
                "direction": "received",
                "type": "challenge",
                "content": challenge_data
            })
        
        connection.register_challenge_callback(on_challenge)
        
        # Conectați la server
        connect_result = await connection.connect()
        results["connection"] = connect_result
        
        if connect_result:
            # Efectuați handshake
            handshake_result = await connection.send_handshake()
            results["handshake"] = handshake_result
            
            if handshake_result:
                # Așteptați pentru challenge
                await asyncio.sleep(3)
                results["challenge"] = challenge_received
                
                # Solicitați cod de asociere dacă este furnizat un număr de telefon
                if phone_number:
                    try:
                        # Creați un autentificator
                        auth = Authenticator(phone_number)
                        
                        # Folosim conexiunea existentă
                        auth.connection = connection
                        
                        # Solicitați codul de asociere
                        await auth._request_pairing_code()
                        
                        # Verificați dacă am primit un cod
                        if auth.pairing_code:
                            results["pairing_code"] = True
                            results["messages"].append({
                                "direction": "received",
                                "type": "pairing_code",
                                "content": f"Cod de asociere: {auth.pairing_code}"
                            })
                        else:
                            results["pairing_code"] = False
                            results["errors"].append("Nu s-a putut obține un cod de asociere")
                    except Exception as e:
                        results["pairing_code"] = False
                        results["errors"].append(f"Eroare la solicitarea codului de asociere: {str(e)}")
            else:
                results["errors"].append("Handshake eșuat")
        else:
            results["errors"].append("Conexiune eșuată")
            
    except Exception as e:
        results["errors"].append(f"Eroare generală: {str(e)}")
    finally:
        # Închideți conexiunea
        if connection:
            try:
                await connection.disconnect()
            except:
                pass
    
    return results

# Export public API
__all__ = [
    'create_client',
    'test_server_connection',
    'MessagingClient',
    'Authenticator',
    '__version__'
]