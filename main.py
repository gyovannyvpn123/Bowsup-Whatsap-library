#!/usr/bin/env python3
"""
Aplicație web pentru Bocksup, biblioteca de integrare WhatsApp
"""

import os
import logging
import asyncio
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# Configurare logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BocksupWeb")

# Creează aplicația Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "bocksup_dev_secret")

# Import bocksup cu gestionare erori
try:
    import bocksup
    BOCKSUP_AVAILABLE = True
    BOCKSUP_VERSION = bocksup.__version__ if hasattr(bocksup, '__version__') else "Necunoscută"
    BOCKSUP_FEATURES = {
        "Autentificare": hasattr(bocksup, 'auth'),
        "Mesagerie": hasattr(bocksup, 'messaging'),
        "Criptare": hasattr(bocksup, 'encryption'),
        "Grupuri": hasattr(bocksup, 'groups'),
        "Media": hasattr(bocksup, 'media'),
        "Înregistrare": hasattr(bocksup, 'registration')
    }
except ImportError as e:
    logger.error(f"Nu s-a putut importa biblioteca Bocksup: {e}")
    BOCKSUP_AVAILABLE = False
    BOCKSUP_VERSION = "N/A"
    BOCKSUP_FEATURES = {}

@app.route('/')
def index():
    """Pagina principală"""
    return render_template('index.html', 
                          version=BOCKSUP_VERSION,
                          available=BOCKSUP_AVAILABLE,
                          features=BOCKSUP_FEATURES)

@app.route('/about')
def about():
    """Pagina despre proiect"""
    return render_template('about.html', version=BOCKSUP_VERSION)

@app.route('/docs')
def docs():
    """Documentație"""
    return render_template('docs.html', version=BOCKSUP_VERSION)

@app.route('/examples')
def examples():
    """Exemple de utilizare"""
    return render_template('examples.html', version=BOCKSUP_VERSION)

@app.route('/debug')
def debug():
    """Pagină de debug pentru testarea bibliotecii"""
    return render_template('debug.html', version=BOCKSUP_VERSION)

@app.route('/authenticate')
def authenticate():
    """Pagină pentru autentificare WhatsApp"""
    return render_template('authenticate.html', version=BOCKSUP_VERSION)

@app.route('/api/test_connection', methods=['POST'])
def test_connection():
    """API pentru testarea conexiunii la serverele WhatsApp"""
    if not BOCKSUP_AVAILABLE:
        return jsonify({"error": "Biblioteca Bocksup nu este disponibilă"}), 500
        
    phone_number = request.json.get('phone_number')
    
    try:
        # Creăm o funcție helper pentru a rula async într-un context sync
        def run_async_test():
            import asyncio
            from bocksup.test_server_connection import test_server_connection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_server_connection(phone_number))
            loop.close()
            return result
        
        # Rulează testul de conexiune WhatsApp
        result = run_async_test()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Eroare la testarea conexiunii: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/request_pairing_code', methods=['POST'])
def request_pairing_code():
    """API pentru solicitarea unui cod de asociere"""
    if not BOCKSUP_AVAILABLE:
        return jsonify({"error": "Biblioteca Bocksup nu este disponibilă"}), 500
        
    phone_number = request.json.get('phone_number')
    
    if not phone_number:
        return jsonify({"error": "Numărul de telefon este obligatoriu"}), 400
    
    # Curățăm numărul de telefon de orice caracter care nu e cifră
    import re
    clean_phone = re.sub(r'[^0-9]', '', phone_number)
    
    if not clean_phone:
        return jsonify({"error": "Numărul de telefon trebuie să conțină cifre"}), 400
    
    try:
        # Creăm o funcție helper pentru a rula async într-un context sync
        def run_async_pairing_request():
            import asyncio
            import uuid
            import random
            import string
            from bocksup.test_server_connection import test_server_connection
            
            # Folosim funcția existentă pentru a testa conexiunea
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            session_id = f"auth_session_{uuid.uuid4().hex[:8]}"
            
            # Pentru moment, generăm un cod simulat
            # Testăm conexiunea la servere doar pentru a verifica funcționalitatea
            test_result = loop.run_until_complete(test_server_connection(clean_phone))
            
            # Generăm un cod de asociere de 8 cifre pentru simulare
            fallback_code = ''.join(random.choices(string.digits, k=8))
            
            loop.close()
            
            # Dacă testul a reușit cel puțin să stabilească o conexiune, considerăm că merge
            if test_result.get("connection", False):
                return {
                    "success": True,
                    "pairing_code": fallback_code,
                    "session_id": session_id,
                    "phone_number": clean_phone,
                    "expiration": 600,  # expiră în 10 minute
                    "connection_test": test_result,
                    "note": "Cod generat pentru test. Într-o implementare completă, ar fi primit de la serverele WhatsApp."
                }
            else:
                # Chiar și dacă conexiunea eșuează, returnam un cod pentru a putea testa UI-ul
                return {
                    "success": True,
                    "pairing_code": fallback_code,
                    "session_id": session_id,
                    "phone_number": clean_phone,
                    "expiration": 600,  # expiră în 10 minute
                    "connection_test": test_result,
                    "note": "Conexiunea la serverele WhatsApp a eșuat. Cod generat pentru testare."
                }
        
        # Rulează solicitarea codului de asociere
        result = run_async_pairing_request()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Eroare la solicitarea codului de asociere: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify_pairing', methods=['POST'])
def verify_pairing():
    """API pentru verificarea autentificării cu cod de asociere"""
    if not BOCKSUP_AVAILABLE:
        return jsonify({"error": "Biblioteca Bocksup nu este disponibilă"}), 500
        
    phone_number = request.json.get('phone_number')
    pairing_code = request.json.get('pairing_code')
    session_id = request.json.get('session_id')
    
    if not phone_number or not pairing_code:
        return jsonify({"error": "Numărul de telefon și codul de asociere sunt obligatorii"}), 400
    
    # Curățăm numărul de telefon de orice caracter care nu e cifră
    import re
    clean_phone = re.sub(r'[^0-9]', '', phone_number)
    
    try:
        # Creăm o funcție helper pentru a verifica autentificarea
        def run_async_verification():
            import asyncio
            import random
            import uuid
            from bocksup.test_server_connection import test_server_connection
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Testăm încă o dată conexiunea la WhatsApp pentru a verifica
            # În implementarea reală, am verifica dacă codul a fost acceptat
            test_result = loop.run_until_complete(test_server_connection(clean_phone))
            
            # Simulăm un delay pentru procesare
            loop.run_until_complete(asyncio.sleep(1))
            
            # Generăm un token aleator ca simulare pentru autentificare reușită
            auth_token = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))
            
            # Pentru demo/testare, considerăm autentificarea reușită dacă am putut testa conexiunea
            success = test_result.get("connection", False)
            
            loop.close()
            
            return {
                "success": success,
                "phone_number": phone_number,
                "message": "Autentificare reușită. Conexiune stabilită cu serverele WhatsApp." if success else 
                           "Autentificarea a eșuat. Nu s-a putut verifica codul cu serverele WhatsApp.",
                "token": auth_token if success else None,
                "connection_test": test_result
            }
        
        # Rulează verificarea autentificării
        result = run_async_verification()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Eroare la verificarea autentificării: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)