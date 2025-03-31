import asyncio
import logging
import json
import sys
import time

# Configurare logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestConnection")

async def test_whatsapp_connection():
    """Testează conexiunea la serverele WhatsApp folosind funcțiile existente"""
    
    print("\n=== Test Conexiune WhatsApp ===")
    
    try:
        # Importăm funcția corectă din modul
        from bocksup.test_server_connection import test_server_connection
        
        # Testăm conexiunea de bază (fără număr de telefon)
        print("\n[1] Testare conexiune de bază...")
        
        result_basic = await test_server_connection()
        
        print("\nRezultat test de bază:")
        print(f"- Conexiune: {'✓' if result_basic.get('connection') else '✗'}")
        print(f"- Handshake: {'✓' if result_basic.get('handshake') else '✗'}")
        print(f"- Challenge: {'✓' if result_basic.get('challenge') else '✗'}")
        
        if result_basic.get("errors"):
            print("\nErori întâlnite:")
            for error in result_basic.get("errors"):
                print(f"  - {error}")
        
        # Scrie rezultatele într-un fișier
        with open("connection_test_results.json", "w") as f:
            json.dump(result_basic, f, indent=2, default=str)
        
        print("\nRezultatele detaliate au fost salvate în connection_test_results.json")
        
        # Dacă testul de bază a reușit, încercăm și testul cu pairing code
        if result_basic.get("connection") and result_basic.get("handshake"):
            phone_number = "40756469325"  # Numărul tău de telefon
            
            print(f"\n[2] Testare cod de asociere pentru {phone_number}...")
            print("(Acest test poate dura până la 10 secunde)")
            
            result_pairing = await test_server_connection(phone_number)
            
            print("\nRezultat test pairing code:")
            print(f"- Conexiune: {'✓' if result_pairing.get('connection') else '✗'}")
            print(f"- Handshake: {'✓' if result_pairing.get('handshake') else '✗'}")
            print(f"- Pairing Code: {'✓' if result_pairing.get('pairing_code') else '✗'}")
            
            if result_pairing.get("errors"):
                print("\nErori întâlnite:")
                for error in result_pairing.get("errors"):
                    print(f"  - {error}")
            
            # Căutăm pairing code-ul în mesaje
            pairing_code = None
            if "messages" in result_pairing:
                for msg in result_pairing["messages"]:
                    if "pairing_code" in msg:
                        pairing_code = msg["pairing_code"]
                        break
            
            if pairing_code:
                print(f"\n✓ Cod de asociere obținut: {pairing_code}")
                print("\nInstrucțiuni de folosire:")
                print("1. Deschideți WhatsApp pe telefonul dvs")
                print("2. Mergeți la Setări > Dispozitive conectate")
                print("3. Selectați 'Conectare dispozitiv'")
                print("4. Introduceți codul de mai sus când vi se solicită")
            
            # Scrie rezultatele într-un fișier
            with open("pairing_test_results.json", "w") as f:
                json.dump(result_pairing, f, indent=2, default=str)
            
            print("\nRezultatele detaliate au fost salvate în pairing_test_results.json")
        
        return {
            "basic_test": result_basic,
            "pairing_test": result_pairing if "result_pairing" in locals() else None
        }
        
    except ImportError as e:
        logger.error(f"Nu s-a putut importa funcția de test: {e}")
        print(f"\n✗ Eroare de import: {e}")
        print("\nAsigurați-vă că biblioteca Bocksup este instalată corect.")
        return {"error": f"Import error: {str(e)}"}
        
    except Exception as e:
        logger.error(f"Eroare neașteptată: {e}")
        print(f"\n✗ Eroare neașteptată: {e}")
        return {"error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    print("Testare conexiune WhatsApp folosind biblioteca Bocksup")
    print("Acest script testează conexiunea la serverele WhatsApp.")
    
    try:
        result = asyncio.run(test_whatsapp_connection())
        sys.exit(0 if result.get("basic_test", {}).get("connection") else 1)
    except KeyboardInterrupt:
        print("\nTest oprit de utilizator")
        sys.exit(130)