#!/usr/bin/env python3
"""
Bocksup - Interfață web pentru biblioteca WhatsApp

Acest script oferă o interfață web pentru biblioteca Bocksup, permițând utilizatorilor
să testeze conexiunea, să obțină coduri de asociere și să trimită mesaje.
"""

import os
import sys
import asyncio
import logging
import json
import uuid
from typing import Dict, Any, Optional, Union

from flask import Flask, render_template, request, jsonify, session

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("Bocksup-Web")

# Crearea aplicației Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "bocksup_secret_key")

# Stare globală pentru a stoca conexiunea curentă între cereri
connections = {}

# Importarea modulelor Bocksup
from bocksup import create_client, test_server_connection
from bocksup.auth import Authenticator

# Rute API

@app.route('/')
def index():
    """Pagina principală"""
    return render_template('index.html')

@app.route('/about')
def about():
    """Pagina despre"""
    return render_template('about.html')

@app.route('/docs')
def docs():
    """Pagina documentație"""
    return render_template('docs.html')

@app.route('/examples')
def examples():
    """Pagina exemple"""
    return render_template('examples.html')

@app.route('/test')
def test_page():
    """Pagina de test"""
    return render_template('test.html')

@app.route('/pairing')
def pairing():
    """Pagina de asociere"""
    return render_template('pairing.html')

@app.route('/debug')
def debug():
    """Pagina de debug"""
    return render_template('debug.html')

@app.route('/api/test-connection', methods=['POST'])
def api_test_connection():
    """Testează conexiunea la serverele WhatsApp"""
    data = request.json or {}
    phone_number = data.get('phone_number')
    
    # Folosiți asyncio pentru a rula testul de conexiune
    async def run_test():
        results = await test_server_connection(phone_number)
        return results
    
    try:
        # Executați testul de conexiune
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(run_test())
        loop.close()
        
        # Formatați mesajele pentru afișare
        formatted_messages = []
        for msg in results.get('messages', []):
            if isinstance(msg.get('content'), dict):
                content = json.dumps(msg['content'], indent=2)
            else:
                content = str(msg.get('content', ''))
                if len(content) > 500:
                    content = content[:500] + "... (truncated)"
            
            formatted_messages.append({
                'direction': msg.get('direction', 'unknown'),
                'type': msg.get('type', 'unknown'),
                'content': content
            })
        
        results['messages'] = formatted_messages
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        logger.error(f"Eroare la testarea conexiunii: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/get-pairing-code', methods=['POST'])
def api_get_pairing_code():
    """Obține un cod de asociere WhatsApp"""
    data = request.json or {}
    phone_number = data.get('phone_number')
    
    if not phone_number:
        return jsonify({
            'success': False,
            'error': 'Numărul de telefon este obligatoriu'
        })
    
    # Generăm un ID unic pentru această conexiune
    connection_id = str(uuid.uuid4())
    
    # Folosiți asyncio pentru a obține codul de asociere
    async def run_pairing():
        authenticator = None
        try:
            logger.info(f"Solicitare cod de asociere pentru numărul: {phone_number}")
            
            # Creați un autentificator
            authenticator = Authenticator(phone_number)
            
            # Stocați referință la această conexiune
            connections[connection_id] = authenticator
            
            # Autentificați și obțineți codul
            authenticated = await authenticator.authenticate()
            
            if authenticated and authenticator.pairing_code:
                logger.info(f"Cod de asociere obținut: {authenticator.pairing_code}")
                return {
                    'success': True,
                    'pairing_code': authenticator.pairing_code
                }
            else:
                logger.error("Nu s-a putut obține codul de asociere")
                return {
                    'success': False,
                    'error': 'Nu s-a putut obține codul de asociere'
                }
        except Exception as e:
            logger.error(f"Eroare la obținerea codului de asociere: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # Curățare
            if authenticator and hasattr(authenticator, 'connection') and authenticator.connection:
                try:
                    await authenticator.connection.disconnect()
                except:
                    pass
            
            # Eliminați referința din dicționar
            if connection_id in connections:
                del connections[connection_id]
    
    try:
        # Executați solicitarea codului de asociere
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_pairing())
        loop.close()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Eroare la obținerea codului de asociere: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/library-info', methods=['GET'])
def api_library_info():
    """Returnează informații despre biblioteca Bocksup"""
    try:
        import bocksup
        
        return jsonify({
            'success': True,
            'info': {
                'name': 'Bocksup',
                'version': getattr(bocksup, '__version__', 'unknown'),
                'description': 'Bibliotecă Python pentru integrare WhatsApp',
                'modules': [
                    'auth - Autentificare',
                    'messaging - Mesagerie',
                    'layers - Componente stratificate',
                    'utils - Utilități',
                    'common - Funcții comune'
                ]
            }
        })
    except Exception as e:
        logger.error(f"Eroare la obținerea informațiilor bibliotecii: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # Verificați prezența șabloanelor
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        logger.warning(f"Directorul templates a fost creat: {templates_dir}")
    
    # Start server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)