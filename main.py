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
    return render_template('about.html')

@app.route('/docs')
def docs():
    """Documentație"""
    return render_template('docs.html')

@app.route('/examples')
def examples():
    """Exemple de utilizare"""
    return render_template('examples.html')

@app.route('/debug')
def debug():
    """Pagină de debug pentru testarea bibliotecii"""
    return render_template('debug.html')

@app.route('/api/test_connection', methods=['POST'])
async def test_connection():
    """API pentru testarea conexiunii la serverele WhatsApp"""
    if not BOCKSUP_AVAILABLE:
        return jsonify({"error": "Biblioteca Bocksup nu este disponibilă"}), 500
        
    phone_number = request.json.get('phone_number')
    
    try:
        # Rulează testul de conexiune WhatsApp
        result = await bocksup.test_server_connection(phone_number)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Eroare la testarea conexiunii: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)