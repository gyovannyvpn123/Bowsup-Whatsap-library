"""
Constants used throughout the Bocksup library.
"""

# Server information
WHATSAPP_SERVER = 'e1.whatsapp.net'
WHATSAPP_PORT = 443
WHATSAPP_WEBSOCKET_URL = 'wss://web.whatsapp.com/ws'

# Media server
WHATSAPP_MEDIA_SERVER = 'media.whatsapp.net'

# Protocol details
PROTOCOL_VERSION = '0.4.2412'
USER_AGENT = f'WhatsApp/2.24.12 Bocksup/{PROTOCOL_VERSION}'

# Connection parameters
CONNECT_TIMEOUT = 10  # seconds
READ_TIMEOUT = 30  # seconds
PING_INTERVAL = 60  # seconds

# Message types
MESSAGE_TYPE_TEXT = 1
MESSAGE_TYPE_MEDIA = 2
MESSAGE_TYPE_LOCATION = 3
MESSAGE_TYPE_CONTACT = 4
MESSAGE_TYPE_STATUS = 5

# Media types
MEDIA_TYPE_IMAGE = 1
MEDIA_TYPE_VIDEO = 2
MEDIA_TYPE_AUDIO = 3
MEDIA_TYPE_DOCUMENT = 4
MEDIA_TYPE_STICKER = 5
MEDIA_TYPE_GIF = 6

# Status types
STATUS_TYPE_AVAILABLE = 'available'
STATUS_TYPE_UNAVAILABLE = 'unavailable'
STATUS_TYPE_TYPING = 'composing'
STATUS_TYPE_RECORDING = 'recording'
STATUS_TYPE_PAUSED = 'paused'

# Group chat constants
GROUP_CREATE = 'create'
GROUP_SUBJECT = 'subject'
GROUP_ADD = 'add'
GROUP_REMOVE = 'remove'
GROUP_LEAVE = 'leave'
GROUP_PHOTO = 'photo'

# Authentication related
AUTH_REQUIRED = 'auth'
AUTH_SUCCESS = 'success'
AUTH_FAILURE = 'failure'

# Message related
MESSAGE_RECEIPT_SERVER = 'server'
MESSAGE_RECEIPT_DEVICE = 'device'
MESSAGE_RECEIPT_READ = 'read'
MESSAGE_RECEIPT_PLAYED = 'played'

# Signal protocol related
AXO_INIT = 'init'
AXO_KEY_EXCHANGE = 'key'
AXO_MESSAGE = 'msg'
