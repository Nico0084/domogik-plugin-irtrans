# !/usr/bin/python
#-*- coding: utf-8 -*-
import commands
import zmq
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from domogik.common.utils import get_sanitized_hostname
from domogik_packages.plugin_irtrans.lib.irclients import getIRTransId, checkIfConfigured, IRTransClient, IRWSClient


#  *********** Prérequis *********************
# Installer le server IRTrans
# donner les droit d'ecriture dans le repertoire 'remotes' afin d'autoriser l'écriture du fichier de commande mise à jour pour chaque commande générée

ipirtrans = 'localhost'


class IRTransException(Exception):
    """
    IRTRans exception
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = "IRTRans exception" + value

    def __str__(self):
        return repr(self.value)

class IRTransServer :
    """Server instance for IRTrans modul.
    """
    def __init__ (self, serverPath , ipIRTrans, log, ipServer = "localhost") :
        """Start as daemon if necessary and init server
        /usr/local/irtrans irserver64 -debug_code -daemon -pidfile /var/run/irserver64.pid -loglevel 4 -logfile /var/log/irserver.log 192.168.0.175
        """
        # TODO : handle server, actually juste a check with irclient to verif if server is on
        self.path = serverPath
        self.serverIP = ipServer
        self.serverIPIRTrans = ipIRTrans
        self._Plugin.log = log
        # irserver64 -daemon 192.168.0.175
        status, self.etat = commands.getstatusoutput("{0}/irclient64 {1} -remotelist".format(self.path, self.serverIP))
        print "Etat : {0}\n Status : {1}".format(self.etat, status)
        progOK,  servOK = False,  True
        if status == 0  :         # pas d"erreur
            for li in self.etat.split('\n') :
                print li
                if li.find('IRTrans ASCII Client') !=-1 : progOK = True
                if li.find('Error connecting to host') !=-1 : servOK = False
        if not progOK :
            self._Plugin.log.info(u"irclient Program not find : {0/irclient".format(self.path))
        elif not servOK :
            self._Plugin.log.info(u"server connexion {0} impossible.".format(self.serverIP))
        else : self._Plugin.log.info(u"server IRtrans ok")

class ManagerClients :
    """" Manager IRTrans Clients.
    """
    def __init__ (self, Plugin,  cb_send_sensor) :
        """Initialise le manager IRTrans Clients"""
        self._Plugin = Plugin
        self._cb_send_sensor = cb_send_sensor
        self._stop = Plugin.get_stop()  # TODO : pas forcement util ?
        self.irTransClients = {} # list of all IRTRans modul
        self._Plugin.log.info(u"Manager IRTrans Clients is ready.")

    def addClient(self, device):
        """Add a IRTrans from domogik device"""
        name = getIRTransId(device)
        if self.irTransClients.has_key(name) :
            self._Plugin.log.debug(u"IRtransceiver Clients Manager : IRtransceiver {0} already exist, not added.".format(name))
            return False
        else:
            if checkIfConfigured(device["device_type_id"], device ) :
                if device["device_type_id"] == "irtrans.irtrans_lan" :
                    self.irTransClients[name] = IRTransClient(self, device, self._Plugin.log)
                elif  device["device_type_id"] == "irtrans.irwsserver" :
                    self.irTransClients[name] = IRWSClient(self, device, self._Plugin.log)
                else :
                    self._Plugin.log.error(u"IRtransceiver Clients Manager : IRtransceiver type {0} not exist, not added.".format(name))
                    return False
                self._Plugin.log.info(u"IRtransciever Clients Manager : created new client {0}.".format(name))
            else :
                self._Plugin.log.info(u"IRtransciever Clients Manager : device not configured can't add new client {0}.".format(name))
                return False
#            pprint.pprint(device)
            return True

    def removeClient(self, name):
        """Remove a IRTrans client and close it"""
        remote = self.getRemote(name)
        if remote :
            remote.close()
            self.irTransClients.pop(name)

    def getClient(self, id):
        """Get IRTrans client object by id."""
        if self.irTransClients.has_key(id) :
            return self.irTransClients[id]
        else :
            return None

    def getIdsClient(self, idToCheck):
        """Get IRTrans client key ids."""
        retval = []
        findId = ""
        self._Plugin.log.debug (u"getIdsClient check for device : {0}".format(idToCheck))
        if isinstance(idToCheck, IRTransClient) :
            for id in self.irTransClients.keys() :
                if self.irTransClients[id] == idToCheck :
                    retval = [id]
                    break
        else :
            self._Plugin.log.debug (u"getIdsClient, no IRTransClient instance...")
            if isinstance(idToCheck, str) :
                findId = idToCheck
                self._Plugin.log.debug (u"str instance...")
            else :
                if isinstance(idToCheck, dict) :
                    if idToCheck.has_key('device') : findId = idToCheck['device']
                    else :
                        if idToCheck.has_key('name') and idToCheck.has_key('id'):
                            findId = getIRTransId(idToCheck)
            if self.irTransClients.has_key(findId) :
                retval = [findId]
                self._Plugin.log.debug (u"key id type find")
            else :
                self._Plugin.log.debug (u"No key id type, search {0} in devices {1}".format(findId, self.irTransClients.keys()))
                for id in self.irTransClients.keys() :
                    self._Plugin.log.debug(u"Search in list by device key : {0}".format(self.irTransClients[id].domogikDevice))
                    if self.irTransClients[id].domogikDevice == findId :
                        self._Plugin.log.debug('find IRTransClient :)')
                        retval.append(id)
        self._Plugin.log.debug(u"getIdsClient result : {0}".format(retval))
        return retval

    def refreshClientDevice(self,  client):
        """Request a refresh domogik device data for a IRTrans Client."""
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('device.get')
        msg.add_data('type', 'plugin')
        msg.add_data('name', self._Plugin.get_plugin_name())
        msg.add_data('host', get_sanitized_hostname())
        devices = cli.request('dbmgr', msg.get(), timeout=10).get()
        for a_device in devices:
            if a_device['device_type_id'] == client._device['device_type_id']  and a_device['id'] == client._device['id'] :
                if a_device['name'] != client.device['name'] : # rename and change key client id
                    old_id = getIRTransId(client._device)
                    self.irTransClients[getIRTransId(a_device)] = self.irTransClients.pop(old_id)
                    self._Plugin.log.info(u"IRTransciever Client {0} is rename {1}".format(old_id,  getIRTransId(a_device)))
                client.updateDevice(a_device)
                break

    def handle_cmd(self, data, device):
        """ Handle a command from MQ for a specific device"""
        sended = False
        status = False
        reason = ""
        ids = self.getIdsClient(device)
        for id in ids :
            irClient = self.getClient(id)
            if irClient is not None :
                sended, status, reason = irClient.handle_cmd(data)
        return sended, status, reason

    def send_sensor(self, device, sensor_id, dt_type, value):
        """transmit message to send update sensor"""
        self._cb_send_sensor(device, sensor_id, dt_type, value)

    def sendXplTrig(self,  data):
        """Send an xpl message"""
        self._cb_send_sensor(data)


if __name__ == '__main__' :
    m = ManagerClients(None, None)
