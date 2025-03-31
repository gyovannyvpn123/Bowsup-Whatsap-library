#!/usr/bin/env python3
"""
Script pentru afișarea informațiilor despre biblioterca Bocksup.
"""

import bocksup
# Import explicit pentru submodulele necesare
import bocksup.auth.authenticator
import bocksup.messaging.client

def main():
    """Afișează informații despre biblioteca Bocksup."""
    print("\n=== Informații Bocksup ===\n")
    
    # Versiune
    print(f"Versiune Bocksup: {bocksup.__version__}")
    
    # Module principale
    print("\nModule principale:")
    for module in dir(bocksup):
        if not module.startswith('__'):
            print(f"- {module}")
    
    # Funcționalități disponibile
    print("\nFuncționalități principale:")
    print("- Autentificare:", "Disponibilă" if hasattr(bocksup, 'auth') else "Indisponibilă")
    print("- Mesagerie:", "Disponibilă" if hasattr(bocksup, 'messaging') else "Indisponibilă")
    print("- Criptare:", "Disponibilă" if hasattr(bocksup, 'encryption') else "Indisponibilă")
    print("- Grupuri:", "Disponibile" if hasattr(bocksup, 'groups') else "Indisponibile")
    print("- Procesare media:", "Disponibilă" if hasattr(bocksup, 'media') else "Indisponibilă")
    print("- Înregistrare:", "Disponibilă" if hasattr(bocksup, 'registration') else "Indisponibilă")
    
    # Clasa de autentificare
    if hasattr(bocksup, 'auth'):
        print("\nClasa Authenticator:")
        try:
            auth = bocksup.auth.authenticator.Authenticator("12345678901")
            methods = [m for m in dir(auth) if not m.startswith('__')]
            print(f"- Metode disponibile: {len(methods)}")
            print("- Exemple metode: " + ", ".join(methods[:5]) + " ...")
        except Exception as e:
            print(f"- Eroare la instanțierea Authenticator: {e}")
    
    # Mesagerie
    if hasattr(bocksup, 'messaging'):
        print("\nClasa MessagingClient:")
        try:
            # Corect: MessagingClient este în submodulul client
            client = bocksup.messaging.client.MessagingClient("12345678901")
            methods = [m for m in dir(client) if not m.startswith('__')]
            print(f"- Metode disponibile: {len(methods)}")
            print("- Exemple metode: " + ", ".join(methods[:5]) + " ...")
        except Exception as e:
            print(f"- Eroare la instanțierea MessagingClient: {e}")
    
    # Test Server Connection
    print("\nTest server connection:")
    print("- Funcția test_server_connection este disponibilă")
    print("  Această funcție poate testa conexiunea cu serverele WhatsApp")
    print("  fără a avea nevoie de autentificare.")
    
    print("\n=== End ===\n")

if __name__ == "__main__":
    main()