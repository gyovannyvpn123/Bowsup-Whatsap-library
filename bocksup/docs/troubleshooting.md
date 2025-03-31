# Troubleshooting și rezolvarea problemelor

Acest document oferă ghiduri pentru diagnosticarea și rezolvarea problemelor comune întâlnite în timpul utilizării bibliotecii Bocksup.

## Probleme de conectare

### Nu se poate conecta la serverele WhatsApp

1. **Verifică URL-ul WebSocket**: Asigură-te că constanta `WHATSAPP_WEBSOCKET_URL` din `bocksup/common/constants.py` este actualizată.

2. **Verifică header-ele de conectare**: Serverele WhatsApp se pot actualiza pentru a cere header-e diferite sau valori specifice. Verifică `connection.py` și modifică header-ele după necesități.

3. **User-Agent actualizat**: Asigură-te că User-Agent-ul este suficient de recent pentru a fi acceptat de servere.

4. **Probleme de rețea**: Verifică dacă există restricții de firewall sau proxy care blochează conexiunile WebSocket.

### Conexiunea se închide imediat după deschidere

1. **Handshake incorect**: Verifică dacă mesajul de handshake este formatat corect conform protocolului actual.

2. **Protocol actualizat**: WhatsApp ar fi putut actualiza protocolul. Captează și analizează răspunsurile pentru a adapta implementarea.

3. **Probleme de timeout**: Ajustează timeouts pentru conexiuni și ping-uri.

## Probleme de autentificare

### Nu se poate obține pairing code

1. **Format număr de telefon incorect**: Asigură-te că numărul de telefon este în formatul internațional corect (fără +).

2. **Rate limiting**: Serverele WhatsApp pot limita numărul de solicitări. Implementează un mecanism de back-off exponențial.

3. **Implementare protocol incorectă**: Verifică și ajustează implementarea protocolului conform răspunsurilor reale.

### Autentificarea eșuează după introducerea pairing code

1. **Timp expirat**: Asigură-te că pairing code-ul este introdus suficient de repede (cca. 60 secunde).

2. **Format mesaj de verificare incorect**: Verifică formatul mesajului de verificare a pairing code-ului.

3. **Challenge-data incomplet**: Asigură-te că toate datele de challenge sunt procesate și folosite corect.

## Probleme cu mesajele

### Mesajele nu sunt trimise

1. **Sesiune neautentificată**: Verifică dacă sesiunea este autentificată complet.

2. **Format mesaj incorect**: Verifică formatul mesajului față de protocolul actual.

3. **Erori de criptare**: Verifică implementarea protocolului Signal.

### Mesajele nu sunt primite

1. **Gestionare incorectă a evenimentelor**: Verifică dacă evenimentele de mesaj sunt capturate și procesate corect.

2. **Probleme de decriptare**: Verifică implementarea protocolului de criptare.

3. **WebSocket închis**: Asigură-te că conexiunea WebSocket este menținută deschisă.

## Probleme de criptare

### Erori în procesul de criptare/decriptare

1. **Implementare incompletă Signal**: Asigură-te că toate etapele procesului Signal sunt implementate corect.

2. **Probleme cu cheile de sesiune**: Verifică generarea și managementul cheilor.

3. **Algoritmi neconcordanți**: Asigură-te că utilizezi algoritmii corecți pentru criptare/decriptare (AES, Curve25519, etc.).

## Gestionarea grupurilor

### Nu se pot crea sau gestiona grupuri

1. **Implementare incompletă**: Protocolul pentru grupuri poate necesita mesaje specifice care nu sunt încă implementate.

2. **Permisiuni insuficiente**: Asigură-te că clientul are permisiunile necesare pentru operațiunile cu grupuri.

## Probleme media

### Nu se pot trimite sau primi fișiere media

1. **Implementare media server incorectă**: Verifică dacă constanta `WHATSAPP_MEDIA_SERVER` este corectă.

2. **Procesare incorectă a criptării media**: Fișierele media pot avea un protocol separat de criptare.

## Instrumente de diagnosticare

### Activarea logging-ului detaliat

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bocksup_debug.log')
    ]
)
```

### Capturarea traficului WebSocket

Folosește modulul `test_server_connection.py` pentru a capta și analiza traficul WebSocket.

### Verificarea versiunilor protocolului

WhatsApp utilizează versiuni specifice pentru protocol. Verifică periodic dacă versiunea protocolului trebuie actualizată.

## Raportarea problemelor

Când raportezi o problemă, include:

1. Versiunea Bocksup
2. Mesajele de logging relevante
3. Pasul exact în care apare problema
4. Răspunsul serverului (dacă este disponibil)

## Resurse suplimentare pentru debugging

1. Inspectarea WebSocket din browsere: Folosește browserul pentru a analiza traficul WhatsApp Web
2. Instrumente de captură de rețea: Wireshark (criptarea SSL/TLS trebuie dezactivată pentru analiză)
3. Grupuri și forumuri de reverse engineering: Caută informații actualizate despre protocolul WhatsApp