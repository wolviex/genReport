import websocket
import jwtools
import ebayTools
import json
import sys

def onConnect(e):
	print e.address

def onData(packet):
	print "Data: {}".format(packet.decoded)

def cmd_test(packet):
	d = {"test":"Yo","Bro":{"No":"Ye"}}
	js = json.dumps(d)
	sendPacket = websocket.PacketHandler.Packet(packet.usr)
	sendPacket.decoded = "/test {}".format(js)
	packet.usr.send_packet = sendPacket


def cmd_getEbayListings(packet):
	print "Sending ebay list"

	sendPacket = websocket.PacketHandler.Packet(packet.usr)
	sendPacket.decoded = "/updateEbayList {}".format(jwtools.mJoin("\n","\r",ebayTools.getAllListings()))
	packet.usr.send_packet = sendPacket



server = websocket.Server("10.0.2.15",9999)

server.onConnect.append(onConnect)
server.onRecieve.append(onData)
server.parent = sys.modules[__name__]


try:
	server.startServer()
except (Exception, KeyboardInterrupt) as e:
	print e
	server.close()