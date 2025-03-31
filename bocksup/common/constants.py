"""
Constante utilizate în biblioteca Bocksup.
"""

# Versiuni și identificatori WhatsApp
DEFAULT_CLIENT_VERSION = "2.2315.6"
WA_PROTOCOL_VERSION = "2"
DEFAULT_PLATFORM = "android"
DEFAULT_USER_AGENT = "WhatsApp/2.2315.6 Android/13"

# URL-uri server WhatsApp
WA_WEB_URL = "https://web.whatsapp.com"
WA_WEBSOCKET_URL = "wss://web.whatsapp.com/ws"

# Timeouts și intervale
CONNECTION_TIMEOUT = 30  # secunde
KEEP_ALIVE_INTERVAL = 25  # secunde

# Marker binar WebSocket
WS_BINARY_PREFIX = b"\x00\x00\x00\x00"
WS_BINARY_SUFFIX = b"\x00"

# Tipuri de mesaje binare
BINARY_TYPE_JSON = 1
BINARY_TYPE_BINARY = 2
BINARY_TYPE_MESSAGE = 3
BINARY_TYPE_HANDSHAKE = 4
BINARY_TYPE_PAIRING = 5
BINARY_TYPE_CHALLENGE = 6
BINARY_TYPE_RESPONSE = 7

# Stări de conexiune
CONN_STATE_DISCONNECTED = "disconnected"
CONN_STATE_CONNECTING = "connecting"
CONN_STATE_CONNECTED = "connected"
CONN_STATE_AUTHENTICATED = "authenticated"
CONN_STATE_ERROR = "error"

# Metode de autentificare
AUTH_METHOD_SMS = "sms"
AUTH_METHOD_VOICE = "voice"
AUTH_METHOD_QR = "qr"

# Tipuri de mesaje
MSG_TYPE_TEXT = "text"
MSG_TYPE_IMAGE = "image"
MSG_TYPE_AUDIO = "audio"
MSG_TYPE_VIDEO = "video"
MSG_TYPE_DOCUMENT = "document"
MSG_TYPE_LOCATION = "location"
MSG_TYPE_CONTACT = "contact"
MSG_TYPE_STICKER = "sticker"

# Stări mesaje
MSG_STATUS_PENDING = "pending"
MSG_STATUS_SENT = "sent"
MSG_STATUS_DELIVERED = "delivered"
MSG_STATUS_READ = "read"
MSG_STATUS_ERROR = "error"

# Stări prezență
PRESENCE_AVAILABLE = "available"
PRESENCE_UNAVAILABLE = "unavailable"
PRESENCE_TYPING = "typing"
PRESENCE_RECORDING = "recording"