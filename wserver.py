import websocket
import jwtools
import ebayTools
import json
import sys

def onConnect(e):
	print e.address

def onData(packet):
	pass

def onDisconnected(packet):
	global server
	print "Num clients: {}".format(len(server.connections))


def cmd_getEbayListings(packet):
	print "Sending ebay list"

	sendPacket = websocket.PacketHandler.Packet(packet.usr)
	sendPacket.decoded = "/updateEbayList {}".format(jwtools.mJoin("\n","\r",ebayTools.getAllListings()))
	packet.usr.send_packet = sendPacket



server = websocket.Server("104.238.129.237",80)

server.onConnect.append(onConnect)
server.onRecieve.append(onData)
server.onDisconnect.append(onDisconnected)
server.parent = sys.modules[__name__]


try:
	server.startServer()
except (Exception, KeyboardInterrupt) as e:
	print e
	server.close()