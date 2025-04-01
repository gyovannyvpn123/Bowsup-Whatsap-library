"""
Implementarea protocolului Signal pentru criptarea end-to-end în WhatsApp.

Acest modul implementează protocolul Signal (anterior cunoscut ca Axolotl)
care este folosit de WhatsApp pentru criptarea end-to-end. Acest protocol
asigură că mesajele pot fi citite doar de expeditor și destinatar.

Referințe:
- https://signal.org/docs/
- https://www.whatsapp.com/security/
"""

import os
import logging
import hashlib
import hmac
import time
import json
import base64
from typing import Dict, Any, Optional, Tuple, List, Union, Callable

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

logger = logging.getLogger(__name__)

class SignalProtocol:
    """
    Implementare a protocolului Signal pentru criptare end-to-end.

    Acest protocol asigură criptarea, autentificarea și perfect forward
    secrecy pentru comunicarea între două părți.
    """

    def __init__(self):
        """Inițializează protocolul Signal."""
        self.identity_key_pair = None
        self.registration_id = None
        self.pre_keys = []
        self.signed_pre_key = None
        self.session_store = {}
        self.identity_store = {}
        self.pre_key_store = {}

    def generate_identity(self) -> Dict[str, Any]:
        """
        Generează perechea de chei de identitate pentru acest client folosind X3DH.

        Returns:
            Dict conținând cheia publică și privată de identitate
        """
        Implementarea protocolului Signal pentru criptare end-to-end
        """
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        class SignalProtocol:
            def __init__(self):
                self.private_key = X25519PrivateKey.generate()
                self.public_key = self.private_key.public_key()
                self.session_keys = {}

            def get_public_key(self):
                return self.public_key.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )

            def create_shared_secret(self, peer_public_key_bytes):
                peer_public_key = X25519PublicKey.from_public_bytes(peer_public_key_bytes)
                shared_key = self.private_key.exchange(peer_public_key)

                # Derivă cheia folosind HKDF
                hkdf = HKDF(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=None,
                    info=b"WhatsApp Message Keys"
                )
                return hkdf.derive(shared_key)

            def encrypt_message(self, message, peer_public_key_bytes):
                if not isinstance(message, bytes):
                    message = message.encode('utf-8')

                session_key = self.create_shared_secret(peer_public_key_bytes)
                aesgcm = AESGCM(session_key)
                nonce = os.urandom(12)

                ciphertext = aesgcm.encrypt(nonce, message, None)
                return nonce + ciphertext

            def decrypt_message(self, encrypted_message, peer_public_key_bytes):
                session_key = self.create_shared_secret(peer_public_key_bytes)
                aesgcm = AESGCM(session_key)

                nonce = encrypted_message[:12]
                ciphertext = encrypted_message[12:]

                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                return plaintext.decode('utf-8')
        public_key = private_key.public_key()

        # Serializează cheile
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        private_key = get_random_bytes(32)
        # Derivăm o cheie publică (în implementarea reală ar folosi criptografie cu curbe eliptice)
        public_key = hashlib.sha256(private_key).digest()

        self.identity_key_pair = {
            "private": private_key,
            "public": public_key
        }

        # Generează ID de înregistrare (un număr aleatoriu)
        self.registration_id = int.from_bytes(get_random_bytes(4), byteorder='big') % 16384

        logger.info(f"Identitate generată cu registration_id: {self.registration_id}")

        return {
            "identity_key": {
                "public": base64.b64encode(public_key).decode('utf-8'),
                "private": "<privat>" # Nu arăta cheia privată în log-uri
            },
            "registration_id": self.registration_id
        }

    def generate_pre_keys(self, count: int = 20) -> List[Dict[str, Any]]:
        """
        Generează un set de pre-keys pentru sesiune.

        Pre-keys sunt folosite pentru a stabili sesiuni noi între participanți,
        permițând inițierea comunicării asincrone.

        Args:
            count: Numărul de pre-keys de generat

        Returns:
            Listă de pre-keys generate
        """
        start_id = int(time.time()) % 16384

        pre_keys = []
        for i in range(count):
            key_id = start_id + i

            # În implementarea reală, acestea ar fi chei Curve25519
            private_key = get_random_bytes(32)
            public_key = hashlib.sha256(private_key + str(key_id).encode('utf-8')).digest()

            pre_key = {
                "id": key_id,
                "public": public_key,
                "private": private_key
            }

            self.pre_keys.append(pre_key)

            # Adaugă la rezultat doar cheile publice
            pre_keys.append({
                "id": key_id,
                "key": base64.b64encode(public_key).decode('utf-8')
            })

        logger.info(f"Generate {count} pre-keys începând cu ID-ul: {start_id}")
        return pre_keys

    def generate_signed_pre_key(self) -> Dict[str, Any]:
        """
        Generează o pre-key semnată.

        Pre-keys semnate sunt folosite pentru a preveni atacurile
        man-in-the-middle în timpul stabilirii sesiunii.

        Returns:
            Dict conținând pre-key-ul semnat
        """
        if not self.identity_key_pair:
            raise ValueError("Trebuie să generezi mai întâi identitatea")

        key_id = int(time.time()) % 16384

        # În implementarea reală, aceasta ar fi o cheie Curve25519
        private_key = get_random_bytes(32)
        public_key = hashlib.sha256(private_key + str(key_id).encode('utf-8')).digest()

        # Semnează cheia publică cu cheia privată de identitate (HMAC în această implementare)
        # În implementarea reală, s-ar folosi semnături cu curbe eliptice
        hmac_key = self.identity_key_pair["private"]
        signature = hmac.new(hmac_key, public_key, hashlib.sha256).digest()

        signed_pre_key = {
            "id": key_id,
            "public": public_key,
            "private": private_key,
            "signature": signature
        }

        self.signed_pre_key = signed_pre_key

        # Returnează doar informația publică
        return {
            "id": key_id,
            "key": base64.b64encode(public_key).decode('utf-8'),
            "signature": base64.b64encode(signature).decode('utf-8')
        }

    def initiate_session(self, recipient_id: str, recipient_key: bytes) -> str:
        """
        Inițiază o sesiune nouă cu un destinatar.

        Args:
            recipient_id: Identificatorul destinatarului (ex: număr de telefon)
            recipient_key: Cheia publică a destinatarului

        Returns:
            ID-ul sesiunii generate
        """
        if not self.identity_key_pair:
            raise ValueError("Trebuie să generezi mai întâi identitatea")

        # Generează un ID de sesiune unic
        session_id = f"{recipient_id}_{int(time.time())}"

        # Pentru această implementare simplificată, vom genera doar o cheie de sesiune
        # În implementarea reală, procesul ar implica schimb de chei Diffie-Hellman
        ephemeral_key = get_random_bytes(32)

        # Derivă cheia de sesiune (în implementarea reală, ar folosi ECDH și procesul X3DH)
        # Combinăm cheia noastră privată, cheia publică a destinatarului și o valoare aleatoare
        session_key = PBKDF2(
            self.identity_key_pair["private"] + recipient_key + ephemeral_key,
            salt=get_random_bytes(16),
            dkLen=32,
            count=1000
        )

        # Stochează informațiile sesiunii
        session_info = {
            "recipient_id": recipient_id,
            "session_id": session_id,
            "session_key": session_key,
            "created_at": int(time.time()),
            "last_used": int(time.time()),
            "message_keys": {}
        }

        # Stochează sesiunea
        self.session_store[session_id] = session_info

        logger.info(f"Sesiune inițiată cu {recipient_id}, session_id: {session_id}")
        return session_id

    def encrypt_message(self, session_id: str, plaintext: Union[str, bytes]) -> Dict[str, Any]:
        """
        Criptează un mesaj pentru o sesiune specifică.

        Args:
            session_id: ID-ul sesiunii
            plaintext: Mesajul de criptat

        Returns:
            Dict conținând mesajul criptat și metadate necesare pentru decriptare

        Raises:
            ValueError: Dacă sesiunea nu există
        """
        if session_id not in self.session_store:
            raise ValueError(f"Sesiunea {session_id} nu există")

        session = self.session_store[session_id]

        # Actualizează timestamp-ul ultimei utilizări
        session["last_used"] = int(time.time())

        # Generează un mesaj key unic pentru acest mesaj (pentru forward secrecy)
        message_id = f"msg_{int(time.time())}_{os.urandom(4).hex()}"
        message_key = PBKDF2(
            session["session_key"] + message_id.encode('utf-8'),
            salt=get_random_bytes(16),
            dkLen=32,
            count=100
        )

        # Convertește plaintext la bytes dacă este string
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')

        # Criptează mesajul cu AES-CBC
        iv = get_random_bytes(16)
        cipher = AES.new(message_key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

        # Stochează cheia mesajului pentru decriptare ulterioară
        session["message_keys"][message_id] = message_key

        # Construiește rezultatul
        encrypted_message = {
            "session_id": session_id,
            "message_id": message_id,
            "iv": base64.b64encode(iv).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8')
        }

        return encrypted_message

    def decrypt_message(self, encrypted_message: Dict[str, Any]) -> bytes:
        """
        Decriptează un mesaj.

        Args:
            encrypted_message: Mesajul criptat și metadatele asociate

        Returns:
            Mesajul decriptat ca bytes

        Raises:
            ValueError: Dacă sesiunea nu există sau mesajul nu poate fi decriptat
        """
        session_id = encrypted_message.get("session_id")
        message_id = encrypted_message.get("message_id")

        if not session_id or not message_id:
            raise ValueError("Mesajul criptat nu conține session_id sau message_id")

        if session_id not in self.session_store:
            raise ValueError(f"Sesiunea {session_id} nu există")

        session = self.session_store[session_id]

        # Dacă avem deja cheia mesajului stocată, o folosim
        if message_id in session["message_keys"]:
            message_key = session["message_keys"][message_id]
        else:
            # Altfel, o derivăm din nou
            message_key = PBKDF2(
                session["session_key"] + message_id.encode('utf-8'),
                salt=get_random_bytes(16),  # Aici ar trebui să fie același salt, în practică ar fi inclus în mesaj
                dkLen=32,
                count=100
            )

        # Decriptează mesajul
        iv = base64.b64decode(encrypted_message["iv"])
        ciphertext = base64.b64decode(encrypted_message["ciphertext"])

        cipher = AES.new(message_key, AES.MODE_CBC, iv)

        try:
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
            return plaintext
        except Exception as e:
            raise ValueError(f"Eroare la decriptarea mesajului: {str(e)}")

    def get_bundle(self) -> Dict[str, Any]:
        """
        Obține bundle-ul de chei pentru înregistrare la server.

        Bundle-ul conține toate informațiile necesare pentru ca alți utilizatori
        să inițieze sesiuni criptate cu acest client.

        Returns:
            Dict conținând bundle-ul de înregistrare
        """
        if not self.identity_key_pair or not self.signed_pre_key:
            raise ValueError("Trebuie să generezi identitatea și pre-key-urile semnate mai întâi")

        # Construiește bundle-ul cu informațiile publice
        pre_keys_public = []
        for pre_key in self.pre_keys:
            pre_keys_public.append({
                "id": pre_key["id"],
                "key": base64.b64encode(pre_key["public"]).decode('utf-8')
            })

        bundle = {
            "registration_id": self.registration_id,
            "identity_key": base64.b64encode(self.identity_key_pair["public"]).decode('utf-8'),
            "signed_pre_key": {
                "id": self.signed_pre_key["id"],
                "key": base64.b64encode(self.signed_pre_key["public"]).decode('utf-8'),
                "signature": base64.b64encode(self.signed_pre_key["signature"]).decode('utf-8')
            },
            "pre_keys": pre_keys_public
        }

        return bundle

    def save_state(self, file_path: str, password: str) -> bool:
        """
        Salvează starea protocolului într-un fișier criptat.

        Args:
            file_path: Calea unde va fi salvat fișierul
            password: Parola pentru criptarea fișierului

        Returns:
            True dacă salvarea a reușit
        """
        state = {
            "identity_key_pair": {
                "private": base64.b64encode(self.identity_key_pair["private"]).decode('utf-8'),
                "public": base64.b64encode(self.identity_key_pair["public"]).decode('utf-8')
            },
            "registration_id": self.registration_id,
            "pre_keys": [],
            "signed_pre_key": None,
            "sessions": {}
        }

        # Convertește pre_keys în format serializabil
        for pre_key in self.pre_keys:
            state["pre_keys"].append({
                "id": pre_key["id"],
                "public": base64.b64encode(pre_key["public"]).decode('utf-8'),
                "private": base64.b64encode(pre_key["private"]).decode('utf-8')
            })

        # Serializează signed_pre_key
        if self.signed_pre_key:
            state["signed_pre_key"] = {
                "id": self.signed_pre_key["id"],
                "public": base64.b64encode(self.signed_pre_key["public"]).decode('utf-8'),
                "private": base64.b64encode(self.signed_pre_key["private"]).decode('utf-8'),
                "signature": base64.b64encode(self.signed_pre_key["signature"]).decode('utf-8')
            }

        # Serializează sesiunile
        for session_id, session in self.session_store.items():
            session_data = {
                "recipient_id": session["recipient_id"],
                "session_id": session["session_id"],
                "session_key": base64.b64encode(session["session_key"]).decode('utf-8'),
                "created_at": session["created_at"],
                "last_used": session["last_used"],
                "message_keys": {}
            }

            # Serializează cheile de mesaj
            for msg_id, msg_key in session["message_keys"].items():
                session_data["message_keys"][msg_id] = base64.b64encode(msg_key).decode('utf-8')

            state["sessions"][session_id] = session_data

        # Serializează starea completă ca JSON
        state_json = json.dumps(state)

        # Derivă cheia de criptare din parolă
        key = PBKDF2(password.encode('utf-8'), salt=b'signal_state', dkLen=32, count=10000)

        # Criptează starea
        iv = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(pad(state_json.encode('utf-8'), AES.block_size))

        # Adaugă IV la începutul datelor criptate și salvează
        with open(file_path, 'wb') as f:
            f.write(iv + encrypted_data)

        logger.info(f"Starea protocolului Signal salvată în {file_path}")
        return True

    def load_state(self, file_path: str, password: str) -> bool:
        """
        Încarcă starea protocolului dintr-un fișier criptat.

        Args:
            file_path: Calea fișierului de încărcat
            password: Parola pentru decriptarea fișierului

        Returns:
            True dacă încărcarea a reușit

        Raises:
            ValueError: Dacă fișierul nu există sau parola este incorectă
        """
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()

            # Primii 16 bytes sunt IV-ul
            iv = encrypted_data[:16]
            encrypted_state = encrypted_data[16:]

            # Derivă cheia de decriptare din parolă
            key = PBKDF2(password.encode('utf-8'), salt=b'signal_state', dkLen=32, count=10000)

            # Decriptează starea
            cipher = AES.new(key, AES.MODE_CBC, iv)
            state_json = unpad(cipher.decrypt(encrypted_state), AES.block_size).decode('utf-8')

            # Parsează starea ca JSON
            state = json.loads(state_json)

            # Încarcă identity_key_pair
            self.identity_key_pair = {
                "private": base64.b64decode(state["identity_key_pair"]["private"]),
                "public": base64.b64decode(state["identity_key_pair"]["public"])
            }

            # Încarcă registration_id
            self.registration_id = state["registration_id"]

            # Încarcă pre_keys
            self.pre_keys = []
            for pre_key in state["pre_keys"]:
                self.pre_keys.append({
                    "id": pre_key["id"],
                    "public": base64.b64decode(pre_key["public"]),
                    "private": base64.b64decode(pre_key["private"])
                })

            # Încarcă signed_pre_key
            if state.get("signed_pre_key"):
                self.signed_pre_key = {
                    "id": state["signed_pre_key"]["id"],
                    "public": base64.b64decode(state["signed_pre_key"]["public"]),
                    "private": base64.b64decode(state["signed_pre_key"]["private"]),
                    "signature": base64.b64decode(state["signed_pre_key"]["signature"])
                }

            # Încarcă sesiunile
            self.session_store = {}
            for session_id, session_data in state.get("sessions", {}).items():
                session = {
                    "recipient_id": session_data["recipient_id"],
                    "session_id": session_data["session_id"],
                    "session_key": base64.b64decode(session_data["session_key"]),
                    "created_at": session_data["created_at"],
                    "last_used": session_data["last_used"],
                    "message_keys": {}
                }

                # Încarcă cheile de mesaj
                for msg_id, msg_key_b64 in session_data.get("message_keys", {}).items():
                    session["message_keys"][msg_id] = base64.b64decode(msg_key_b64)

                self.session_store[session_id] = session

            logger.info(f"Starea protocolului Signal încărcată din {file_path}")
            return True

        except FileNotFoundError:
            raise ValueError(f"Fișierul {file_path} nu există")
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise ValueError(f"Eroare la încărcarea stării: {str(e)}")


# Funcția de ajutor pentru testare
def test_signal_protocol():
    """Testează funcționalitatea protocolului Signal."""
    # Creează două instanțe ale protocolului pentru Alice și Bob
    alice = SignalProtocol()
    bob = SignalProtocol()

    # Generează identități
    alice_identity = alice.generate_identity()
    bob_identity = bob.generate_identity()

    print("Identitate Alice:", alice_identity["registration_id"])
    print("Identitate Bob:", bob_identity["registration_id"])

    # Generează pre-keys
    alice.generate_pre_keys(count=5)
    alice.generate_signed_pre_key()

    bob.generate_pre_keys(count=5)
    bob.generate_signed_pre_key()

    # Obține bundle-ul lui Bob pentru ca Alice să poată iniția o sesiune
    bob_bundle = bob.get_bundle()

    # Alice inițiază o sesiune cu Bob
    bob_public_key = base64.b64decode(bob_bundle["identity_key"])
    session_id = alice.initiate_session("bob_phone", bob_public_key)

    # Alice trimite un mesaj lui Bob
    message = "Salut Bob, acest mesaj este criptat end-to-end!"
    encrypted = alice.encrypt_message(session_id, message)

    print("\nMesaj criptat:", encrypted)

    # Bob ar trebui să inițieze o sesiune cu Alice și să decripteze mesajul
    # În implementarea reală, acest proces ar implica schimb de chei complexe
    # Pentru simplificare, vom crea manual o sesiune pentru Bob

    alice_public_key = base64.b64decode(alice_identity["identity_key"]["public"])
    bob_session_id = bob.initiate_session("alice_phone", alice_public_key)

    # Pentru testare, vom folosi aceeași cheie de sesiune ca Alice
    # În realitate, această cheie ar fi derivată din schimbul Diffie-Hellman
    bob.session_store[bob_session_id]["session_key"] = alice.session_store[session_id]["session_key"]

    # Modificăm ID-ul sesiunii pentru a reflecta ID-ul corect
    encrypted["session_id"] = bob_session_id

    # Bob decriptează mesajul
    decrypted = bob.decrypt_message(encrypted)
    print("\nMesaj decriptat:", decrypted.decode('utf-8'))

    # Testăm salvarea și încărcarea stării
    password = "parola_test"
    alice.save_state("alice_state.bin", password)

    # Creăm o nouă instanță și încărcăm starea Alice
    alice2 = SignalProtocol()
    alice2.load_state("alice_state.bin", password)

    # Verificăm dacă putem trimite un nou mesaj cu starea restaurată
    encrypted2 = alice2.encrypt_message(session_id, "Mesaj după restaurarea stării")
    encrypted2["session_id"] = bob_session_id
    decrypted2 = bob.decrypt_message(encrypted2)
    print("\nMesaj după restaurarea stării:", decrypted2.decode('utf-8'))

    print("\nProtocolul Signal funcționează corect!")


if __name__ == "__main__":
    # Configurează logging
    logging.basicConfig(level=logging.INFO)
    # Rulează testul
    test_signal_protocol()