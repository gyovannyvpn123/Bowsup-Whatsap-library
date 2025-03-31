"""
Main application for demonstrating Bocksup functionality.

This is a simple Flask application that demonstrates the basic
features of the Bocksup library for WhatsApp integration.
It also provides tools for testing and debugging the library's functionality.
"""

import os
import logging
import json
import asyncio
from flask import Flask, render_template, request, jsonify, redirect, url_for
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "bocksup-demo-secret")

# Utilitare pentru a rula corutine asyncio în Flask
def async_route(f):
    """Decorator pentru a rula rute async în Flask."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        def run_async():
            try:
                return asyncio.run(f(*args, **kwargs))
            except Exception as e:
                logger.error(f"Error in async route: {str(e)}")
                return jsonify({'error': str(e)}), 500
        return run_async()
    return wrapper

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@app.route('/docs')
def docs():
    """Render the documentation page."""
    return render_template('docs.html')

@app.route('/examples')
def examples():
    """Render the examples page."""
    return render_template('examples.html')

@app.route('/debug')
def debug_page():
    """Render the debug page for testing the library functionality."""
    return render_template('debug.html')

@app.route('/api/test_connection', methods=['POST'])
@async_route
async def test_connection():
    """
    Run a connection test to WhatsApp servers.
    Requires a phone number for pairing code testing.
    """
    phone_number = request.json.get('phone_number', None)
    
    try:
        # Import Bocksup test module
        from bocksup.test_server_connection import test_server_connection
        
        # Run the test
        results = await test_server_connection(phone_number)
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f"Import error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error running connection test: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f"Error: {str(e)}"
        }), 500

@app.route('/api/request_pairing_code', methods=['POST'])
@async_route
async def request_pairing_code():
    """
    Request a pairing code from WhatsApp servers.
    Requires a phone number.
    """
    phone_number = request.json.get('phone_number')
    if not phone_number:
        return jsonify({
            'status': 'error',
            'error': 'Phone number is required'
        }), 400
    
    try:
        # Import authenticator
        from bocksup.auth.authenticator import Authenticator
        
        # Create an authenticator with phone number (password can be empty for pairing code)
        auth = Authenticator(phone_number, "")
        
        # Attempt to authenticate
        result = await auth.authenticate()
        
        return jsonify({
            'status': 'success',
            'authenticated': result,
            'pairing_code': "Please check your WhatsApp mobile app for the pairing code"
        })
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f"Import error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error requesting pairing code: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f"Error: {str(e)}"
        }), 500

@app.route('/api/library_info')
def library_info():
    """Return information about the Bocksup library."""
    try:
        # Import Bocksup if available
        import bocksup
        
        # Get version and modules
        version = getattr(bocksup, '__version__', 'Unknown')
        modules = [m for m in dir(bocksup) if not m.startswith('__')]
        
        # Check available features
        features = {
            'authentication': hasattr(bocksup, 'auth'),
            'messaging': hasattr(bocksup, 'messaging'),
            'encryption': hasattr(bocksup, 'encryption'),
            'groups': hasattr(bocksup, 'groups'),
            'media': hasattr(bocksup, 'media'),
            'registration': hasattr(bocksup, 'registration')
        }
        
        return jsonify({
            'version': version,
            'modules': modules,
            'features': features,
            'status': 'available'
        })
    except ImportError:
        return jsonify({
            'status': 'not_available',
            'error': 'Bocksup library is not available or cannot be imported.'
        })

@app.route('/api/analyze_protocol', methods=['POST'])
def analyze_protocol():
    """
    Analyze a captured protocol log to help with debugging.
    Uploads a log file that will be analyzed for WhatsApp protocol details.
    """
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'error': 'No file provided'
        }), 400
        
    file = request.files['file']
    if not file.filename:
        return jsonify({
            'status': 'error',
            'error': 'Empty filename'
        }), 400
    
    # Save the uploaded file
    log_dir = os.path.join(os.getcwd(), 'protocol_logs')
    os.makedirs(log_dir, exist_ok=True)
    
    file_path = os.path.join(log_dir, file.filename)
    file.save(file_path)
    
    try:
        # Determine file type and pass to appropriate handler
        from analyze_protocol import ProtocolAnalyzer
        
        analyzer = ProtocolAnalyzer()
        
        if file.filename.endswith('.json') or file.filename.endswith('.har'):
            analyzer.analyze_json_file(file_path)
        else:
            analyzer.analyze_text_file(file_path)
        
        # Generate a report
        report = analyzer.generate_report()
        
        return jsonify({
            'status': 'success',
            'report': report
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'error': f"Import error: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f"Error analyzing protocol: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)