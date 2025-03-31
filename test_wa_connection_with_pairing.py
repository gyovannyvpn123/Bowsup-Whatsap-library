#!/usr/bin/env python3
"""
Script pentru testarea conexiunii WhatsApp și solicitarea unui cod de asociere.
"""

import asyncio
import logging
import json
import os
import random
import time
import websockets
import uuid

# Configurare logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WAConnection")

# Constants
WA_WEB_URL = "wss://web.whatsapp.com/ws/chat"
VERSION = "2.2348.50"
BROWSER_DETAILS = ["Bocksup", "Chrome", "10.0"]
CLIENT_TOKEN = f"bocksup_test_{int(time.time())}"
CLIENT_ID = f"bocksup_test:{str(uuid.uuid4())[:8]}"

# Numărul de telefon pentru care solicităm codul de asociere
# Formatat fără + sau alte caractere speciale
PHONE_NUMBER = "40748427351"

async def connect_to_whatsapp():
    """Conectare la serverele WhatsApp și solicitare cod de asociere."""
    logger.info(f"Conectare la {WA_WEB_URL}...")
    
    try:
        # Conectare WebSocket cu subprotocol
        async with websockets.connect(
            WA_WEB_URL, 
            subprotocols=["chat"]
        ) as websocket:
            logger.info("Conexiune WebSocket stabilită!")
            
            # Trimitere mesaj de handshake (binary encoded JSON)
            handshake_msg = {
                "clientToken": CLIENT_TOKEN,
                "serverToken": None,
                "clientId": CLIENT_ID,
                "tag": f"{int(time.time())}.--0",
                "type": "connect",
                "protocolVersion": "0.4",
                "connectType": "PHONE_CONNECTING",
                "connectReason": "USER_ACTIVATED", 
                "features": {
                    "supportsMultiDevice": True,
                    "supportsE2EEncryption": True,
                    "supportsQRLinking": True
                }
            }
            
            # Convertire mesaj la JSON pentru trimitere
            json_msg = json.dumps(handshake_msg)
            logger.info(f"Trimitere handshake: {json_msg}")
            await websocket.send(json_msg)
            
            # Așteaptă și procesează răspunsul la handshake
            handshake_response = await websocket.recv()
            
            # Determină tipul răspunsului (binar sau text)
            if isinstance(handshake_response, bytes):
                try:
                    decoded = handshake_response.decode('latin-1')
                    logger.info(f"Răspuns binar primit: {decoded[:30]}... ({len(handshake_response)} bytes)")
                except:
                    logger.info(f"Răspuns binar primit: {len(handshake_response)} bytes")
            else:
                logger.info(f"Răspuns text primit: {handshake_response}")
            
            logger.info("Handshake complet. Presupun handshake reușit.")
            
            # Pauză scurtă
            await asyncio.sleep(1)
            
            # Trimitere cerere pentru cod de asociere
            pairing_request = {
                "tag": f"{int(time.time())}.--1",
                "type": "request_pairing_code",
                "phoneNumber": PHONE_NUMBER,
                "isPrimaryDevice": True,
                "method": "sms"  # Poate fi "voice" sau "sms"
            }
            
            # Trimitem cererea pentru codul de asociere ca text
            json_pairing = json.dumps(pairing_request)
            logger.info(f"Trimitere cerere cod de asociere: {json_pairing}")
            await websocket.send(json_pairing)
            
            # Așteptăm răspunsul cu codul de asociere
            pairing_responses = []
            try:
                # Așteptăm până la 5 secunde pentru răspunsuri multiple
                start_time = time.time()
                while time.time() - start_time < 5:
                    try:
                        pairing_response = await asyncio.wait_for(websocket.recv(), timeout=1)
                        pairing_responses.append(pairing_response)
                        
                        # Procesăm răspunsul
                        if isinstance(pairing_response, bytes):
                            try:
                                # Încercăm diverse codificări
                                for encoding in ['utf-8', 'latin-1']:
                                    try:
                                        decoded = pairing_response.decode(encoding)
                                        logger.info(f"Răspuns decodificat ({encoding}): {decoded[:50]}...")
                                        
                                        # Verificăm dacă este JSON
                                        if decoded.startswith('{'):
                                            try:
                                                json_data = json.loads(decoded)
                                                logger.info(f"JSON valid: {json_data}")
                                                
                                                # Verificăm pentru codul de asociere
                                                if "pairingCode" in json_data:
                                                    logger.info(f"COD DE ASOCIERE GĂSIT: {json_data['pairingCode']}")
                                                    logger.info("=================================================")
                                                    logger.info(f"FOLOSIȚI CODUL: {json_data['pairingCode']}")
                                                    logger.info("=================================================")
                                            except:
                                                pass
                                        break
                                    except:
                                        continue
                            except:
                                logger.info(f"Răspuns binar brut: {pairing_response[:20]}... ({len(pairing_response)} bytes)")
                        else:
                            logger.info(f"Răspuns text: {pairing_response}")
                            
                            # Verificăm dacă este JSON
                            try:
                                json_data = json.loads(pairing_response)
                                logger.info(f"JSON valid: {json_data}")
                                
                                # Verificăm pentru codul de asociere
                                if "pairingCode" in json_data:
                                    logger.info(f"COD DE ASOCIERE GĂSIT: {json_data['pairingCode']}")
                                    logger.info("=================================================")
                                    logger.info(f"FOLOSIȚI CODUL: {json_data['pairingCode']}")
                                    logger.info("=================================================")
                            except:
                                pass
                    except asyncio.TimeoutError:
                        # Timeout pentru un singur recv, dar continuăm bucla
                        continue
            except Exception as e:
                logger.error(f"Eroare la primirea codului de asociere: {e}")
            
            logger.info(f"Total răspunsuri primite: {len(pairing_responses)}")
            
            if not pairing_responses:
                logger.warning("Nu s-a primit niciun răspuns pentru codul de asociere")
                logger.info("Verificați telefonul pentru a vedea dacă a apărut codul de asociere")
            
            # Încheiem sesiunea
            try:
                disconnect_msg = {
                    "tag": f"{int(time.time())}.--2",
                    "type": "disconnect",
                    "reason": "USER_INITIATED"
                }
                json_disconnect = json.dumps(disconnect_msg)
                await websocket.send(json_disconnect)
                logger.info("Deconectare trimisă")
            except:
                logger.warning("Nu s-a putut trimite mesajul de deconectare")
                
    except Exception as e:
        logger.error(f"Eroare la conectare: {e}")
        return False
    
    return True

async def main():
    """Funcția principală."""
    logger.info("Începere test WhatsApp cu solicitare cod de asociere...")
    
    # Conectare și solicitare cod
    success = await connect_to_whatsapp()
    
    if success:
        logger.info("Test finalizat cu succes!")
        logger.info("Dacă un cod de asociere a fost generat, verificați informațiile de mai sus.")
    else:
        logger.error("Testul a eșuat!")
    
if __name__ == "__main__":
    asyncio.run(main())