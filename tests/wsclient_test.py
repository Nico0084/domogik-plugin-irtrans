# -*- coding: utf-8 -*-

from ws4py.client.threadedclient import WebSocketClient
import json
import threading
import time

on = "2100010000101101111100100000011110000000000000000000000000100000032100010000101101111100100000000000000000010000010000101000000000011110101000000000000000000000000000000000000000000000000000000110000000000000000010101110"
off = "2100010000101101111100100000011110000000000000000000000000100000032100010000101101111100100000000000000000000000010000101000000000011110101000000000000000000000000000000000000000000000000000000110000000000000000100101110"
powerfullOn  = "2100010000101101111100100000011110000000000000000000000000100000032100010000101101111100100000000000000000010000010000101000000000011110101000000000000000000000000000000001000000000000000000000110000000000000000110101110"
powerfullOff = "2100010000101101111100100000011110000000000000000000000000100000032100010000101101111100100000000000000000010000010000101000000000011110101000000000000000000000000000000000000000000000000000000110000000000000000010101110"

SEND_TEST = True
FLAG_Repeat = False
IPSERVER = "192.168.0.172" #"localhost"

class DummyClient(WebSocketClient):
    
    def opened(self):
        confirmation = {'header':{'type': 'ack-connect', 'idws':'request'}}
        self.idws = None
        self.send(json.dumps(confirmation))

    def closed(self, code, reason=None):
        print "Closed down", code, reason

    def received_message(self, message):
        global FLAG_Repeat
        print "Message received :"
        print message
        try :
            msg = json.loads(str(message))
        except TypeError as e :
            print '   Error parsing websocket msg :',  e
        else :
            if msg['header']['type'] == 'confirm-connect' :
                self.idws = msg['header']['idws']
            elif msg['header']['type'] == 'ack' :
                if msg['error'] !="" : 
                    FLAG_Repeat = True

if __name__ == '__main__':
    try:
        ws = DummyClient('ws://' + IPSERVER + ':5590/', protocols=['http-only', 'chat'])
        ws.connect()
        th = threading.Thread(None, ws.run_forever, "th_WSClient_forever", (), {})
        th.start()
        cpt = 0
        numcode = 2
        code = on
        while 1 :
            time.sleep(1)
            if (cpt % 10 == 0) :
                if SEND_TEST :
                    nbTry = 0
                    message = {'header':{'type': 'req-ack', 'idws': ws.idws,'idmsg': 1200,
                               'ip' : '192.168.0.172','timestamp' : time.time()}}
                    message.update({'request': 'sendIRCode', 'Coder':'DAIKIN', 'Type':'BinTimings',
                                    'IRCode': code})
                    FLAG_Repeat = True
                    while FLAG_Repeat and nbTry < 3 :
                        FLAG_Repeat = False
                        print "Sending message to server try : {0}".format(nbTry+1)
                        ws.send(json.dumps(message))
                        time.sleep(2)
                        nbTry +=1
                    if numcode == 1 : 
                        code = on
                        numcode = 2
                        time.sleep(5)
                    elif numcode == 2 :
                        code = powerfullOn
                        numcode = 3
                        time.sleep(15)
                    elif numcode == 3 :
                        code = powerfullOff
                        numcode = 4
                        time.sleep(15)
                    elif numcode == 4 :
                        code = off
                        numcode = 5
                        time.sleep(10)
                    elif numcode == 5 :
                        time.sleep(20)
            cpt += 1

    except KeyboardInterrupt:
        ws.close()
