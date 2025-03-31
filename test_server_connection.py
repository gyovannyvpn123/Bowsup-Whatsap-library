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
import json
import logging
import os
import sys
from typing import Dict, Optional

import bocksup

# Configurarea logging-ului
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('whatsapp_tester')

class WhatsAppServerTester:
    """
    Tester pentru conectarea și comunicarea cu serverele WhatsApp.
    Folosit pentru a capta răspunsurile autentice și a ajusta implementarea.
    """
    
    def __init__(self, phone_number: Optional[str] = None, debug: bool = True):
        """
        Inițializează tester-ul.
        
        Args:
            phone_number: Numărul de telefon pentru testare (opțional)
            debug: Activează logarea detaliată
        """
        self.phone_number = phone_number
        self.debug = debug
        self.connection = None
        self.results = {
            "connection_success": False,
            "handshake_success": False,
            "challenge_received": False,
            "pairing_code_requested": False,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": []
        }
        
        if debug:
            logging.getLogger('bocksup').setLevel(logging.DEBUG)
        
        logger.info("WhatsApp Server Tester inițializat" + 
                   (f" pentru numărul {phone_number}" if phone_number else ""))
    
    async def connect_to_server(self):
        """
        Conectează la serverul WhatsApp și testează comunicarea de bază.
        """
        logger.info("Începerea testelor de conexiune")
        
        try:
            # Testarea conexiunii de bază
            test_results = await bocksup.test_server_connection(self.phone_number)
            
            # Actualizarea rezultatelor
            self.results["connection_success"] = test_results["connection"]
            self.results["handshake_success"] = test_results["handshake"]
            self.results["challenge_received"] = test_results["challenge"]
            self.results["pairing_code_requested"] = test_results["pairing_code"]
            
            if test_results["errors"]:
                self.results["errors"].extend(test_results["errors"])
            
            # Afișarea rezultatelor
            logger.info("Rezultatele testului de conexiune:")
            logger.info(f"- Conexiune: {'SUCCES' if self.results['connection_success'] else 'EȘEC'}")
            logger.info(f"- Handshake: {'SUCCES' if self.results['handshake_success'] else 'EȘEC'}")
            
            if self.phone_number:
                logger.info(f"- Challenge primit: {'DA' if self.results['challenge_received'] else 'NU'}")
                logger.info(f"- Pairing code solicitat: {'DA' if self.results['pairing_code_requested'] else 'NU'}")
            
            if self.results["errors"]:
                logger.warning("Erori întâlnite:")
                for error in self.results["errors"]:
                    logger.warning(f"- {error}")
            
            # Verificare teste suplimentare
            if self.results["connection_success"]:
                logger.info("Executarea testelor suplimentare...")
                await self._test_message_serialization()
            
        except Exception as e:
            logger.error(f"Teste eșuate cu excepție: {e}")
            self.results["errors"].append(f"Excepție generală: {str(e)}")
    
    async def _test_message_serialization(self):
        """
        Testează serializarea diferitelor tipuri de mesaje.
        """
        logger.info("Testarea serializării mesajelor")
        
        try:
            # Crearea unui nou obiect de conexiune pentru testare
            connection = bocksup.WhatsAppConnection()
            
            # Testarea serializării mesajelor diferite (fără a le trimite efectiv)
            messages = [
                # Mesaj de text
                {
                    "id": "test_message_1",
                    "type": "chat",
                    "to": "1234567890@s.whatsapp.net",
                    "content": "Test message",
                    "timestamp": bocksup.timestamp_now()
                },
                
                # Mesaj de prezență
                {
                    "type": "presence",
                    "id": "test_presence_1",
                    "data": {
                        "type": "available",
                        "last_seen": bocksup.timestamp_now()
                    }
                },
                
                # Mesaj de grup
                {
                    "id": "test_group_message_1",
                    "type": "group",
                    "to": "1234567890-1234567@g.us",
                    "content": "Test group message",
                    "timestamp": bocksup.timestamp_now()
                }
            ]
            
            # Serializarea mesajelor
            serialized_messages = []
            for msg in messages:
                try:
                    if isinstance(msg, dict):
                        serialized = json.dumps(msg)
                        serialized_messages.append(serialized)
                        logger.debug(f"Mesaj serializat: {serialized[:100]}...")
                except Exception as e:
                    logger.error(f"Eroare la serializarea mesajului: {e}")
                    self.results["errors"].append(f"Eroare de serializare: {str(e)}")
            
            self.results["messages_sent"] = len(serialized_messages)
            logger.info(f"Serializarea mesajelor testată: {len(serialized_messages)} mesaje procesate")
            
        except Exception as e:
            logger.error(f"Testul de serializare a mesajelor a eșuat: {e}")
            self.results["errors"].append(f"Eroare în testul de serializare: {str(e)}")
    
    def _create_handshake_message(self) -> str:
        """
        Creează mesajul de handshake inițial.
        """
        # Acest mesaj este generat automat de WhatsAppConnection.connect()
        return "[\"admin\",\"init\",[\"2.2408.5\",\"7Odg9GWl5nK7xh3jFhzK\"],[\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36\"],\"<client_id>\",true]"
    
    def _create_pairing_code_request(self) -> str:
        """
        Creează mesajul pentru solicitarea unui pairing code.
        """
        if not self.phone_number:
            return ""
            
        return "[\"admin\",\"request_code\",{\"method\":\"sms\",\"phone\":\"" + self.phone_number + "\",\"device_id\":\"<device_id>\"}]"
    
    def generate_report(self) -> str:
        """
        Generează un raport cu rezultatele testelor pentru ajustarea implementării.
        """
        report = [
            "==== Raport de Testare a Conexiunii WhatsApp ====",
            f"Data: {asyncio.get_event_loop().time()}",
            f"Versiune Bocksup: {bocksup.__version__}",
            "",
            "Rezultate:",
            f"- Conexiune: {'SUCCES' if self.results['connection_success'] else 'EȘEC'}",
            f"- Handshake: {'SUCCES' if self.results['handshake_success'] else 'EȘEC'}"
        ]
        
        if self.phone_number:
            report.extend([
                f"- Challenge primit: {'DA' if self.results['challenge_received'] else 'NU'}",
                f"- Pairing code solicitat: {'DA' if self.results['pairing_code_requested'] else 'NU'}"
            ])
        
        report.extend([
            f"- Mesaje procesate: {self.results['messages_sent']}",
            f"- Mesaje primite: {self.results['messages_received']}",
            "",
            "Erori întâlnite:"
        ])
        
        if self.results["errors"]:
            for error in self.results["errors"]:
                report.append(f"- {error}")
        else:
            report.append("- Nicio eroare raportată")
        
        report.extend([
            "",
            "==== Recomandări pentru Implementare ====",
            "1. Verifică constantele de conexiune și versiunile WhatsApp",
            "2. Ajustează formatele mesajelor pe baza răspunsurilor reale",
            "3. Implementează complet protocolul de criptare Signal",
            "4. Testează și validează procesul de autentificare cu pairing code",
            "",
            "==== Sfârşit Raport ===="
        ])
        
        return "\n".join(report)

async def run_tests(phone_number: Optional[str] = None):
    """
    Rulează toate testele și înregistrează rezultatele.
    
    Args:
        phone_number: Opțional, numărul de telefon pentru testarea pairing code-ului
    """
    tester = WhatsAppServerTester(phone_number)
    
    try:
        await tester.connect_to_server()
        
        # Generează și afișează raportul
        report = tester.generate_report()
        print("\n" + report)
        
        # Salvează raportul într-un fișier
        with open("whatsapp_test_report.txt", "w") as f:
            f.write(report)
        
        logger.info("Raport salvat în 'whatsapp_test_report.txt'")
        
    except Exception as e:
        logger.error(f"Eroare la rularea testelor: {e}")
        raise

if __name__ == "__main__":
    # Verifică argumentele pentru numărul de telefon
    phone_number = None
    if len(sys.argv) > 1:
        phone_number = sys.argv[1]
        
    # Rulează testele
    asyncio.run(run_tests(phone_number))