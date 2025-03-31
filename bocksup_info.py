#!/usr/bin/env python3
"""
Script pentru afișarea informațiilor despre biblioteca Bocksup
"""

import sys
import logging

# Configurare logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BocksupInfo")

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