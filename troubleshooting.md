# Ghid de Troubleshooting pentru Biblioteca Bocksup

Acest ghid oferă soluții pentru problemele comune întâlnite la utilizarea bibliotecii Bocksup pentru integrarea cu WhatsApp.

## Cuprins

1. [Probleme de conectare](#probleme-de-conectare)
2. [Erori de autentificare](#erori-de-autentificare)
3. [Probleme cu trimiterea mesajelor](#probleme-cu-trimiterea-mesajelor)
4. [Erori de criptare](#erori-de-criptare)
5. [Probleme cu fișiere media](#probleme-cu-fișiere-media)
6. [Actualizarea bibliotecii](#actualizarea-bibliotecii)
7. [Diagnostic și raportare](#diagnostic-și-raportare)

## Probleme de conectare

### Nu se poate stabili conexiunea cu serverele WhatsApp

**Simptome:**
- Eroare `ConnectionError: Nu s-a putut conecta la WhatsApp: [Detalii eroare]`
- Aplicația se blochează la `await client.connect()`

**Soluții:**
1. **Verificați conexiunea la internet** - Asigurați-vă că dispuneți de o conexiune stabilă la internet.
2. **Verificați firewall-ul sau proxy-ul** - Asigurați-vă că conexiunile WebSocket către `web.whatsapp.com` sunt permise.
3. **Actualizați versiunile client** - Versiunile WhatsApp se schimbă frecvent. Actualizați constantele `WHATSAPP_WEB_VERSION` și `WHATSAPP_WEB_VERSION_HASH` din fișierul de configurare.
4. **Verificați timeout-urile** - Creșteți valorile timeout pentru conexiune în situații cu latență mare.

### Deconectări frecvente

**Simptome:**
- Conexiunea se întrerupe după câteva minute
- Erori `ConnectionClosed` în log-uri

**Soluții:**
1. **Ajustați parametrii ping** - Modificați `ping_interval` și `ping_timeout` la valori mai potrivite.
2. **Implementați o strategie de reconnect** - Asigurați-vă că folosiți logica de reconectare din bibliotecă.
3. **Verificați stabilitatea rețelei** - Probleme de rețea pot cauza deconectări frecvente.
4. **Limitați numărul de conexiuni** - WhatsApp poate limita numărul de sesiuni active simultan.

## Erori de autentificare

### Autentificarea eșuează constant

**Simptome:**
- Eroare `AuthenticationError: Autentificare eșuată`
- Nu se primește niciun challenge de autentificare

**Soluții:**
1. **Verificați credentialele** - Asigurați-vă că numărul de telefon este în format corect.
2. **Folosiți autentificarea QR/pairing code** - Încercați metoda alternativă de autentificare.
3. **Verificați limitele de rate** - WhatsApp poate limita încercările de autentificare. Așteptați înainte de a reîncerca.
4. **Actualizați User-Agent** - Folosiți un User-Agent actual pentru browser.

### Probleme cu codul de împerechere (pairing code)

**Simptome:**
- Nu se primește codul pe telefon
- Eroare la procesarea codului introdus

**Soluții:**
1. **Verificați formatarea numărului** - Numărul de telefon trebuie să includă codul țării.
2. **Verificați eligibilitatea** - Nu toate numerele pot primi coduri de împerechere.
3. **Așteptați mai mult** - Poate dura până la un minut primirea codului.
4. **Verificați implementarea răspunsului la challenge** - Asigurați-vă că răspunsul la challenge este calculat corect.

## Probleme cu trimiterea mesajelor

### Mesajele nu sunt trimise

**Simptome:**
- Funcția `send_text_message()` nu generează erori dar mesajul nu ajunge la destinatar
- Nicio confirmare de primire nu este recepționată

**Soluții:**
1. **Verificați formatul destinatarului** - Asigurați-vă că numărul de telefon sau JID-ul este corect.
2. **Verificați autentificarea** - Asigurați-vă că sunteți autentificat înainte de a trimite mesaje.
3. **Verificați formatul mesajului** - Asigurați-vă că structura mesajului respectă formatul actual al WhatsApp.
4. **Captați și analizați traficul** - Folosiți instrumente de analiză a traficului pentru a vedea ce se trimite efectiv.

### Erori la trimiterea mesajelor media

**Simptome:**
- Eroare `MediaError` la încărcarea fișierelor
- Media se încarcă dar nu este vizibilă pentru destinatar

**Soluții:**
1. **Verificați dimensiunea fișierului** - WhatsApp are limite pentru dimensiunea fișierelor.
2. **Verificați formatul fișierului** - Asigurați-vă că formatul este suportat de WhatsApp.
3. **Verificați implementarea încărcării** - Asigurați-vă că urmați protocolul corect pentru încărcarea fișierelor.
4. **Testați cu fișiere simple** - Începeți cu imagini mici pentru a verifica funcționalitatea de bază.

## Erori de criptare

### Probleme cu stabilirea sesiunii criptate

**Simptome:**
- Eroare `EncryptionError: Nu s-a putut stabili o sesiune criptată`
- Mesajele sunt respinse din cauza criptării inadecvate

**Soluții:**
1. **Verificați implementarea X3DH** - Asigurați-vă că protocolul X3DH este implementat corect.
2. **Generați chei noi** - Probleme cu cheile existente pot cauza erori de sesiune.
3. **Verificați implementarea Double Ratchet** - Asigurați-vă că ratchet-ul este actualizat corect.
4. **Folosiți biblioteci verificate** - Considerați utilizarea unei biblioteci Signal verificate.

### Erori la decriptarea mesajelor primite

**Simptome:**
- Eroare `EncryptionError: Nu s-a putut decripta mesajul`
- Mesajele primite apar corupte sau ilizibile

**Soluții:**
1. **Verificați starea sesiunii** - Asigurați-vă că starea sesiunii este corect menținută.
2. **Gestionați cheile de sesiune** - Implementați corect stocarea și actualizarea cheilor.
3. **Verificați sincronizarea** - Asigurați-vă că indexurile mesajelor sunt sincronizate.
4. **Implementați recuperarea mesajelor** - Includeți logica pentru recuperarea mesajelor pierdute.

## Probleme cu fișiere media

### Încărcarea fișierelor eșuează

**Simptome:**
- Eroare `MediaError: Încărcarea a eșuat`
- Timeout la încercarea de a încărca fișiere media

**Soluții:**
1. **Verificați dimensiunea** - Reduceți dimensiunea fișierelor mari.
2. **Verificați conexiunea** - Asigurați-vă că aveți suficientă lățime de bandă.
3. **Verificați endpoint-urile** - Asigurați-vă că folosiți URL-urile corecte pentru încărcare.
4. **Implementați încărcarea în chunk-uri** - Divizați fișierele mari în părți mai mici.

### Descărcarea media eșuează

**Simptome:**
- Nu se pot descărca atașamentele media din mesaje
- Erori la deschiderea URL-urilor media

**Soluții:**
1. **Verificați URL-urile de descărcare** - Asigurați-vă că URL-urile de media sunt corecte.
2. **Verificați criptarea media** - Media sunt de obicei criptate separat.
3. **Verificați autorizarea** - Asigurați-vă că aveți permisiunile necesare pentru descărcare.
4. **Implementați retry logic** - Adăugați logică de reîncercare pentru descărcări eșuate.

## Actualizarea bibliotecii

### Compatibilitate cu versiuni noi de WhatsApp

**Simptome:**
- Biblioteca nu mai funcționează după o actualizare WhatsApp
- Erori noi la conectare sau autentificare

**Soluții:**
1. **Actualizați constantele** - Preluați versiunile noi din WhatsApp Web.
2. **Analizați traficul** - Identificați schimbările de protocol.
3. **Verificați endpoint-urile** - Asigurați-vă că URL-urile și endpoint-urile sunt actuale.
4. **Urmăriți comunitățile** - Verificați forumurile și repo-urile pentru actualizări.

### Tranziția la versiuni noi ale bibliotecii

**Simptome:**
- Cod care funcționa cu versiuni anterioare nu mai funcționează
- Erori la migrarea la versiuni noi

**Soluții:**
1. **Citiți documentația de migrare** - Consultați ghidurile de upgrade.
2. **Actualizați gradual** - Testați fiecare schimbare separat.
3. **Verificați modificările breaking** - Atenție la schimbările de API.
4. **Testați extensiv** - Testați toate funcționalitățile după upgrade.

## Diagnostic și raportare

### Colectarea informațiilor pentru debugging

Pentru a diagnostica problemele sau a raporta bug-uri, colectați următoarele informații:

1. **Logs complete** - Activați logging-ul în modul DEBUG.
2. **Versiunea bibliotecii** - Specificați versiunea Bocksup și Python.
3. **Stacktrace-uri** - Includeți stacktrace-urile complete pentru erori.
4. **Pași de reproducere** - Descrieți exact cum se poate reproduce problema.
5. **Capturi de trafic** - Dacă este posibil, includeți capturi de trafic WebSocket.

### Utilizarea modulului de testare

Biblioteca include modulul `test_server_connection.py` pentru diagnosticare:

```python
import asyncio
from bocksup import test_server_connection

async def run_diagnostic():
    # Rulați testul de diagnosticare
    results = await test_server_connection()
    
    # Analizați rezultatele
    print("Rezultate diagnosticare:")
    print(f"- Conexiune: {'OK' if results['connection'] else 'EȘEC'}")
    print(f"- Handshake: {'OK' if results['handshake'] else 'EȘEC'}")
    
    # Verificați erorile
    if results['errors']:
        print("Erori detectate:")
        for error in results['errors']:
            print(f"  - {error}")
    else:
        print("Nicio eroare detectată")

# Rulați diagnosticarea
asyncio.run(run_diagnostic())
```

### Raportarea bug-urilor

Când raportați bug-uri pe GitHub:

1. **Verificați problemele existente** - Problema dvs. poate fi deja raportată.
2. **Folosiți șablonul de bug report** - Completați toate câmpurile relevante.
3. **Includeți minimum reproducible example** - Furnizați cod minim pentru a reproduce problema.
4. **Specificați versiunile** - Menționați versiunile de Python, Bocksup și sistem.
5. **Descrieți comportamentul așteptat** - Explicați ce ar trebui să se întâmple vs. ce se întâmplă.

---

**Notă:** WhatsApp își actualizează frecvent protocolul, așa că unele probleme pot fi cauzate de schimbări recente în API-ul lor. Verificați întotdeauna dacă folosiți cea mai recentă versiune a bibliotecii.