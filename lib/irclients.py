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
import traceback

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
#    print(device)
    if deviceType == 'irtrans.irtrans_lan' :
        if device["name"] and \
           device["parameters"]["ir_coder"]["value"] and \
           device["parameters"]["server_path"]["value"] and \
           device["parameters"]["ip_server"]["value"] and \
           device["parameters"]["irtrans_ip"]["value"]: return True
        else : return False
    elif deviceType == 'irtrans.irwsserver' :
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

    def __init__ (self, manager, device, log) :
        "Initialise le client"
        self._manager = manager
        self._device = device
        self._log = log
        self.etat = ""

    # On accède aux attributs uniquement depuis les property
    remoteId = property(lambda self: getIRTransId(self._device))  # remote = IR Trancseiver ID for Comunications
    domogikDevice = property(lambda self: self._device)

    def updateDevice(self, device):
        """Update device data."""
        self._device = device

    def sendCmd (self, remote, cmd) :
        '''Envoi la commande au trametteur, surcharger la methode pour l'adapter à la techno.'''
        self._log.debug(u"Basic methode overwrite it for send command capapibility.")
        return "Basic methode overwrite it for send command capapibility."

    def send_to_sensor(self, data):
        """"Format and send value to sensor"""
        for s in self._device['sensors'] :
            if self._device['sensors'][s]['reference'] == data ['type'] :
                print("\n Message for sensor {0}, data: {1}".format(self._device['sensors'][s]['reference'], data ['type']))
                self._manager.send_sensor(self._device, self._device['sensors'][s]['id'], self._device['sensors'][s]['data_type'], data['value'])
                break

    def handle_cmd(self, data):
        """Handle a cmnd data from MQ.
           surcharger éventuellement la methode pour l'adapter à la techno.
        """
        sended = False
        status = False
        reason = u"IR Client {0}, recieved unknows command id {1}".format(getIRTransId(self._device), data)
        for cmd in self._device['commands']:
            if data['command_id'] == self._device['commands'][cmd]['id'] :
                if 'code' in data :
                    self.sendCmd(data['code'])
                    status = True
                    reason = ""
                else :
                    reason = u"IR Client {0}, recieved invalid command {1}".format(getIRTransId(self._device), data)
                    self._log.debug(reason)
                break
        if reason != "" : self._log.warning(reason)
        return sended, status, reason

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
   #     print status, self.etat

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

    def handle_cmd(self, data):
        """Handle a cmnd message from MQ"""
        sended = False
        status = False
        reason = u"IR Client {0}, recieved unknows command id {1}".format(getIRTransId(self._device), data)
        for cmd in self._device['commands']:
            if data['command_id'] == self._device['commands'][cmd]['id'] :
                if cmd == 'send_bintimings' :
                    # timing : {'TIMINGS': [['440', '448'], ['440', '1288'], ['3448', '1720'], ['408', '29616']], 'N': 4, 'FREQ': 38, 'FL': 0, 'RP': 0, 'RS': 0, 'RC5': 0, 'RC6': 0, 'RC': 1, 'NOTOG': 0, 'SB': 0}
                    result = self.sendNewCmd(self._remote,  data['timing'],  data['code'])
                    self._log.debug("IRTrans Client {0}, send code {1}, result : {2}".format(getIRTransId(self._device), data['code'],  result))
                    data = {'device': data['device'],  'type': 'ack_ir_cmd', 'value': result}
                    self.send_to_sensor(data)
                elif cmd == 'send_raw' :
                    pass
                elif cmd == 'send_hexa' :
                    pass
                    self.sendCmd(data['code'])
                    status = True
                    reason = ""
                else :
                    reason = u"IR Client {0}, recieved invalid command {1}".format(getIRTransId(self._device), data)
                    self._log.debug(reason)
                break
        if reason != "" : self._log.warning(reason)
        return sended, status, reason


class IRWSClient(IRClientBase ):

    class WSClient(WebSocketClient):

        def __init__(self, parent, url, protocols=None, extensions=None, heartbeat_freq=None, ssl_options=None, headers=None) :
            self._parent = parent
            WebSocketClient.__init__(self, url = url, protocols = protocols,  ssl_options = ssl_options)

        log = property(lambda self: self._parent._log)
        remoteId = property(lambda self: self._parent.remoteId)

        # WebSocketClient methodes overwrite
        def opened(self):
            confirmation = {'header':{'type': 'ack-connect', 'idws':'request'}}
            self.send(json.dumps(confirmation))

        def closed(self, code, reason=None):
            self._parent.webSockect = None
            self.log.info(u"Closed {0} down with code {1}, {2}".format(self.remoteId, code, reason))

        def received_message(self, message):
            print "WSClient Message received :"
            print message
            try :
                msg = json.loads(str(message))
            except TypeError as e :
                self.log.warning(u"{0} Error parsing websocket msg :{1}".format(self.remoteId, e))
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
                                data = {'device': self._parent.domogikDevice,  'type': 'code_ir', 'value': msg['data']['code'],  'encoder' : msg['data']['encoder']}
                                self._parent.send_to_sensor(data)
                        else :
                            self.log.debug("Receive ir code with bad encoder : {0}".format(msg['data']['encoder'] if msg['data']['encoder'] !='' else 'unknown'))
                    elif msg['request'] == 'setTolerances':
                        if msg['error']  != '': self.log.warning(msg['error'] + msg['data']['error'] )
                    elif msg['request'] == 'getTolerances':
                        if msg['error']  == '':
                            self._parent.setTolerancesEncoder(msg['data']['tolerances'])
                    elif msg['request'] == 'getState':
                        if msg['error']  == '':
                            self._parent.setHardState(msg['data']['state'])
                        else :
                            self._hardState = None
                            self.log.info("Hard State : {0}, {1}".format( msg['error'],  msg['data']['error']))
                    elif self._parent._msgToSend and (msg['request'] == 'sendIRCode') :
                        if msg['header']['idmsg'] == self._parent._msgToSend['header']['idmsg'] :
                            data = {'device': self._parent.domogikDevice,  'type': 'ack_ir_cmd', 'value': msg['error'] if msg['error'] else "ok"}
                            if msg['error'] != '':
                               if not self._parent.nextTrySendCode() :
                                    self._parent.send_to_sensor(data)
                                    self._parent._msgToSend = None
                            else :
                                self._parent.setMemIRCode(msg['data'])
                                self._parent.send_to_sensor(data)
                                self._parent._msgToSend = None
                        else : self.log(u"Ack msg received but not register for {0}".format(self._parent.remoteId))
                elif msg['header']['type'] == 'pub' and msg['header']['idws'] == self._parent.idws :
                    if msg['type'] == 'codereceived' :
                        if msg['data']['encoder'] == self._parent.irCoder:
                            self._parent.setMemIRCode(msg['data'])
                            data = {'device': self._parent.domogikDevice,  'type': 'code_ir', 'value': msg['data']['code'],  'encoder' : msg['data']['encoder']}
                            self._parent.send_to_sensor(data)
                        else :
                            self.log.debug(u"Receive ir code with bad encoder : {0}".format(msg['data']['encoder'] if msg['data']['encoder'] !='' else 'unknown'))
                    elif msg['type'] == 'hardState' :
                            self._parent.setHardState(msg['data']['state'])
                    else :
                        self.log.debug(u"Receive unknown published type : {0}".format(msg['type']))


    def __init__(self, manager, device, log) :
        '''Init IRClientBase and WebSocketClient'''

        IRClientBase.__init__(self, manager, device, log)
        self.updateDevice(device)
        self._numTrySend = 1
        self._msgToSend = None
        self.webSockect = None
        self.IRCodeValue = None
        self._hardState = None
        self.createWSClient()
        self._serverHbeat = TimerClient(30, self.sendHbeat)
        time.sleep(1)
        self._serverHbeat.start()

    def __del__(self):
        '''Close hbeat timmer and web socket client'''
        if self.webSockect : self.webSockect.close()
        self._serverHbeat.stop()

# IRClientBase methodes overwrite
    def updateDevice(self, device):
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

    def sendCmd (self, dataType, cmd) :
        """Envoi la commande au server WebSocket"""
        self._msgToSend = self.getMsgHeader()
        self._msgToSend.update({'request': 'sendIRCode', 'encoder': self.irCoder, 'datatype': dataType, 'code': cmd})
        if self.webSockect :
            self.webSockect.send(json.dumps(self._msgToSend))
        else : self.createWSClient()
        return ""

    def handle_cmd(self, data):
        """Handle a cmnd data from MQ"""
        sended = False
        status = False
        reason = u"IR Client {0}, recieved unknows command id {1}".format(getIRTransId(self._device), data)
        print(u"*** WS handle_cmd for device : {0}".format(self._device))
        for cmd in self._device['commands']:
            if data['command_id'] == self._device['commands'][cmd]['id'] :
                sended = True
                if cmd == 'send_bintimings' :
                    self.sendCmd(DataTypes[1], data['code'])
                    self._log.debug("WS Client {0}, send code {1}".format(getIRTransId(self._device), data['code']))
                    status = True
                    reason = ""
                elif cmd == 'send_raw' :
                    pass
                elif cmd == 'send_hexa' :
                    pass
        if reason != "" : self._log.warning(reason)
        return sended, status, reason

 # New methods

    def getMsgHeader(self):
        return {"header" : {"type": "req-ack",  'idws': self.idws,'idmsg': randint(1, 1000000), 'ip' : self.ip,'timestamp' : time.time()}}

    def createWSClient(self):
        if self._device :
            if self._device["parameters"]["ssl_activate"]["value"] == "True":
                prefix = "wss"
                ssl_options = {'certificate': self._device["parameters"]["ssl_certificate"]["value"], 'key': self._device["parameters"]["ssl_key"]["value"]}
            else :
                prefix ="ws"
                ssl_options = None
            url = prefix +"://" + self._serverIP + ":"+ self._serverPort +"/"
            self.idws = None
            self.ip =""
            self.webSockect = self.WSClient(self,  url, ['http-only', 'chat'], None, None, ssl_options, None )
            try :
                self.webSockect.connect()
               # TODO: run dans thread avec self.isStop
                th = threading.Thread(None, self.webSockect.run_forever, "th_WSClient_forever-{0}".format(getIRTransId(self.domogikDevice)), (), {})
                self._log.info(u"WSClient for <{0}>, start forever mod to {1}".format(getIRTransId(self.domogikDevice), url))
                th.start()
            except Exception, e:
                self.webSockect = None
                self._log.warning(u"WSClient for <{0}> to {1}, create error : {2}".format(getIRTransId(self.domogikDevice), url, e))
        else :
            self.webSockect = None
            self._log.warning(u"No device attached, WS Client creation unavailable.")

    def nextTrySendCode(self):
        if self._numTrySend < self.repeatCode :
            self._log.info("Reception fail, try resend {0}/{1}".format(self._numTrySend + 1,  self.repeatCode))
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
        '''Memorize flag hardState and send to sensor if necessary.'''
        if  self._hardState != state :
            self._hardState = state
            data = {'device': self.domogikDevice,  'type': 'power', 'value': "1" if self._hardState == 1 else "0"}
            self.send_to_sensor(data)

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


