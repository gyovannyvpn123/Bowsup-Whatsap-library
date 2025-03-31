"""
Main application for demonstrating Bocksup functionality.

This is a simple Flask application that demonstrates the basic
features of the Bocksup library for WhatsApp integration.
"""

import os
import logging
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "bocksup-demo-secret")

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)