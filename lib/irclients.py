# !/usr/bin/python
#-*- coding: utf-8 -*-


""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Send en receive IR code for the IRTrans modul

Implements
==========

- class ir clients to communicate with ir  emitter / receiver
- define all class corresponding to ir emitter / receiver technnology.
- use class IRClientBase as parents
example irtrans ethernet, usb, websocket server like raspberry, ....


@author: Nico <nico84dev@gmail.com>
@copyright: (C) 2007-2014 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from ws4py.client.threadedclient import WebSocketClient
import json
import commands
import threading
import time
from random  import randint

class IRClientException(Exception):
    """
    IRClients exception
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = "IRClient exception, " + value

    def __str__(self):
        return repr(self.value)

DataTypes = ["RAW", "BinTimings", "HEX"]

def getIRTransId(device):
    """Return key IrRTrans id."""
    if device.has_key('name') and device.has_key('id'):
        return "{0}_{1}".format(device['name'], + device['id'])
    else : return None
    
def checkIfConfigured(deviceType,  device):
    print device
    if deviceType == 'irtrans_lan.device' :
        if device["name"] and \
           device["parameters"]["ir_coder"]["value"] and \
           device["parameters"]["server_path"]["value"] and \
           device["parameters"]["ip_server"]["value"] and \
           device["parameters"]["irtrans_ip"]["value"]: return True
        else : return False
    elif deviceType == 'irwsserver.device' :
        if device["name"] and \
           device["parameters"]["ir_coder"]["value"] and \
           device["parameters"]["ip_server"]["value"] and \
           device["parameters"]["port_server"]["value"] :
                if  device["parameters"]["ssl_activate"]["value"] == 'True':
                    if device["parameters"]["ssl_certificate"]["value"] and \
                       device["parameters"]["ssl_key"]["value"] : return True
                    else : return False
                return True
        else : return False
    return False

class TimerClient:
    def __init__(self, tempo, callback, args= [], kwargs={}):
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        self._tempo = tempo

    def _run(self):
        self._timer = threading.Timer(self._tempo, self._run)
        self._timer.start()
        self._callback(*self._args, **self._kwargs)
        
    def start(self):
        self._timer = threading.Timer(self._tempo, self._run)
        self._timer.start()

    def stop(self):
        self._timer.cancel()

class IRClientBase :
    "Objet client de base pour la liaison avec le tramsmetteur infrarouge."

    def __init__ (self,  manager,  device, log) :
        "Initialise le client"
        self._manager = manager
        self._device = device
        self._log = log
        self.etat = "" 

    # On accède aux attributs uniquement depuis les property
    remoteId = property(lambda self: getIRTransId(self._device))  # remote = IR Trancseiver ID for Comunications
    domogikDevice = property(lambda self: self._getDomogikDevice())

    def updateDevice(self,  device):
        """Update device data."""
        self._device = device

    def _getDomogikDevice(self):
        """Return device Id for xPL domogik device"""
        if self._device :
            # try to find in xpl_commands
            for a_cmd in self._device['xpl_commands']:
                for a_param in self._device['xpl_commands'][a_cmd]['parameters']:
                    if a_param['key'] == 'device' : return a_param['value']
            # try to find in xpl_stats
            for a_stat in self._device['xpl_stats']:
                for a_param in self._device['xpl_stats'][a_stat]['parameters']['static']:
                    if a_param['key'] == 'device' : return a_param['value']
            return None
        else : return None

    def sendCmd (self,  remote, cmd) :
        '''Envoi la commande au trametteur, surcharger la methode pour l'adapter à la techno.'''
        self._log.debug(u"Basic methode overwrite it for send capapibility.")
        return "Basic methode overwrite it for send capapibility."

    def handle_xpl_cmd(self,  xPLmessage):
        '''Handle a xpl-cmnd message from hub.
           surcharger éventuellement la methode pour l'adapter à la techno.
        '''
        if xPLmessage['command'] == 'send' :
            self.sendCmd(xPLmessage['code'])
        else : self._log.debug(u"IR Client {0}, recieved unknows command {1}".format(getIRTransId(self._device), xPLmessage['command']))

class IRTransClient(IRClientBase) :
    '''Objet de liaison avec le server IRTrans (Linux) dialogue avec irclient en ASCII'''

    def __init__ (self,  manager,  device, log) :
        "Initialise et recupère l'etat du server"
        IRClientBase.__init__(self,  manager,  device, log)
        self.path = device["parameters"]["server_path"]["value"]
        self.serverIP = device["parameters"]["ip_server"]["value"]
        self.irTransIP = device["parameters"]["irtrans_ip"]["value"]
        self._remote = "client_{0}".format(device["id"])
        status, self.etat = commands.getstatusoutput('%s/irclient64 %s -remotelist' %(self.path,  self.serverIP)) 
        print "Etat : {0}\n Status : {1}".format(self.etat,  status)
        progOK,  servOK = False,  True
        if status == 0  :         # pas d"erreur
            for li in self.etat.split('\n') :
                print li
                if li.find('IRTrans ASCII Client') !=-1 : progOK = True
                if li.find('Error connecting to host') !=-1 : servOK = False
        if not servOK :
            self._log.warning(u"Server connexion {0} impossible.".format(self.serverIP))
        if not progOK :
            self._log.warning(u"irclient software unreachable : {0}/irclient".format(self.path))
   #     print status,  self.etat


    def updateDevice(self,  device):
        """Update device data."""
        IRClientBase.updateDevice(self, device)
        self.path = device["parameters"]["server_path"]["value"]
        self.serverIP = device["parameters"]["ip_server"]["value"]
        self.irTransIP = device["parameters"]["irtrans_ip"]["value"]
        self._remote = "client_{0}".format(device["id"])

    def sendCmd (self,  remote, cmd) :
        "Envoi la commande au server IRTrans"
        status, output = commands.getstatusoutput('%s/irclient %s %s %s' %(self.path, self.serverIP, remote, cmd))
        print "Command result, status : {0}\n output : {1}".format(status,  output)
        err=''
        if status !=0 :         # Erreur
            for li in output.split('\n') :
                if li.find('Error connecting to host') !=-1  or  li.find('IR Error:') !=-1 :  err = err + li
        else : err='IR client sending cmd : %s' %('%s/irclient %s %s %s' %(self.path, self.serverIP, remote, cmd))
        return err

    def sendNewCmd(self, remote='',  timing = "" , code="") : 
        "Envoi une nouvelle commande, Ecrit le fichier fait un reload et envoi la commande"
        if remote =='' : remote =self._remote
        error = ''
        error = self.ecritFichRemote(remote,  timing, code)
        if not error :
           error = self.reloadIRTransDB()
           if not error : error = self.sendCmd(remote, "sample")
        return error

    def ecritFichRemote(self,  remote='',  timing = "" , code="") :
        "Ecrit un fichier type IRTrans comprenant la commande"
        if code.find('[T]') == -1 : 
            s = timing.split('][')[0]
            index =  s.find('[')
            if index != -1 : 
                num = int(s[index+1:])
                code = '[T]{0}[D]{1}'.format(num,  code)
        try :
            f = open('%s/remotes/%s.rem' %(self.path, remote),  "w")
            f.write ("[REMOTE]\n  [NAME]" + remote + "\n\n[TIMING]\n")
            f.write (timing + '\n[COMMANDS]\n')
            f.write ("  [sample]" + code +'\n')
            f.close()
            return 0
        except IOError, e :
            return e

    def reloadIRTransDB(self):
        "Recharge la base de donnée de irTransClients"
        status,output = commands.getstatusoutput('%s/irclient %s -reload' %(self.path,  self.serverIP)) 
        err=''
        print ("reload DB status: {0} output : {1}".format(status,  output))
        if status !=0 :         # erreur
            for li in output.split('\n') :
                if li.find('Error connecting to host') !=-1  : pass # err = err + li
        return err

    def handle_xpl_cmd(self,  xPLmessage):
        """Handle a xpl-cmnd message from hub"""
        if xPLmessage['command'] == 'send' :
            if xPLmessage['datatype'] == DataTypes[0] : # "RAW"
                pass
            elif xPLmessage['datatype'] == DataTypes[1] : # "BinTimings"
                # timing : {'TIMINGS': [['440', '448'], ['440', '1288'], ['3448', '1720'], ['408', '29616']], 'N': 4, 'FREQ': 38, 'FL': 0, 'RP': 0, 'RS': 0, 'RC5': 0, 'RC6': 0, 'RC': 1, 'NOTOG': 0, 'SB': 0}
                result = self.sendNewCmd(self._remote,  xPLmessage['timing'],  xPLmessage['code'])
                self._log.debug("IRTrans Client {0}, send code {1}, result : {2}".format(getIRTransId(self._device), xPLmessage['code'],  result))
                data = {'device': xPLmessage['device'],  'type': 'ack_ir_cmd', 'result': result}
                self._manager.sendXplAck(data)
            elif xPLmessage['datatype'] == DataTypes[2]: # "HEX" 
                pass
        else : self._log.debug(u"IRTrans Client {0}, recieved unknows command {1}".format(getIRTransId(self._device), xPLmessage['command']))


class IRWSClient(IRClientBase ):

    class WSClient(WebSocketClient):

        def __init__(self, parent, url, protocols=None, extensions=None, heartbeat_freq=None, ssl_options=None, headers=None) :
            self._parent = parent
            WebSocketClient.__init__(self, url = url, protocols = protocols,  ssl_options = ssl_options)

        # WebSocketClient methodes overwrite
        def opened(self):
            confirmation = {'header':{'type': 'ack-connect', 'idws':'request'}}
            self.send(json.dumps(confirmation))

        def closed(self, code, reason=None):
            self._parent.webSockect = None
            print "Closed down", code, reason

        def received_message(self, message):
            print "Message received :"
            print message
            try :
                msg = json.loads(str(message))
            except TypeError as e :
                print '   Error parsing websocket msg :',  e
            else :
                if msg['header']['type'] == 'confirm-connect' :
                    self._parent.idws = msg['header']['idws']
                    self._parent.requestLasMemIRcode()
                    self._parent.requestTolerancesEncoder() # TODO: à changer par sendTolerancesEncoder une fois les paramettres récupérés de device
                    self._parent.requestHardState(True)
                    if self._parent._msgToSend  : self.send(json.dumps(self._parent._msgToSend))
                elif msg['header']['type'] == 'ack' and msg['header']['idws'] == self._parent.idws :
                    if msg['request'] == 'server-hbeat':
                        pass
                    elif msg['request'] == 'getMemIRCode':
                        if msg['data']['encoder'] == self._parent.irCoder:
                            if self._parent.setMemIRCode(msg['data']) :
                                data = {'device': self._parent.domogikDevice,  'type': 'code_ir', 'code': msg['data']['code'],  'encoder' : msg['data']['encoder']}
                                self._parent._manager.sendXplTrig(data)
                        else : 
                            self._parent._log.debug("Receive ir code with bad encoder : {0}".format(msg['data']['encoder'] if msg['data']['encoder'] !='' else 'unknown'))
                    elif msg['request'] == 'setTolerances':
                        if msg['error']  != '': self._parent._log.warning(msg['error'] + msg['data']['error'] )
                    elif msg['request'] == 'getTolerances':         
                        if msg['error']  == '':
                            self._parent.setTolerancesEncoder(msg['data']['tolerances'])
                    elif msg['request'] == 'getState':         
                        if msg['error']  == '':
                            self._parent.setHardState(msg['data']['state'])
                        else :
                            self._hardState = None
                            self._parent._log.info("Hard State : {0}, {1}".format( msg['error'],  msg['data']['error']))
                    elif self._parent._msgToSend and (msg['request'] == 'sendIRCode') :
                        if msg['header']['idmsg'] == self._parent._msgToSend['header']['idmsg'] :
                            data = {'device': self._parent.domogikDevice,  'type': 'ack_ir_cmd', 'result': msg['error'] if msg['error'] else "ok"}
                            if msg['error'] != '':
                               if not self._parent.nextTrySendCode() :
                                    self._parent._manager.sendXplAck(data)
                                    self._parent._msgToSend = None
                            else :        
                                self._parent.setMemIRCode(msg['data'])
                                self._parent._manager.sendXplAck(data)
                                self._parent._msgToSend = None
                        else : self._parent._log.info(u"Ack msg received but not register for {0}".format(self._parent.remoteId))
                elif msg['header']['type'] == 'pub' and msg['header']['idws'] == self._parent.idws :
                    if msg['type'] == 'codereceived' :
                        if msg['data']['encoder'] == self._parent.irCoder:
                            self._parent.setMemIRCode(msg['data'])
                            data = {'device': self._parent.domogikDevice,  'type': 'code_ir', 'code': msg['data']['code'],  'encoder' : msg['data']['encoder']}
                            self._parent._manager.sendXplTrig(data)
                        else : 
                            self._parent._log.debug("Receive ir code with bad encoder : {0}".format(msg['data']['encoder'] if msg['data']['encoder'] !='' else 'unknown'))
                    if msg['type'] == 'hardState' :
                            self._parent.setHardState(msg['data']['state'])                        
                    else :
                        self._parent._log.debug("Receive unknown published type : {0}".format(msg['type']))
                    

    def __init__(self, manager,  device, log) :
        '''Init IRClientBase and WebSocketClient'''

        IRClientBase.__init__(self,  manager,  device, log)
        self.updateDevice(device)
        self._numTrySend = 1
        self._msgToSend = None
        self.webSockect = None
        self.IRCodeValue = None
        self._hardState = None
        self.createWSClient()
        self._serverHbeat = TimerClient(30,  self.sendHbeat)
        time.sleep(1)
        self._serverHbeat.start()
        
    def __del__(self):
        '''Close hbeat timmer and web socket client'''
        if self.webSockect : self.webSockect.close()
        self._serverHbeat.stop()

# IRClientBase methodes overwrite
    def updateDevice(self,  device):
        """Update device data."""
        IRClientBase.updateDevice(self, device)
        self._serverIP = device["parameters"]["ip_server"]["value"]
        self._serverPort = device["parameters"]["port_server"]["value"]
        self.irCoder = device["parameters"]["ir_coder"]["value"]
        self.repeatCode = int(device["parameters"]["ir_repeat"]["value"])
        self.tolerances = {"tolerance": int(device["parameters"]["ir_tolerance"]["value"]) ,  
                                  "large": int(device["parameters"]["ir_large_tolerance"]["value"]), 
                                  "maxout": int(device["parameters"]["ir_max_out"]["value"])}  
        self._remote = "client_{0}".format(device["id"])

    def sendCmd (self,  dataType, cmd) :
        "Envoi la commande au server WebSocket"
        self._msgToSend = self.getMsgHeader()
        self._msgToSend.update({'request': 'sendIRCode', 'encoder': self.irCoder, 'datatype': dataType, 'code': cmd})
        if self.webSockect : 
            self.webSockect.send(json.dumps(self._msgToSend))
        else : self.createWSClient()
        return ""

    def handle_xpl_cmd(self,  xPLmessage):
        """Handle a xpl-cmnd message from hub"""
        if xPLmessage['command'] == 'send' :
            if xPLmessage['datatype'] == DataTypes[0] : # "RAW"
                pass
            elif xPLmessage['datatype'] == DataTypes[1] :  #"BinTimings" 
                self.sendCmd(xPLmessage['datatype'],  xPLmessage['code'])
                self._log.debug("WS Client {0}, send code {1}".format(getIRTransId(self._device), xPLmessage['code']))
            elif xPLmessage['datatype'] == DataTypes[0] : #"HEX" :
                pass
        else : self._log.debug(u"WS Client {0}, recieved unknows command {1}".format(getIRTransId(self._device), xPLmessage['command']))

 # New methods
 
    def getMsgHeader(self):
        return {"header" : {"type": "req-ack",  'idws': self.idws,'idmsg': randint(1, 1000000), 'ip' : self.ip,'timestamp' : time.time()}}

    def createWSClient(self):
        if self._device :
            if self._device["parameters"]["ssl_activate"]["value"] == "True": 
                prefix = "wss"
                ssl_options = {'certificate': device["parameters"]["ssl_certificate"]["value"], 'key': device["parameters"]["ssl_key"]["value"]}
            else : 
                prefix ="ws"
                ssl_options = None
            url = prefix +"://" + self._serverIP + ":"+ self._serverPort +"/"
            print "**** ",  url
            self.idws = None
            self.ip =""
            self.webSockect = self.WSClient(self,  url, ['http-only', 'chat'],  None, None,  ssl_options,  None )
            try :
                self.webSockect.connect()
               # TODO: run dans thread avec self.isStop
                th = threading.Thread(None, self.webSockect.run_forever, "th_WSClient_forever-{0}".format(self.domogikDevice), (), {})
                print "start forever mod"
                th.start()
                self._log.debug(u"WSClient for <{0}>, running forever".format(self.domogikDevice))
            except Exception, e:
                self.webSockect = None
                self._log.warning(u"WebSocket Client for <{0}> to {1}, create error : {2}".format(self.domogikDevice,  url, e))
        else : 
            self.webSockect = None
            self._log.debug(u"No device attached, WS Client creation unavailable.")
    
    def nextTrySendCode(self):
        if self._numTrySend < self.repeatCode :
            print ("**************  Next TRY **********************")
            print("repeat :{0}, nb :{1}".format(self.repeatCode, self._numTrySend))
            self._numTrySend +=1
            self.sendCmd(self._msgToSend['datatype'],  self._msgToSend['code'])
            return True
        else :
            self._numTrySend = 1
            return False
            
    def setMemIRCode(self,  data):
        '''Memorize last IR code known. return True is updated else False'''
        if data['error'] == '':
            if not self.IRCodeValue :
                self._log.info("IRCode Value must be created.")
                self.IRCodeValue = {'code': data['code'],  'encoder' : data['encoder']}
                return True
            elif self.IRCodeValue['code'] != data['code'] :
                self._log.info("IRCode Value must be updated.")
                self.IRCodeValue = {'code': data['code'],  'encoder' : data['encoder']}
                return True
            else : 
                self._log.debug("IRCode Value is up to date.")
        else :
            self._log.info("Can't check IRCode : {0}".format(data['error']))
        return False
            
    def setTolerancesEncoder(self,  tolerances):
        self.tolerances = tolerances
        
    def setHardState(self,  state):
        '''Memorize flag hardState and send xpl-trig if necessary.'''
        if  self._hardState != state :
            self._hardState = state
            data = {'device': self.domogikDevice,  'type': 'power',  'state': "On" if self._hardState == 1 else "Off"}
            self._manager.sendXplTrig(data)

    def sendTolerancesEncoder(self):
        '''Set Tolerances parameters for encoder'''
        msgToSend = self.getMsgHeader()
        msgToSend.update({'request': 'setTolerances', 'encoder': self.irCoder,  'tolerances' : self.tolerances})
        if self.webSockect : 
            self.webSockect.send(json.dumps(msgToSend))

    def requestTolerancesEncoder(self):
        '''Request by sending message to WSServer tolerances parameters.'''
        msgToSend = self.getMsgHeader()
        msgToSend.update({'request': 'getTolerances', 'encoder': self.irCoder,})
        if self.webSockect : 
            self.webSockect.send(json.dumps(msgToSend))

    def requestLasMemIRcode(self):
        '''Request by sending message to WSServer code in memory.'''
        msgToSend = self.getMsgHeader()
        msgToSend.update({'request': 'getMemIRCode'})
        if self.webSockect : 
            self.webSockect.send(json.dumps(msgToSend))
            
    def requestHardState(self,  getCapability = False):
        '''Request hard state by sending message to WSserver if getCapability force to get hard State capabity.'''
        if getCapability or (self._hardState != None):
            msgToSend = self.getMsgHeader()
            msgToSend.update({'request': 'getState'})
            if self.webSockect : 
                self.webSockect.send(json.dumps(msgToSend))

    def sendHbeat(self):
        '''Envoi un message Hbeat pour  vérifier la connection au WebSockect server.'''
        hbeatMsg = self.getMsgHeader()
        hbeatMsg.update({'request': 'server-hbeat'})
        if self.webSockect : 
            self.webSockect.send(json.dumps(hbeatMsg))
        else : self.createWSClient()
        
    def startHbeat(self):
        self._serverHbeat.start()
    
    def stopHbeat(self):
        self._serverHbeat.stop()
    
    
