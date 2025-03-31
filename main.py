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
    
    try:
        # Simulam obținerea unui cod de asociere
        # În implementarea reală, am folosi bocksup.auth.request_pairing_code
        
        # Creăm o funcție helper pentru a rula async într-un context sync
        def run_async_pairing_request():
            import asyncio
            import random
            import string
            
            # În versiunea reală, am folosi bocksup.auth.request_pairing_code
            # Pentru simulare, generăm un cod aleator
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Simulăm un delay de rețea
            loop.run_until_complete(asyncio.sleep(1))
            
            # Generează un cod de 8 caractere
            pairing_code = ''.join(random.choices(string.digits, k=8))
            session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            
            loop.close()
            return {
                "success": True,
                "pairing_code": pairing_code,
                "session_id": session_id,
                "expiration": 600  # expiră în 10 minute
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
    
    try:
        # Simulam verificarea autentificării
        # În implementarea reală, am verifica cu WhatsApp dacă codul a fost acceptat
        
        # Creăm o funcție helper pentru a rula async într-un context sync
        def run_async_verification():
            import asyncio
            import random
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Simulăm un delay de rețea și procesare
            loop.run_until_complete(asyncio.sleep(2))
            
            # Simulăm o probabilitate de 80% de succes
            success = random.random() < 0.8
            
            loop.close()
            return {
                "success": success,
                "phone_number": phone_number,
                "message": "Autentificare reușită" if success else "Codul a expirat sau a fost introdus greșit",
                "token": ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32)) if success else None
            }
        
        # Rulează verificarea autentificării
        result = run_async_verification()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Eroare la verificarea autentificării: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)