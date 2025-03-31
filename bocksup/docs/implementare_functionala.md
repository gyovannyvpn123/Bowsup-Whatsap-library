# Ghid pentru implementarea funcțională a Bocksup cu serverele WhatsApp

Acest document descrie pașii necesari pentru a face biblioteca Bocksup complet funcțională cu serverele WhatsApp reale.

## Teste reale cu serverele WhatsApp

Biblioteca include un modul dedicat pentru testarea cu serverele WhatsApp reale: `bocksup/test_server_connection.py`. 
Utilizează acest modul pentru a:

1. Capta răspunsurile reale de la serverele WhatsApp
2. Înțelege formatul exact și secvența mesajelor așteptate
3. Identifica diferențele dintre implementarea curentă și comportamentul real

```bash
# Rulează testarea și captarea răspunsurilor
python -m bocksup.test_server_connection +4400000000000
```

Înlocuiește numărul de telefon cu un număr real pentru a testa solicitarea pairing code.

### Parametri de testare

Pentru testarea extensivă, ar trebui să captezi și să analizezi:

1. Procesul inițial de handshake și challenge
2. Răspunsul la solicitarea unui pairing code
3. Verificarea pairing code-ului
4. Răspunsurile după autentificare
5. Comportamentul diferitelor tipuri de mesaje

## Ajustarea implementării

Pe baza răspunsurilor reale, trebuie să ajustezi implementarea în:

1. **bocksup/layers/protocol/websocket_protocol.py**: modifică `process_message()` și alte funcții pentru a se potrivi exact cu răspunsurile serverului

2. **bocksup/auth/authenticator.py**: actualizează `_authenticate_web()` pentru a implementa corect fluxul de autentificare bazat pe răspunsurile reale

3. **bocksup/common/constants.py**: actualizează toate constantele, în special:
   - WHATSAPP_WEBSOCKET_URL
   - CLIENT_VERSION
   - PROTOCOL_VERSION
   - USER_AGENT
   - Header-ele necesare pentru conectare

4. **bocksup/layers/network/connection.py**: ajustează logica de conectare, ping și reconectare conform comportamentului observat

## Implementarea protocolului de criptare Signal

Protocolul Signal implementat în `bocksup/encryption/signal_protocol.py` trebuie ajustat și extins:

1. Implementează suportul real pentru curbe eliptice Curve25519 în locul simulării actuale
2. Implementează procesul X3DH (Extended Triple Diffie-Hellman) pentru stabilirea inițială a cheilor
3. Implementează algoritmul Double Ratchet pentru actualizarea continuă a cheilor
4. Implementează managementul sesiunilor pentru sesiuni multiple

Resurse utile:
- [Specificațiile protocolului Signal](https://signal.org/docs/)
- [Specificațiile X3DH](https://signal.org/docs/specifications/x3dh/)
- [Specificațiile Double Ratchet](https://signal.org/docs/specifications/doubleratchet/)

```python
# Exemplu de utilizare a protocolului Signal pentru criptarea mesajelor
from bocksup.encryption.signal_protocol import SignalProtocol

# Inițializează protocolul
signal = SignalProtocol()
signal.generate_identity()
signal.generate_pre_keys()
signal.generate_signed_pre_key()

# Stabilește o sesiune
session_id = signal.initiate_session(recipient_id, recipient_key)

# Criptează și trimite un mesaj
encrypted = signal.encrypt_message(session_id, "Mesaj criptat end-to-end")
# Trimite mesajul criptat prin conexiunea WebSocket

# La primire, decriptează mesajul
decrypted = signal.decrypt_message(encrypted_message)
```

## Rezolvarea problemelor de interacțiune reală

Testele reale vor expune probleme suplimentare care trebuie rezolvate:

1. **Gestionarea reconectărilor**: implementează o strategie robustă pentru detectarea și gestionarea deconectărilor

2. **Rate limiting**: implementează logica pentru a respecta limitele de rată impuse de servere, cu mecanism de back-off exponențial

3. **Probleme QR/Pairing**: implementează gestionarea erorilor și reîncercărilor pentru procesul de autentificare

4. **Rotația cheilor**: implementează mecanismul pentru rotația periodică a cheilor de sesiune

5. **Păstrarea stării**: asigură-te că starea de criptare este salvată și restaurată corect între sesiuni

## Testare și validare

După fiecare modificare semnificativă:

1. Rulează modulul de testare a serverului pentru a verifica dacă comportamentul s-a îmbunătățit
2. Testează diferite scenarii de mesaje și autentificare
3. Monitorizează conexiunea pentru stabilitate pe perioade mai lungi
4. Testează gestionarea erorilor și recuperarea

## Implementarea funcționalităților suplimentare

Pentru o librărie completă, implementează:

1. **Suport pentru grupuri**: captează și implementează protocolul pentru gestionarea grupurilor
2. **Gestionarea media**: implementează trimiterea și primirea de imagini, audio, video, etc.
3. **Notificări de prezență**: implementează gestionarea statusurilor online/offline, seen, typing
4. **Contacte**: implementează sincronizarea și gestionarea contactelor

## Menținerea compatibilității

WhatsApp actualizează frecvent protocolul, așa că biblioteca trebuie:

1. Să detecteze modificări ale protocolului
2. Să implementeze un mecanism de actualizare a constantelor și comportamentului
3. Să includă o strategie pentru versiuni și compatibilitate înapoi

Prin urmarea acestor pași și testarea extensivă, Bocksup poate deveni o alternativă funcțională la yowsup, adaptată la protocolul WhatsApp actual.