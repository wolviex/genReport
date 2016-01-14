__VERSION__ = '0.0.1'

MagicKey = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

handshake = "HTTP/1.1 101 Switching Protocols\r\n"
handshake += "Upgrade: websocket\r\n"
handshake += "Connection: Upgrade\r\n"
handshake += "Sec-WebSocket-Accept: {}\r\n\r\n"

from .ws_server import Server
from .HTML5App import HTML5App
from .serverBuilder import serverBuilder
import PacketHandler


class ObjectType:
	_int,_float,_str,_func,_element,_array = [chr(x) for x in range(1,7)]
	