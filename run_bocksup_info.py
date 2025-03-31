#!/usr/bin/env python3
"""
Script pentru afișarea informațiilor despre biblioteca Bocksup
Aceasta este o versiune de workflow care rulează în directorul principal al proiectului
"""

import sys
import os
import logging

# Configurare logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BocksupInfo")

# Asigură-te că putem importa bocksup
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    import bocksup
    
    # Afișează versiunea
    version = bocksup.__version__ if hasattr(bocksup, '__version__') else "necunoscută"
    print(f"Bocksup version: {version}")
    
    # Afișează modulele principale
    print("\nMain modules:")
    for module in dir(bocksup):
        if not module.startswith('__'):
            print(f"- {module}")
    
    # Afișează funcționalitățile
    print("\nMain features:")
    print("- Authentication:", "Available" if hasattr(bocksup, 'auth') else "Not available")
    print("- Messaging:", "Available" if hasattr(bocksup, 'messaging') else "Not available")
    print("- Encryption:", "Available" if hasattr(bocksup, 'encryption') else "Not available")
    print("- Groups:", "Available" if hasattr(bocksup, 'groups') else "Not available")
    print("- Media handling:", "Available" if hasattr(bocksup, 'media') else "Not available")
    print("- Registration:", "Available" if hasattr(bocksup, 'registration') else "Not available")
    
except ImportError as e:
    logger.error(f"Nu s-a putut importa biblioteca Bocksup: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Eroare la afișarea informațiilor: {e}")
    sys.exit(1)