#!/usr/bin/env python3

import sys
import os

# Add project to Python path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
bocksup_dir = os.path.join(current_dir, "bocksup")
sys.path.insert(0, current_dir)

try:
    import bocksup
    
    # Print basic library information
    print(f"Bocksup version: {getattr(bocksup, '__version__', 'Unknown')}")
    
    # Check modules
    print("\nMain modules:")
    modules = [m for m in dir(bocksup) if not m.startswith('__')]
    for module in modules:
        print(f"- {module}")
    
    # Check features
    print("\nMain features:")
    print("- Authentication:", "Available" if hasattr(bocksup, 'auth') else "Not available")
    print("- Messaging:", "Available" if hasattr(bocksup, 'messaging') else "Not available")
    print("- Encryption:", "Available" if hasattr(bocksup, 'encryption') else "Not available")
    print("- Groups:", "Available" if hasattr(bocksup, 'groups') else "Not available")
    print("- Media handling:", "Available" if hasattr(bocksup, 'media') else "Not available")
    print("- Registration:", "Available" if hasattr(bocksup, 'registration') else "Not available")
    
    # Test utility functions
    print("\nUtility functions:")
    if hasattr(bocksup, 'generate_random_id'):
        print(f"- generate_random_id: {bocksup.generate_random_id()}")
    if hasattr(bocksup, 'timestamp_now'):
        print(f"- timestamp_now: {bocksup.timestamp_now()}")
    if hasattr(bocksup, 'format_phone_number'):
        print(f"- format_phone_number: {bocksup.format_phone_number('1234567890')}")
        
    print("\nLibrary initialized successfully!")
    
except ImportError as e:
    print(f"Error importing bocksup: {e}")
    print("Make sure the library is properly installed or in the Python path.")
except Exception as e:
    print(f"Unexpected error: {e}")