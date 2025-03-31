"""
Constants used throughout the Bocksup library.
"""

# Server information
WHATSAPP_SERVER = 'web.whatsapp.com'
WHATSAPP_PORT = 443
WHATSAPP_WEBSOCKET_URL = 'wss://web.whatsapp.com/ws/chat'
WHATSAPP_WEBSOCKET_ORIGIN = 'https://web.whatsapp.com'

# Media server
WHATSAPP_MEDIA_SERVER = 'mmg.whatsapp.net'
WHATSAPP_MEDIA_UPLOAD_SERVER = 'upload.whatsapp.net'
WHATSAPP_MEDIA_DOWNLOAD_SERVER = 'cdn.whatsapp.net'

# Protocol details
PROTOCOL_VERSION = '2.2412.54'
CLIENT_VERSION = '2.2412.54'
USER_AGENT = f'WhatsApp/{CLIENT_VERSION} Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
WA_SECRET_BUNDLE = 'BD3YXSsQmIiuQ/QQPVXnKQ=='  # This is a placeholder, in real implementation this should come from configuration

# Connection parameters
CONNECT_TIMEOUT = 20  # seconds
READ_TIMEOUT = 45  # seconds
PING_INTERVAL = 25  # seconds
MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds

# WebSocket frame related
WS_NORMAL_CLOSURE = 1000
WS_GOING_AWAY = 1001
WS_NO_STATUS_RCVD = 1005

# Protocol message tags
TAG_MESSAGE = 'message'
TAG_RECEIPT = 'receipt'
TAG_PRESENCE = 'presence'
TAG_GROUP = 'group'
TAG_NOTIFICATION = 'notification'
TAG_CALL = 'call'
TAG_CHAT = 'chat'
TAG_RESPONSE = 'response'
TAG_ERROR = 'error'
TAG_STREAM = 'stream'

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
