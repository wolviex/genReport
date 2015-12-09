__VERSION__ = '0.0.1'

MagicKey = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

handshake = "HTTP/1.1 101 Switching Protocols\r\n"
handshake += "Upgrade: websocket\r\n"
handshake += "Connection: Upgrade\r\n"
handshake += "Sec-WebSocket-Accept: {}\r\n\r\n"

from .ws_server import Server
import PacketHandler