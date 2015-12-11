import socket
import thread
import websocket
import websocket.Events
import time
import hashlib
import base64
import re

class wsClient(object):
	s = None
	address = None
	handshake = None
	key = None
	magickey = None
	stillRecv = False
	packet = None
	send_packet = None

	def __init__(self,arg):
		self.s = arg[0]
		self.address = arg[1]

	def genKey(self):
		hash = hashlib.sha1(self.key.rstrip() + websocket.MagicKey)
		self.magickey = base64.standard_b64encode(hash.digest())

class Server(object):
	"""Hosts a websocket server"""

	logCommands = False

	s = None
	ip = None
	port = None
	acceptThread = None
	packetHandler = None
	parent = None
	connections = []

	onConnect = []
	onDisconnect = []
	onRecieve = []

	def __init__(self,ip,port):

		self.ip = ip
		self.port = port

		self.packetHandler = websocket.PacketHandler.PacketHandler(self)

	def acceptConnections(self):
		try:
			self.s.listen(20)
			c = self.s.accept()
			if c is not None:
				client = wsClient(c)
				self.connections.append(client)
				for f in self.onConnect:
					f(self.connections[-1])
		except socket.error as e:
			pass

	def getData(self):
		for usr in self.connections:
			try:
				data = usr.s.recv(4096)
				self.packetHandler.handleData(usr,data)
			except socket.error:
				pass


	def startServer(self):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s.bind((self.ip,self.port))
		self.s.setblocking(False)
		print "Server started"

		while True:
			self.acceptConnections()
			self.packetHandler.update()
			time.sleep(0.5)

	def clientDisconnect(self, packet):
		print "{} Disconnected".format(packet.usr.address[0])
		id = self.connections.index(packet.usr)
		packet.usr.s.close()
		self.connections.pop(id)

	def recievePacket(self, packet):
		cmdSearch = re.search(r"/([a-zA-Z0-9_]*?)(?:\s|$)",packet.decoded)
		if cmdSearch is not None:
			if self.parent is not None:
				fname = "cmd_{}".format(cmdSearch.group(1))
				f = getattr(self.parent,fname)
				if f is not None:
					f(packet)
					if not self.logCommands:
						return
		if len(packet.decoded) == 2:
			if [ord(x) for x in packet.decoded] == [3,233]:
				self.clientDisconnect(packet)
				for f in self.onDisconnect:										
					f(packet)
				
			

		for f in self.onRecieve:
			f(packet)

	def close(self):
		
		self.s.shutdown(1)
		self.s.close()



