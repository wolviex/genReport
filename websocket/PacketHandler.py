import websocket
import socket
import binascii
import numpy as np
import select
import re
global curPacketHandler


def readIntBytes(b,offset=0,mask=False):
	byte = ord(b[offset])

	if mask:
		byte = byte & 0x7f

	if byte > 127:
		print("Error in getMessageLength!");
		return [-1,-1]
	

	if (byte == 126):
		return [(ord(b[offset + 1]) << 8) | ord(b[offset + 2]),2];
	
	elif (byte == 127):
		return [(ord(b[offset + 1]) << 24) | (ord(b[offset + 2]) << 16) | (ord(b[offset + 3]) << 8) | ord(b[offset + 4]),4];
	
	else:
		return [byte,0]


def writeLengthBytes(l,max=64):
	encoded = ""
	if l >= 126 and l <= 65535:
		encoded += chr(126)
		encoded += chr((l & (((1<<8)-1)<<8)) >> 8)
		encoded += chr((l & (((1<<8)-1)<<0)) >> 0)
	elif l > 65535:
		if max == 64:
			encoded += chr(127)
			encoded += chr((l & (((1<<8)-1)<<56)) >> 56)
			encoded += chr((l & (((1<<8)-1)<<48)) >> 48)
			encoded += chr((l & (((1<<8)-1)<<40)) >> 40)
			encoded += chr((l & (((1<<8)-1)<<32)) >> 32)
			encoded += chr((l & (((1<<8)-1)<<24)) >> 24)
			encoded += chr((l & (((1<<8)-1)<<16)) >> 16)
			encoded += chr((l & (((1<<8)-1)<<8)) >> 8)
			encoded += chr((l & (((1<<8)-1)<<0)) >> 0)
		elif max == 32:
			encoded += chr(127)
			encoded += chr((l & (((1<<8)-1)<<24)) >> 24)
			encoded += chr((l & (((1<<8)-1)<<16)) >> 16)
			encoded += chr((l & (((1<<8)-1)<<8)) >> 8)
			encoded += chr((l & (((1<<8)-1)<<0)) >> 0)
		else:
			raise Exception("Error. writeLengthBytes max bytes must be either 64 or 32!")

	else:
		encoded += chr(l)	


		
	return encoded	

class arrayWalkClass(object):
	parentWalk = None
	array = None
	size = 0
	def __init__(self,walk=None):
		if walk:
			if isinstance(walk,arrayWalkClass):
				self.parentWalk = walk.parentWalk
				self.array = walk.array
				self.size = walk.size
			elif isinstance(walk,(list,tuple)):
				self.array = walk
				self.size = len(walk)

		

	

class Packet(object):
	length = 0
	l_bytes = 0
	mask = 0
	mask_key = ""
	buf = ""
	opcode = 0
	fin = 0
	handler = None
	usr = None
	message = None
	decoded = ""
	cmds = []
	arrayWalk = arrayWalkClass()

	def newPacket(self):
		self.opcode = 2
		self.fin = 1
		self.mask = 1
		self.buf = ""
		self.decoded = ""
		self.cmds = []
		

	def __init__(self,usr,encoded=""):
		


		self.usr = usr
		
		if len(encoded) <= 0:
			self.newPacket()
			print "Creating new packet"
			return
		self.cmds = []
		self.length,self.l_bytes = readIntBytes(encoded,1,True);	
		self.buf = encoded
		self.mask_key = encoded[2+self.l_bytes:6+self.l_bytes]
		self.mask = ord(encoded[1]) & 0x80
		self.opcode = ord(encoded[0]) & ((1<<4)-1)
		self.fin = ord(encoded[0]) & 0x80
		self.headerLength = 2 + self.l_bytes

		
		print "Packet initialized. Length: {}".format(self.length)

	def readBuf(self, idx,dv):
		
		while (idx < len(dv)):
			objtype = dv[idx]
			
			idx += 1
			truelen = readIntBytes(dv, idx);
			
			idx += 1+truelen[1]

			if objtype == websocket.ObjectType._func:
				re = str(dv[idx:idx+truelen[0]])
				
				a = [re,[]]

				self.cmds.append(a)
				idx += truelen[0]
			
			elif objtype == websocket.ObjectType._str:
				
				re = str(dv[idx:idx+truelen[0]])
				if self.arrayWalk.array is not None:
					self.arrayWalk.array.append(re)				
					while True:	
						if len(self.arrayWalk.array) >= self.arrayWalk.size:
							if self.arrayWalk.parentWalk is not None:
								self.arrayWalk = arrayWalkClass(self.arrayWalk.parentWalk)						
							else:
								self.arrayWalk.array = None
								break			
						else:
							break				
				else:
					self.cmds[-1][1].append(re)
				idx += truelen[0];
			
			elif objtype == websocket.ObjectType._array:
				a = []
			
				if self.arrayWalk.array is not None:
					self.arrayWalk.parentWalk = arrayWalkClass(self.arrayWalk)
					self.arrayWalk.array.append(a)
				else:
					self.cmds[-1][1].append(a)

				self.arrayWalk.array = a		
				self.arrayWalk.size = truelen[0]
				
				
			
			elif objtype == websocket.ObjectType._int:
				self.cmds[-1][1].append(truelen[0])
			elif objtype == websocket.ObjectType._float:
				self.cmds[-1][1].append(float(truelen[0]) / 256.0)
			
		
		
		


	def decode(self):
		decoded = ""
		for i in range(self.length):
			decoded += chr(ord(self.buf[self.headerLength+4+i]) ^ ord(self.mask_key[i%4]))


		if len(decoded) > 2:
			self.readBuf(0,decoded)

		self.decoded = decoded

		
		


	def addHeader(self):
		m = ""
		m += chr((self.fin<<7)|self.opcode)
		m += writeLengthBytes(len(self.buf))
		m += self.buf;

		self.buf = m
		
	def __len__(self):
		return self.length + self.headerLength + 4


	def addCommand(self,cmd, *args):


		self.buf += websocket.ObjectType._func
		self.buf += writeLengthBytes(len(cmd),32)	#Pretty much everything after the initial handshake has to use a 32 bit uint for the size
		self.buf += cmd						#due to javascript bit operations using 32bit ints (max 15.99tb)
		
		self.writeObjects(*args)

		

	def writeObjects(self,*args):
		
		for arg in args:
			if isinstance(arg,(str,np.unicode_)):

				self.buf += websocket.ObjectType._str
				self.buf += writeLengthBytes(len(arg),32)				
				self.buf += str(arg)
			elif isinstance(arg,(list,tuple,np.ndarray)):
				self.buf += websocket.ObjectType._array
				self.buf += writeLengthBytes(len(arg),32)
				for obj in arg:
					self.writeObjects(obj);
			elif isinstance(arg,(int,np.int64)):
				self.buf += websocket.ObjectType._int
				self.buf += writeLengthBytes(arg)
			elif isinstance(arg,(float,)):
				self.buf += websocket.ObjectType._float
				self.buf += writeLengthBytes(int(arg * 256),32)

class PacketHandler(object):

	server = None

	def __init__(self,server):
		global curPacketHandler
		curPacketHandler = self
		self.server = server

	def handleData(self,usr):
		
		data = b""
		while True:
			try:
				d = usr.s.recv(1024)
				data += d
			except:
				break
		
		

			
			
		if not usr.handshake:
			self.tryHandshake(usr,data)
		else:
				
			if len(data) > 0:
				if usr.packet is None:
					usr.packet = Packet(usr,data)	
				else:
					usr.packet.buf += data

				if len(usr.packet.buf) >= len(usr.packet):
					usr.packet.decode()
					if len(usr.packet.decoded) == 2:
						if [ord(x) for x in usr.packet.decoded] == [3,233]:
							self.server.clientDisconnect(usr.packet)
					else:
						print "commands {}".format(usr.packet.cmds)
						for func in usr.packet.cmds:

							f = None
							try:
								f=getattr(usr.appPage,"n_{}".format(func[0]))
							except Exception:
								try:
									f=getattr(self.server,"n_{}".format(func[0]))
								except Exception:
									pass
							if f is not None:
								f(usr,*func[1])

									
					
					usr.packet = None
					
					if usr.ready:
						usr.addCommand("cmdRecv",1)


	def sendData(self,usr):
			usr.send_packet.addHeader()
			usr.s.sendall(usr.send_packet.buf)
			print "Sending {} bytes to {}".format(len(usr.send_packet.buf),usr.address[0])
			usr.send_packet = None
			self.server.toSend.remove(usr)

		

		
		

	def tryHandshake(self,usr,data):
		rekey = re.search(r"Sec-WebSocket-Key: (.*)",data)
		key = ""
		if rekey is not None:
			key = rekey.group(1)
			usr.key = key
			usr.genKey()
			hs = websocket.handshake.format(usr.magickey)
			try:
				usr.s.sendall(hs)
			except Exception as e:
				print "tryHandshake Error: {}".format(e)
			print usr.magickey
			usr.handshake = True

	

	def update(self):
		for usr in self.server.connections:
			self.handleData(usr)
			self.sendData(usr)
