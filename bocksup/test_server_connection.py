"""
Script pentru testarea și depanarea conexiunii cu serverele WhatsApp.

Acest modul este folosit pentru a:
1. Testa conectarea la serverele WhatsApp reale
2. Capta și analiza răspunsurile pentru a îmbunătăți implementarea
3. Ajusta implementarea în funcție de comportamentul real al serverelor
4. Depana și diagnostica probleme de comunicare

Folosește-l pentru a face biblioteca pe deplin funcțională cu serverele WhatsApp.
"""

import asyncio
import logging
import json
import base64
import os
import sys
import time
import websockets
from typing import Dict, Any, Optional

# Configurarea logging-ului
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('whatsapp_server_test.log')
    ]
)

logger = logging.getLogger(__name__)

# Constante server
WHATSAPP_WEBSOCKET_URL = 'wss://web.whatsapp.com/ws/chat'
USER_AGENT = 'WhatsApp/2.2412.54 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'

class WhatsAppServerTester:
    """
    Tester pentru conectarea și comunicarea cu serverele WhatsApp.
    Folosit pentru a capta răspunsurile autentice și a ajusta implementarea.
    """
    
    def __init__(self, phone_number: Optional[str] = None, debug: bool = True):
        self.session_id = f"test_session_{int(time.time())}"
        self.client_id = f"bocksup_test_{int(time.time())}"
        self.phone_number = phone_number
        self.debug = debug
        self.message_counter = 0
        self.websocket = None
        self.challenge_data = None
        self.pairing_code = None
        self.test_results = []
        
    async def connect_to_server(self):
        """
        Conectează la serverul WhatsApp și testează comunicarea de bază.
        """
        logger.info("Începerea testului de conectare la serverul WhatsApp")
        
        # Pregătește headerele WebSocket
        headers = {
            'User-Agent': USER_AGENT,
            'Origin': 'https://web.whatsapp.com',
            'Sec-WebSocket-Protocol': 'chat',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        try:
            # Deschide conexiunea WebSocket
            logger.info(f"Conectare la: {WHATSAPP_WEBSOCKET_URL}")
            self.websocket = await websockets.connect(
                WHATSAPP_WEBSOCKET_URL,
                extra_headers=headers,
                ping_interval=None,
                max_size=None
            )
            
            # Trimite mesajul de handshake
            handshake = self._create_handshake_message()
            logger.debug(f"Trimitere handshake: {handshake}")
            await self.websocket.send(handshake)
            
            # Așteaptă și procesează răspunsul
            response = await self.websocket.recv()
            if self.debug:
                logger.debug(f"Răspuns primit: {response[:200]}...")
                
            # Procesează răspunsul pentru a înțelege ce așteaptă serverul
            await self._process_server_response(response)
            
            # Testează solicitarea unui pairing code dacă există un număr de telefon
            if self.phone_number:
                await self._test_pairing_code_request()
            
            # Continuă testarea diverselor tipuri de mesaje și răspunsuri
            await self._test_message_serialization()
            
            logger.info("Testarea conexiunii completă")
            return True
            
        except Exception as e:
            logger.error(f"Eroare în timpul testului de conexiune: {str(e)}")
            self.test_results.append({
                "test": "connect_to_server",
                "success": False,
                "error": str(e)
            })
            return False
        finally:
            # Închide conexiunea
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
                
    async def _process_server_response(self, response):
        """
        Procesează răspunsul serverului pentru a determina pasul următor.
        """
        try:
            # Încearcă să parseze răspunsul ca JSON
            if isinstance(response, str):
                parsed = json.loads(response)
                
                # Verifică tipul mesajului
                if "type" in parsed:
                    message_type = parsed["type"]
                    
                    if message_type == "challenge":
                        logger.info("Primit challenge de autentificare")
                        self.challenge_data = parsed.get("data", {})
                        self.test_results.append({
                            "test": "receive_challenge",
                            "success": True,
                            "challenge_type": self.challenge_data.get("type", "unknown")
                        })
                        
                    elif message_type == "connected":
                        logger.info("Conexiune confirmată de server")
                        self.test_results.append({
                            "test": "connection_confirmed",
                            "success": True
                        })
                        
                    elif message_type == "error":
                        logger.warning(f"Eroare de la server: {parsed.get('error', {})}")
                        self.test_results.append({
                            "test": "server_error",
                            "success": False,
                            "error_code": parsed.get("error", {}).get("code", 0),
                            "error_message": parsed.get("error", {}).get("message", "Eroare necunoscută")
                        })
                    else:
                        logger.info(f"Mesaj de tip necunoscut: {message_type}")
                        self.test_results.append({
                            "test": "unknown_message_type",
                            "message_type": message_type,
                            "success": True
                        })
                else:
                    logger.warning("Răspunsul nu conține un câmp 'type'")
            else:
                logger.warning(f"Răspuns binar sau neașteptat: {type(response)}")
                
        except json.JSONDecodeError:
            logger.warning("Răspunsul nu este un JSON valid")
            # Ar putea fi un mesaj binar sau altă codificare
            self.test_results.append({
                "test": "parse_response",
                "success": False,
                "error": "Nu s-a putut parsa răspunsul ca JSON"
            })
            
    async def _test_pairing_code_request(self):
        """
        Testează solicitarea unui pairing code.
        """
        if not self.websocket or not self.phone_number:
            return
            
        try:
            logger.info(f"Testarea solicitării de pairing code pentru: {self.phone_number}")
            
            # Creează mesajul de solicitare a pairing code-ului
            pairing_request = self._create_pairing_code_request()
            
            # Trimite solicitarea
            await self.websocket.send(pairing_request)
            
            # Așteaptă răspunsul
            response = await self.websocket.recv()
            if self.debug:
                logger.debug(f"Răspuns pairing code: {response[:200]}...")
                
            # Procesează răspunsul
            try:
                if isinstance(response, str):
                    parsed = json.loads(response)
                    
                    # Verifică dacă răspunsul conține un pairing code
                    if "data" in parsed and "pairingCode" in parsed["data"]:
                        self.pairing_code = parsed["data"]["pairingCode"]
                        logger.info(f"Pairing code primit: {self.pairing_code}")
                        
                        self.test_results.append({
                            "test": "pairing_code_request",
                            "success": True,
                            "pairing_code": self.pairing_code
                        })
                    else:
                        logger.warning("Răspunsul nu conține un pairing code")
                        
                        # Verifică dacă există un mesaj de eroare
                        if "error" in parsed:
                            logger.error(f"Eroare la solicitarea pairing code: {parsed.get('error')}")
                            
                        self.test_results.append({
                            "test": "pairing_code_request",
                            "success": False,
                            "error": "Nu s-a primit pairing code"
                        })
            except json.JSONDecodeError:
                logger.warning("Răspunsul pentru pairing code nu este un JSON valid")
                self.test_results.append({
                    "test": "pairing_code_request",
                    "success": False,
                    "error": "Răspuns invalid la solicitarea de pairing code"
                })
                
        except Exception as e:
            logger.error(f"Eroare în timpul testului de pairing code: {str(e)}")
            self.test_results.append({
                "test": "pairing_code_request",
                "success": False,
                "error": str(e)
            })
            
    async def _test_message_serialization(self):
        """
        Testează serializarea diferitelor tipuri de mesaje.
        """
        # Testul este încă în conexiune cu serverul WhatsApp
        if not self.websocket:
            return
            
        try:
            logger.info("Testarea serializării mesajelor")
            
            # Mesaje de test pentru serializare
            test_messages = [
                {
                    "type": "ping",
                    "tag": f"ping_{int(time.time())}",
                    "timestamp": int(time.time())
                },
                {
                    "type": "presence",
                    "tag": f"presence_{int(time.time())}",
                    "status": "available",
                    "timestamp": int(time.time())
                }
            ]
            
            # Serializează și trimite mesaje de test (doar dacă suntem conectați)
            for msg in test_messages:
                serialized = json.dumps(msg)
                logger.debug(f"Mesaj serializat pentru testare: {serialized}")
                
                # Nu trimite efectiv mesajele, doar înregistrează serializarea
                # await self.websocket.send(serialized)
                
                self.test_results.append({
                    "test": "message_serialization",
                    "message_type": msg["type"],
                    "success": True
                })
                
        except Exception as e:
            logger.error(f"Eroare în timpul testului de serializare a mesajelor: {str(e)}")
            self.test_results.append({
                "test": "message_serialization",
                "success": False,
                "error": str(e)
            })
            
    def _create_handshake_message(self) -> str:
        """
        Creează mesajul de handshake inițial.
        """
        message_tag = f"{int(time.time())}.--{self.message_counter}"
        self.message_counter += 1
        
        handshake = {
            "clientToken": self.client_id,
            "serverToken": None,
            "clientId": f"bocksup_test:{self.session_id}",
            "tag": message_tag,
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
        
        return json.dumps(handshake)
        
    def _create_pairing_code_request(self) -> str:
        """
        Creează mesajul pentru solicitarea unui pairing code.
        """
        message_tag = f"{int(time.time())}.--{self.message_counter}"
        self.message_counter += 1
        
        request = {
            "tag": message_tag,
            "type": "request",
            "method": "requestPairingCode",
            "params": {
                "phoneNumber": self.phone_number,
                "requestMeta": {
                    "platform": "python",
                    "deviceId": self.client_id,
                    "sessionId": self.session_id
                }
            }
        }
        
        return json.dumps(request)
        
    def generate_report(self) -> str:
        """
        Generează un raport cu rezultatele testelor pentru ajustarea implementării.
        """
        report = "===== RAPORT DE TESTARE A SERVERELOR WHATSAPP =====\n\n"
        
        for i, result in enumerate(self.test_results, 1):
            report += f"Test #{i}: {result.get('test', 'necunoscut')}\n"
            report += f"Succes: {'Da' if result.get('success', False) else 'Nu'}\n"
            
            # Adaugă detalii specifice în funcție de tipul testului
            if 'error' in result:
                report += f"Eroare: {result['error']}\n"
                
            if 'challenge_type' in result:
                report += f"Tip challenge: {result['challenge_type']}\n"
                
            if 'pairing_code' in result:
                report += f"Pairing code: {result['pairing_code']}\n"
                
            if 'message_type' in result:
                report += f"Tip mesaj: {result['message_type']}\n"
                
            report += "\n"
            
        report += "Recomandări pentru implementare:\n"
        
        # Analizează rezultatele pentru a genera recomandări
        has_challenge = any(r.get('test') == 'receive_challenge' and r.get('success', False) for r in self.test_results)
        has_pairing_code = any(r.get('test') == 'pairing_code_request' and r.get('success', False) for r in self.test_results)
        
        if has_challenge:
            report += "- Implementează gestionarea corectă a challenge-urilor de autentificare\n"
            
        if has_pairing_code:
            report += "- Utilizează pairing code-ul primit pentru autentificare\n"
        else:
            report += "- Implementează gestionarea erorilor pentru solicitarea pairing code-ului\n"
            
        report += "- Actualizează constantele și headerele pentru a corespunde cerințelor serverului\n"
        report += "- Implementează mecanismul de criptare Signal pentru mesaje\n"
        
        return report


async def run_tests(phone_number: Optional[str] = None):
    """
    Rulează toate testele și înregistrează rezultatele.
    
    Args:
        phone_number: Opțional, numărul de telefon pentru testarea pairing code-ului
    """
    logger.info("Începerea testelor de conexiune cu serverele WhatsApp")
    
    tester = WhatsAppServerTester(phone_number)
    
    try:
        await tester.connect_to_server()
        
        # Generează și salvează raportul
        report = tester.generate_report()
        
        with open("whatsapp_test_report.txt", "w") as f:
            f.write(report)
            
        print("\n" + report)
        
        logger.info("Teste complete. Raportul a fost salvat în whatsapp_test_report.txt")
        
    except Exception as e:
        logger.error(f"Eroare în timpul testelor: {str(e)}")


if __name__ == "__main__":
    # Verifică parametrii de linie de comandă
    phone_number = None
    if len(sys.argv) > 1:
        phone_number = sys.argv[1]
        
    # Rulează toate testele
    asyncio.run(run_tests(phone_number))