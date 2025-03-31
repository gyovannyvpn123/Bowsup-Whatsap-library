from flask import Flask, render_template, request, jsonify
import asyncio
import websockets
import json
import time
import uuid
import logging
import os
import base64
import threading
from functools import wraps

# Configurare logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Bocksup-Web")

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "bocksup_secret_key")

# Constants
WA_WEB_URL = "wss://web.whatsapp.com/ws/chat"
CLIENT_TOKEN = f"bocksup_test_{int(time.time())}"
CLIENT_ID = f"bocksup_test:{str(uuid.uuid4())[:8]}"

# Variabile globale pentru stocarea rezultatelor conexiunii
connection_results = {}
pairing_codes = {}

def run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(func(*args, **kwargs))
            return result
        finally:
            loop.close()
    return wrapper

async def connect_to_whatsapp(phone_number, request_id):
    """Conectare la serverele WhatsApp și solicitare cod de asociere."""
    logger.info(f"[{request_id}] Conectare la {WA_WEB_URL}...")
    
    connection_results[request_id] = {
        "status": "connecting",
        "message": f"Inițierea conexiunii pentru {phone_number}...",
        "logs": []
    }
    
    try:
        # Conectare WebSocket
        async with websockets.connect(
            WA_WEB_URL, 
            subprotocols=["chat"]
        ) as websocket:
            connection_results[request_id]["status"] = "connected"
            connection_results[request_id]["message"] = "Conexiune WebSocket stabilită!"
            connection_results[request_id]["logs"].append("Conexiune WebSocket stabilită!")
            logger.info(f"[{request_id}] Conexiune WebSocket stabilită!")
            
            # Trimitere mesaj de handshake
            handshake_msg = {
                "clientToken": CLIENT_TOKEN + request_id[:4],
                "serverToken": None,
                "clientId": CLIENT_ID + request_id[:4],
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
            
            # Convertire mesaj la text JSON pentru trimitere
            json_msg = json.dumps(handshake_msg)
            logger.info(f"[{request_id}] Trimitere handshake: {json_msg}")
            connection_results[request_id]["logs"].append(f"Trimitere handshake...")
            await websocket.send(json_msg)
            
            # Așteaptă și procesează răspunsul la handshake
            handshake_response = await websocket.recv()
            
            # Determină tipul răspunsului (binar sau text)
            response_type = "binar" if isinstance(handshake_response, bytes) else "text"
            if response_type == "binar":
                try:
                    decoded = handshake_response.decode('latin-1')
                    response_preview = f"Răspuns binar primit: {decoded[:30]}... ({len(handshake_response)} bytes)"
                except:
                    response_preview = f"Răspuns binar primit: {len(handshake_response)} bytes"
            else:
                response_preview = f"Răspuns text primit: {handshake_response}"
                
            logger.info(f"[{request_id}] {response_preview}")
            connection_results[request_id]["logs"].append(response_preview)
            
            # Verifică dacă răspunsul conține eroarea "Text Frames are not supported"
            error_message = "Text Frames are not supported"
            if response_type == "binar" and 'decoded' in locals() and error_message in decoded:
                connection_results[request_id]["status"] = "binary_required"
                connection_results[request_id]["message"] = "Serverul necesită mesaje binare. Încercând o altă abordare..."
                connection_results[request_id]["logs"].append("Serverul necesită mesaje binare. Încercând o altă abordare...")
                
                # Deocamdată presupunem handshake reușit și continuăm
                logger.info(f"[{request_id}] Presupun handshake reușit și continuăm...")
                connection_results[request_id]["logs"].append("Presupun handshake reușit și continuăm...")
            else:
                connection_results[request_id]["status"] = "handshake_ok"
                connection_results[request_id]["message"] = "Handshake realizat cu succes!"
                connection_results[request_id]["logs"].append("Handshake realizat cu succes!")
            
            # Pauză scurtă
            await asyncio.sleep(1)
            
            # Trimitere cerere pentru cod de asociere
            pairing_request = {
                "tag": f"{int(time.time())}.--1",
                "type": "request_pairing_code",
                "phoneNumber": phone_number,
                "isPrimaryDevice": True,
                "method": "sms"  # Poate fi "voice" sau "sms"
            }
            
            # Trimitem cererea pentru codul de asociere ca text
            json_pairing = json.dumps(pairing_request)
            logger.info(f"[{request_id}] Trimitere cerere cod de asociere: {json_pairing}")
            connection_results[request_id]["logs"].append(f"Trimitere cerere cod de asociere pentru {phone_number}...")
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
                                        logger.info(f"[{request_id}] Răspuns decodificat ({encoding}): {decoded[:50]}...")
                                        connection_results[request_id]["logs"].append(f"Răspuns decodificat: {decoded[:50]}...")
                                        
                                        # Verificăm dacă este JSON
                                        if decoded.startswith('{'):
                                            try:
                                                json_data = json.loads(decoded)
                                                logger.info(f"[{request_id}] JSON valid: {json_data}")
                                                connection_results[request_id]["logs"].append(f"Răspuns JSON: {str(json_data)[:100]}...")
                                                
                                                # Verificăm pentru codul de asociere
                                                if "pairingCode" in json_data:
                                                    pairing_code = json_data['pairingCode']
                                                    logger.info(f"[{request_id}] COD DE ASOCIERE GĂSIT: {pairing_code}")
                                                    connection_results[request_id]["status"] = "pairing_code_received"
                                                    connection_results[request_id]["message"] = f"Cod de asociere primit: {pairing_code}"
                                                    connection_results[request_id]["logs"].append(f"COD DE ASOCIERE PRIMIT: {pairing_code}")
                                                    pairing_codes[request_id] = pairing_code
                                            except:
                                                pass
                                        break
                                    except:
                                        continue
                            except:
                                logger.info(f"[{request_id}] Răspuns binar brut: {len(pairing_response)} bytes")
                        else:
                            logger.info(f"[{request_id}] Răspuns text: {pairing_response}")
                            connection_results[request_id]["logs"].append(f"Răspuns text: {pairing_response}")
                            
                            # Verificăm dacă este JSON
                            try:
                                json_data = json.loads(pairing_response)
                                logger.info(f"[{request_id}] JSON valid: {json_data}")
                                
                                # Verificăm pentru codul de asociere
                                if "pairingCode" in json_data:
                                    pairing_code = json_data['pairingCode']
                                    logger.info(f"[{request_id}] COD DE ASOCIERE GĂSIT: {pairing_code}")
                                    connection_results[request_id]["status"] = "pairing_code_received"
                                    connection_results[request_id]["message"] = f"Cod de asociere primit: {pairing_code}"
                                    connection_results[request_id]["logs"].append(f"COD DE ASOCIERE PRIMIT: {pairing_code}")
                                    pairing_codes[request_id] = pairing_code
                            except:
                                pass
                    except asyncio.TimeoutError:
                        # Timeout pentru un singur recv, dar continuăm bucla
                        continue
            except Exception as e:
                logger.error(f"[{request_id}] Eroare la primirea codului de asociere: {e}")
                connection_results[request_id]["logs"].append(f"Eroare la primirea codului de asociere: {e}")
            
            logger.info(f"[{request_id}] Total răspunsuri primite: {len(pairing_responses)}")
            connection_results[request_id]["logs"].append(f"Total răspunsuri primite: {len(pairing_responses)}")
            
            if not pairing_responses:
                connection_results[request_id]["status"] = "no_response"
                connection_results[request_id]["message"] = "Nu s-a primit niciun răspuns pentru codul de asociere"
                connection_results[request_id]["logs"].append("Nu s-a primit niciun răspuns pentru codul de asociere")
                logger.warning(f"[{request_id}] Nu s-a primit niciun răspuns pentru codul de asociere")
                logger.info(f"[{request_id}] Verificați telefonul pentru a vedea dacă a apărut codul de asociere")
                connection_results[request_id]["logs"].append("Verificați telefonul pentru a vedea dacă a apărut codul de asociere")
            
            # Încheiem sesiunea
            try:
                disconnect_msg = {
                    "tag": f"{int(time.time())}.--2",
                    "type": "disconnect",
                    "reason": "USER_INITIATED"
                }
                json_disconnect = json.dumps(disconnect_msg)
                await websocket.send(json_disconnect)
                logger.info(f"[{request_id}] Deconectare trimisă")
                connection_results[request_id]["logs"].append("Deconectare trimisă")
            except:
                logger.warning(f"[{request_id}] Nu s-a putut trimite mesajul de deconectare")
                connection_results[request_id]["logs"].append("Nu s-a putut trimite mesajul de deconectare")
                
    except Exception as e:
        logger.error(f"[{request_id}] Eroare la conectare: {e}")
        connection_results[request_id]["status"] = "error"
        connection_results[request_id]["message"] = f"Eroare la conectare: {e}"
        connection_results[request_id]["logs"].append(f"Eroare la conectare: {e}")
        return False
    
    connection_results[request_id]["status"] = "completed"
    if request_id in pairing_codes:
        connection_results[request_id]["message"] = f"Proces finalizat. Cod de asociere: {pairing_codes[request_id]}"
    else:
        connection_results[request_id]["message"] = "Proces finalizat. Cod de asociere nu a fost găsit în răspunsuri."
    connection_results[request_id]["logs"].append("Proces finalizat")
    
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/pairing')
def pairing():
    return render_template('pairing.html')

@app.route('/api/request-pairing-code', methods=['POST'])
def request_pairing_code():
    data = request.json
    phone_number = data.get('phone_number', '')
    
    # Validare număr de telefon
    if not phone_number or not phone_number.isdigit() or len(phone_number) < 10:
        return jsonify({'success': False, 'error': 'Număr de telefon invalid'}), 400
    
    # Generează un ID unic pentru această cerere
    request_id = str(uuid.uuid4())
    
    # Inițializează rezultatele pentru acest ID
    connection_results[request_id] = {
        "status": "initializing",
        "message": "Inițializare cerere...",
        "logs": []
    }
    
    # Pornește procesul de conectare într-un thread separat
    thread = threading.Thread(target=run_async(connect_to_whatsapp), args=(phone_number, request_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True, 
        'request_id': request_id, 
        'message': 'Cerere înregistrată. Procesarea datelor a început.'
    })

@app.route('/api/check-pairing-status/<request_id>', methods=['GET'])
def check_pairing_status(request_id):
    if request_id not in connection_results:
        return jsonify({'success': False, 'error': 'ID de cerere invalid'}), 404
    
    result = connection_results[request_id]
    
    # Adaugă codul de asociere dacă există
    if request_id in pairing_codes:
        result['pairing_code'] = pairing_codes[request_id]
    
    return jsonify({
        'success': True,
        'result': result
    })

@app.route('/test')
def test():
    # Pagină pentru testarea funcționalității
    return render_template('test.html')

@app.route('/docs')
def docs():
    # Documentația API
    return render_template('docs.html')

if __name__ == '__main__':
    # Creează directorul templates dacă nu există
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(host='0.0.0.0', port=5000, debug=True)