#!/usr/bin/env python3
"""
Script pentru analiza traficului WhatsApp Web.

Acest script analizează capturi de trafic WhatsApp Web pentru a extrage informații
despre formatul mesajelor și a identifica modificările din protocol. Captura poate fi
realizată cu instrumente precum Chrome DevTools, Wireshark sau mitmproxy.
"""

import json
import os
import argparse
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

# Configurarea logging-ului
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('protocol_analyzer')

class ProtocolAnalyzer:
    """
    Analizor pentru traficul WhatsApp Web.
    
    Această clasă procesează capturi de trafic pentru a extrage și analiza
    formatul mesajelor WhatsApp.
    """
    
    def __init__(self, data_dir: str = "protocol_data"):
        """
        Inițializează analizorul.
        
        Args:
            data_dir: Directorul pentru stocarea informațiilor analizate
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.message_types = {}
        self.protocol_info = {
            "client_versions": set(),
            "message_types": set(),
            "endpoints": set(),
            "handshake_formats": [],
            "authentication_methods": set(),
            "known_headers": {}
        }
        
    def analyze_json_file(self, filepath: str) -> None:
        """
        Analizează un fișier JSON care conține capturi de trafic.
        
        Args:
            filepath: Calea către fișierul JSON
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.info(f"Analizare fișier: {filepath}")
            
            # Determinarea tipului de fișier
            if isinstance(data, list):
                # Probabil captură din Chrome DevTools
                self._analyze_chrome_capture(data)
            elif isinstance(data, dict):
                # Verificăm dacă este un singur mesaj sau o structură specifică
                if "type" in data or "tag" in data:
                    # Este un singur mesaj WhatsApp
                    self._analyze_whatsapp_message(data)
                elif "log" in data or "entries" in data:
                    # Probabil captură HAR
                    self._analyze_har_file(data)
                else:
                    # Structură JSON necunoscută
                    logger.warning(f"Format JSON necunoscut în {filepath}")
                    self._analyze_generic_json(data)
            else:
                logger.warning(f"Format JSON neașteptat în {filepath}")
                
            # Salvarea informațiilor actualizate
            self._save_protocol_info()
            
        except json.JSONDecodeError:
            logger.error(f"Fișierul {filepath} nu este un JSON valid.")
        except Exception as e:
            logger.error(f"Eroare la analiza fișierului {filepath}: {e}")
    
    def analyze_text_file(self, filepath: str) -> None:
        """
        Analizează un fișier text care conține mesaje WebSocket.
        
        Args:
            filepath: Calea către fișierul text
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            logger.info(f"Analizare fișier text: {filepath}")
            
            # Căutarea mesajelor WebSocket în format "tag,json"
            websocket_pattern = r'([0-9]+\.--[0-9]+|[0-9]+),(\{.*\}|\[.*\])'
            matches = re.findall(websocket_pattern, content)
            
            if matches:
                logger.info(f"S-au găsit {len(matches)} posibile mesaje WebSocket")
                for tag, message_str in matches:
                    try:
                        message = json.loads(message_str)
                        logger.info(f"Mesaj valid găsit cu tag: {tag}")
                        self._analyze_whatsapp_message(message, tag)
                    except json.JSONDecodeError:
                        logger.debug(f"Fragment invalid JSON: {message_str[:50]}...")
            else:
                # Încercăm să găsim JSON-uri independente în text
                self._extract_json_from_text(content)
                
            # Salvarea informațiilor actualizate
            self._save_protocol_info()
            
        except Exception as e:
            logger.error(f"Eroare la analiza fișierului text {filepath}: {e}")
    
    def analyze_directory(self, dirpath: str) -> None:
        """
        Analizează toate fișierele relevante dintr-un director.
        
        Args:
            dirpath: Calea către director
        """
        try:
            dirpath = Path(dirpath)
            if not dirpath.is_dir():
                logger.error(f"{dirpath} nu este un director valid.")
                return
                
            logger.info(f"Analizare director: {dirpath}")
            
            # Procesarea fișierelor JSON
            for json_file in dirpath.glob("*.json"):
                self.analyze_json_file(str(json_file))
                
            # Procesarea fișierelor text
            for text_file in dirpath.glob("*.txt"):
                self.analyze_text_file(str(text_file))
                
            # Procesarea altor tipuri de fișiere
            for har_file in dirpath.glob("*.har"):
                self.analyze_json_file(str(har_file))
                
            logger.info(f"Analiză completă pentru directorul {dirpath}")
            
        except Exception as e:
            logger.error(f"Eroare la analiza directorului {dirpath}: {e}")
    
    def generate_report(self) -> str:
        """
        Generează un raport cu informațiile analizate.
        
        Returns:
            Raportul în format text
        """
        report = []
        report.append("=== RAPORT ANALIZĂ PROTOCOL WHATSAPP ===")
        report.append("")
        
        # Versiuni client
        report.append(f"Versiuni client detectate: {len(self.protocol_info['client_versions'])}")
        for version in sorted(self.protocol_info['client_versions']):
            report.append(f"  - {version}")
        report.append("")
        
        # Tipuri de mesaje
        report.append(f"Tipuri de mesaje detectate: {len(self.protocol_info['message_types'])}")
        for msg_type in sorted(self.protocol_info['message_types']):
            report.append(f"  - {msg_type}")
        report.append("")
        
        # Formate handshake
        report.append(f"Formate handshake detectate: {len(self.protocol_info['handshake_formats'])}")
        for i, handshake in enumerate(self.protocol_info['handshake_formats']):
            report.append(f"  Format {i+1}:")
            report.append(f"    {json.dumps(handshake, indent=2)}")
        report.append("")
        
        # Metode de autentificare
        report.append(f"Metode de autentificare detectate: {len(self.protocol_info['authentication_methods'])}")
        for method in sorted(self.protocol_info['authentication_methods']):
            report.append(f"  - {method}")
        report.append("")
        
        # Detalii despre mesaje
        if self.message_types:
            report.append("Structura mesajelor detectate:")
            for msg_type, details in sorted(self.message_types.items()):
                report.append(f"  {msg_type}:")
                if 'fields' in details:
                    report.append("    Câmpuri:")
                    for field, occurrences in sorted(details['fields'].items(), key=lambda x: x[1], reverse=True):
                        report.append(f"      - {field}: {occurrences} apariții")
                report.append("")
        
        # Concluzii și recomandări
        report.append("=== RECOMANDĂRI PENTRU IMPLEMENTARE ===")
        report.append("1. Versiunea client recomandată: " + 
                     (max(self.protocol_info['client_versions']) if self.protocol_info['client_versions'] else "N/A"))
        
        # Alte recomandări specifice
        for aspect, details in self._generate_recommendations().items():
            report.append(f"{aspect}:")
            for rec in details:
                report.append(f"  - {rec}")
        
        return "\n".join(report)
    
    def _analyze_chrome_capture(self, data: List[Dict[str, Any]]) -> None:
        """
        Analizează o captură din Chrome DevTools.
        
        Args:
            data: Lista de mesaje capturate
        """
        websocket_messages = []
        
        for entry in data:
            if isinstance(entry, dict):
                # Căutăm mesaje WebSocket
                if entry.get('method') == 'Network.webSocketFrameSent':
                    try:
                        payload = entry.get('params', {}).get('response', {}).get('payloadData')
                        if payload:
                            websocket_messages.append(('sent', payload))
                    except (KeyError, AttributeError):
                        pass
                        
                elif entry.get('method') == 'Network.webSocketFrameReceived':
                    try:
                        payload = entry.get('params', {}).get('response', {}).get('payloadData')
                        if payload:
                            websocket_messages.append(('received', payload))
                    except (KeyError, AttributeError):
                        pass
                        
                # Căutăm informații despre cereri HTTP
                elif entry.get('method') == 'Network.requestWillBeSent':
                    try:
                        request = entry.get('params', {}).get('request', {})
                        url = request.get('url', '')
                        if 'whatsapp' in url.lower():
                            self.protocol_info['endpoints'].add(url)
                            
                            # Extragem headerele
                            headers = request.get('headers', {})
                            for header, value in headers.items():
                                if header not in self.protocol_info['known_headers']:
                                    self.protocol_info['known_headers'][header] = set()
                                self.protocol_info['known_headers'][header].add(value)
                    except (KeyError, AttributeError):
                        pass
        
        # Procesarea mesajelor WebSocket
        for direction, payload in websocket_messages:
            try:
                # Încercăm mai întâi să extragem tag-ul și JSON-ul
                match = re.match(r'^([^,]+),(.+)$', payload)
                if match:
                    tag, json_str = match.groups()
                    try:
                        message = json.loads(json_str)
                        self._analyze_whatsapp_message(message, tag)
                        
                        # Detectare handshake
                        if direction == 'sent' and isinstance(message, list) and len(message) >= 2:
                            if message[0] == 'admin' and message[1] == 'init':
                                # Acesta este un mesaj de handshake
                                self.protocol_info['handshake_formats'].append(message)
                                
                                # Extragem versiunea clientului
                                if len(message) > 2 and isinstance(message[2], list) and len(message[2]) >= 1:
                                    self.protocol_info['client_versions'].add(message[2][0])
                    except json.JSONDecodeError:
                        # Nu este JSON valid, încercăm să extragem informații direct din text
                        if 'pairingCode' in payload:
                            self.protocol_info['authentication_methods'].add('pairing_code')
                        elif 'QR' in payload or 'qrcode' in payload.lower():
                            self.protocol_info['authentication_methods'].add('qr_code')
            except Exception as e:
                logger.debug(f"Eroare la procesarea mesajului WebSocket: {e}")
    
    def _analyze_har_file(self, data: Dict[str, Any]) -> None:
        """
        Analizează un fișier HAR (HTTP Archive).
        
        Args:
            data: Datele HAR
        """
        try:
            entries = data.get('log', {}).get('entries', [])
            
            for entry in entries:
                request = entry.get('request', {})
                response = entry.get('response', {})
                
                # Verificăm dacă este o cerere relevantă pentru WhatsApp
                url = request.get('url', '')
                if 'whatsapp' in url.lower() or 'wa.me' in url.lower():
                    self.protocol_info['endpoints'].add(url)
                    
                    # Extragem headerele
                    headers = request.get('headers', [])
                    for header in headers:
                        name = header.get('name', '')
                        value = header.get('value', '')
                        if name and name not in self.protocol_info['known_headers']:
                            self.protocol_info['known_headers'][name] = set()
                        if name and value:
                            self.protocol_info['known_headers'][name].add(value)
                    
                    # Analizăm datele de cerere
                    post_data = request.get('postData', {})
                    if post_data:
                        text = post_data.get('text', '')
                        if text:
                            self._extract_json_from_text(text)
                    
                    # Analizăm datele de răspuns
                    content = response.get('content', {})
                    if content:
                        text = content.get('text', '')
                        if text:
                            self._extract_json_from_text(text)
            
        except Exception as e:
            logger.error(f"Eroare la analiza fișierului HAR: {e}")
    
    def _analyze_whatsapp_message(self, message: Union[Dict[str, Any], List[Any]], tag: Optional[str] = None) -> None:
        """
        Analizează un mesaj WhatsApp.
        
        Args:
            message: Datele mesajului
            tag: Tag-ul mesajului (opțional)
        """
        if isinstance(message, dict):
            # Extragem tipul mesajului
            message_type = message.get('type', 'unknown')
            self.protocol_info['message_types'].add(message_type)
            
            # Inițializăm structura pentru acest tip dacă nu există
            if message_type not in self.message_types:
                self.message_types[message_type] = {
                    'count': 0,
                    'fields': {},
                    'examples': []
                }
            
            # Incrementăm contorul
            self.message_types[message_type]['count'] += 1
            
            # Extragem câmpurile
            for field in message.keys():
                if field not in self.message_types[message_type]['fields']:
                    self.message_types[message_type]['fields'][field] = 0
                self.message_types[message_type]['fields'][field] += 1
            
            # Salvăm un exemplu dacă nu avem deja prea multe
            if len(self.message_types[message_type]['examples']) < 5:
                example = message.copy()
                if tag:
                    example['_tag'] = tag
                self.message_types[message_type]['examples'].append(example)
            
            # Detectăm informații specifice pentru autentificare
            if 'pairingCode' in message:
                self.protocol_info['authentication_methods'].add('pairing_code')
            if message_type == 'challenge':
                self.protocol_info['authentication_methods'].add('challenge')
            if message_type == 'qr':
                self.protocol_info['authentication_methods'].add('qr_code')
                
        elif isinstance(message, list) and len(message) >= 2:
            # Posibil mesaj de handshake sau altă comandă de protocol
            if message[0] == 'admin':
                command = message[1] if len(message) > 1 else ''
                if command == 'init':
                    # Acesta este un mesaj de handshake
                    if message not in self.protocol_info['handshake_formats']:
                        self.protocol_info['handshake_formats'].append(message)
                    
                    # Extragem versiunea clientului
                    if len(message) > 2 and isinstance(message[2], list) and len(message[2]) >= 1:
                        self.protocol_info['client_versions'].add(message[2][0])
                        
                elif command == 'login':
                    # Mesaj de autentificare
                    self.protocol_info['authentication_methods'].add('login')
                
                elif command == 'request_code':
                    # Solicitare de cod de asociere
                    self.protocol_info['authentication_methods'].add('pairing_code')
    
    def _analyze_generic_json(self, data: Any) -> None:
        """
        Analizează date JSON generice căutând informații despre protocolul WhatsApp.
        
        Args:
            data: Datele JSON
        """
        # Parcurgerea recursivă a structurii JSON
        self._process_json_element(data)
    
    def _process_json_element(self, element: Any, path: str = '') -> None:
        """
        Procesează recursiv un element JSON căutând informații relevante.
        
        Args:
            element: Elementul JSON de procesat
            path: Calea curentă în structura JSON
        """
        if isinstance(element, dict):
            # Verificăm dacă arată ca un mesaj WhatsApp
            if 'type' in element:
                self._analyze_whatsapp_message(element)
            
            # Procesăm recursiv toate elementele dict
            for key, value in element.items():
                new_path = f"{path}.{key}" if path else key
                
                # Verificăm chei specifice
                if key == 'pairingCode':
                    self.protocol_info['authentication_methods'].add('pairing_code')
                elif key == 'clientVersion' or key == 'version':
                    if isinstance(value, str):
                        self.protocol_info['client_versions'].add(value)
                
                self._process_json_element(value, new_path)
                
        elif isinstance(element, list):
            # Procesăm recursiv toate elementele din listă
            for i, item in enumerate(element):
                new_path = f"{path}[{i}]"
                self._process_json_element(item, new_path)
    
    def _extract_json_from_text(self, text: str) -> None:
        """
        Extrage și analizează orice JSON valid din text.
        
        Args:
            text: Textul de analizat
        """
        # Căutăm obiecte JSON
        object_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
        for match in re.finditer(object_pattern, text):
            try:
                obj = json.loads(match.group(0))
                self._analyze_whatsapp_message(obj)
            except json.JSONDecodeError:
                pass
        
        # Căutăm array-uri JSON
        array_pattern = r'\[(?:[^\[\]]|(?:\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]))*\]'
        for match in re.finditer(array_pattern, text):
            try:
                arr = json.loads(match.group(0))
                self._analyze_whatsapp_message(arr)
            except json.JSONDecodeError:
                pass
    
    def _save_protocol_info(self) -> None:
        """
        Salvează informațiile despre protocol în fișiere pentru analiză ulterioară.
        """
        # Convertim set-uri în liste pentru JSON
        json_safe_info = {
            "client_versions": list(self.protocol_info['client_versions']),
            "message_types": list(self.protocol_info['message_types']),
            "endpoints": list(self.protocol_info['endpoints']),
            "handshake_formats": self.protocol_info['handshake_formats'],
            "authentication_methods": list(self.protocol_info['authentication_methods']),
            "known_headers": {k: list(v) for k, v in self.protocol_info['known_headers'].items()}
        }
        
        # Salvăm structura mesajelor
        try:
            with open(os.path.join(self.data_dir, 'protocol_info.json'), 'w', encoding='utf-8') as f:
                json.dump(json_safe_info, f, indent=2)
                
            with open(os.path.join(self.data_dir, 'message_types.json'), 'w', encoding='utf-8') as f:
                json.dump(self.message_types, f, indent=2)
                
            logger.info("Informațiile de protocol au fost salvate.")
        except Exception as e:
            logger.error(f"Eroare la salvarea informațiilor: {e}")
    
    def _generate_recommendations(self) -> Dict[str, List[str]]:
        """
        Generează recomandări pentru implementare bazate pe analiza protocoalelor.
        
        Returns:
            Dict cu recomandări pe categorii
        """
        recommendations = {
            "Versiune client": [],
            "Autentificare": [],
            "Protocol": [],
            "Headers": []
        }
        
        # Recomandări pentru versiunea clientului
        if self.protocol_info['client_versions']:
            latest_version = max(self.protocol_info['client_versions'])
            recommendations["Versiune client"].append(
                f"Folosește versiunea {latest_version} pentru comunicarea cu serverele"
            )
        
        # Recomandări pentru autentificare
        auth_methods = self.protocol_info['authentication_methods']
        if auth_methods:
            recommendations["Autentificare"].append(
                f"Implementează metodele de autentificare: {', '.join(sorted(auth_methods))}"
            )
            if 'pairing_code' in auth_methods:
                recommendations["Autentificare"].append(
                    "Prioritizează implementarea autentificării cu pairing code (mai simplu de folosit în bibliotecă)"
                )
        
        # Recomandări pentru protocol
        if self.protocol_info['handshake_formats']:
            recommendations["Protocol"].append(
                "Format handshake revizuit: actualizează structura mesajului în WebSocketProtocol.create_handshake_message()"
            )
        
        # Recomandări pentru headerele HTTP
        important_headers = ['User-Agent', 'Origin', 'Accept', 'Accept-Language', 'Sec-WebSocket-Extensions']
        if self.protocol_info['known_headers']:
            header_recs = []
            for header in important_headers:
                if header in self.protocol_info['known_headers']:
                    values = self.protocol_info['known_headers'][header]
                    if values:
                        header_recs.append(f"{header}: {next(iter(values))}")
            
            if header_recs:
                recommendations["Headers"].append(
                    "Adaugă sau actualizează headerele HTTP:\n    " + "\n    ".join(header_recs)
                )
        
        return recommendations

def main():
    """Funcție principală pentru analiza protocoalelor."""
    parser = argparse.ArgumentParser(description="Analizor de protocol WhatsApp")
    parser.add_argument("--file", "-f", help="Fișier de analizat (JSON sau text)")
    parser.add_argument("--dir", "-d", help="Director cu fișiere de analizat")
    parser.add_argument("--output", "-o", help="Fișier pentru salvarea raportului", default="whatsapp_protocol_report.txt")
    args = parser.parse_args()
    
    if not (args.file or args.dir):
        parser.error("Trebuie să specificați cel puțin un fișier sau un director pentru analiză.")
    
    analyzer = ProtocolAnalyzer()
    
    # Analizăm fișierul specific
    if args.file:
        if args.file.endswith('.json') or args.file.endswith('.har'):
            analyzer.analyze_json_file(args.file)
        else:
            analyzer.analyze_text_file(args.file)
    
    # Analizăm directorul
    if args.dir:
        analyzer.analyze_directory(args.dir)
    
    # Generăm și salvăm raportul
    report = analyzer.generate_report()
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Raport generat și salvat în {args.output}")
    print(f"\nRaport salvat în {args.output}")
    
    # Afișăm un sumar
    print("\n=== SUMAR ANALIZĂ ===")
    print(f"Versiuni client detectate: {len(analyzer.protocol_info['client_versions'])}")
    print(f"Tipuri de mesaje detectate: {len(analyzer.protocol_info['message_types'])}")
    print(f"Metode de autentificare detectate: {len(analyzer.protocol_info['authentication_methods'])}")
    print(f"Formate handshake detectate: {len(analyzer.protocol_info['handshake_formats'])}")
    print("=====================")

if __name__ == "__main__":
    main()