# !/usr/bin/python
#-*- coding: utf-8 -*-
import os
import commands
from zmq.eventloop.ioloop import IOLoop
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from domogik.common.utils import get_sanitized_hostname

from Daikin_Code import  *

#  *********** Prérequis *********************
# Installer le server IRTrans 
# donner les droit d'ecriture dans le repertoire 'irTransClients' afin d'autoriser l'écriture du fichier de commande mise à jour pour chaque commande générée

ipirtrans = 'localhost'


class IRTransException(Exception):
    """
    IRTRans exception
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

def getIRTransId(device):
    """Return key IrRTrans id."""
    if device.has_key('name') and device.has_key('id'):
        return "{0}_{1}".format(device['name'], + device['id'])
    else : return None

class IRTransServer :
    """Server instance for IRTrans modul.
    """
    def __init__ (self,  serverPath , ipIRTrans, log, ipServer = "localhost") :    
        "Start as daemon if necessary and init server"
        # TODO : handle server, actually juste a check with irclient to verif if server is on
        self.path = serverPath
        self.serverIP = ipServer
        self.serverIPIRTrans = ipIRTrans
        self._xplPlugin.log = log
        # irserver64 -daemon 192.168.0.175
        status, self.etat = commands.getstatusoutput("{0}/irclient64 {1} -remotelist".format(self.path,  self.serverIP)) 
        print "Etat : {0}\n Status : {1}".format(self.etat,  status)
        progOK,  servOK = False,  True
        if status == 0  :         # pas d"erreur
            for li in self.etat.split('\n') :
                print li
                if li.find('IRTrans ASCII Client') !=-1 : progOK = True
                if li.find('Error connecting to host') !=-1 : servOK = False
        if not progOK :
            self._xplPlugin.log.info(u"irclient Program not find : {0/irclient".format(self.path))
        elif not servOK :
            self._xplPlugin.log.info(u"server connexion {0} impossible.".format(self.serverIP))
        else : self._xplPlugin.log.info(u"server IRtrans ok")
        
class ManagerClients :
    """" Manager IRTrans Clients.
    """
    def __init__ (self,  cb_send_xPL) :
        """Initialise le manager IRTrans Clients"""
        self._xplPlugin = xplPlugin
        self._cb_send_xPL = cb_send_xPL
        self._stop = xplPlugin.get_stop()  # TODO : pas forcement util ?
        self.irTransClients = {} # list of all IRTRans modul
        self._xplPlugin.log.info(u"Manager IRTrans Clients is ready.")

    def addClient(self, device):
        """Add a IRTrans from domogik device"""
        name = getIRTransId(device)
        if self.irTransClients.has_key(name) :
            self._xplPlugin.log.debug(u"IRtrans Clients Manager : IRtrans {0} already exist, not added.".format(name))
            return False
        else:
            self.irTransClients[name] = IRTransClient(self,  device,  self._xplPlugin.log)
            self._xplPlugin.log.info(u"IRtrans Clients Manager : created new client {0}.".format(name))
            print "Add Client :"
            pprint.pprint(device)
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
        retval =[]
        findId = ""
        self._xplPlugin.log.debug (u"getIdsClient check for device : {0}".format(idToCheck))
        if isinstance(idToCheck,  IRTransClient) :
            for id in self.irTransClients.keys() :
                if self.irTransClients[id] == idToCheck :
                    retval = [id]
                    break
        else :
            self._xplPlugin.log.debug (u"getIdsClient,  no IRTransClient instance...")
            if isinstance(idToCheck,  str) :  
                findId = idToCheck
                self._xplPlugin.log.debug (u"str instance...")
            else :
                if isinstance(idToCheck,  dict) :
                    if idToCheck.has_key('device') : findId = idToCheck['device']
                    else :
                        if idToCheck.has_key('name') and idToCheck.has_key('id'): 
                            findId = getIRTransId(idToCheck)
            if self.irTransClients.has_key(findId) : 
                retval = [findId]
                self._xplPlugin.log.debug (u"key id type find")
            else :
                self._xplPlugin.log.debug (u"No key id type, search {0} in devices {1}".format(findId, self.irTransClients.keys()))
                for id in self.irTransClients.keys() :
                    self._xplPlugin.log.debug(u"Search in list by device key : {0}".format(self.irTransClients[id].getDomogikDevice))
                    if self.irTransClients[id].getDomogikDevice == findId : 
                        self._xplPlugin.log.debug('find IRTransClient :)')
                        retval.append(id)
        self._xplPlugin.log.debug(u"getIdsClient result : {0}".format(retval))
        return retval
        
    def refreshClientDevice(self,  client):
        """Request a refresh domogik device data for a IRTrans Client."""
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('device.get')
        msg.add_data('type', 'plugin')
        msg.add_data('name', self._xplPlugin.get_plugin_name())
        msg.add_data('host', get_sanitized_hostname())
        devices = cli.request('dbmgr', msg.get(), timeout=10).get()
        for a_devices in devices:
            if a_device['device_type_id'] == client._device['device_type_id']  and a_device['id'] == client._device['id'] :
                if a_device['name'] != client.device['name'] : # rename and change key client id
                    old_id = getIRTransId(client._device)
                    self.irTransClients[getIRTransId(a_device)] = self.irTransClients.pop(old_id)
                    self._xplPlugin.log.info(u"IRTrans Client {0} is rename {1}".format(old_id,  getIRTransId(a_device)))
                client.updateDevice(a_device)
                break        

class IRTransClient :
    "Objet de liaison avec le server IRTrans (Linux) dialogue avec irclient en ASCII"
    
    def __init__ (self,  manager,  device, log) :
        "Initialise et recupère l'etat du server"
        self._manager = manager
        self._device = device
        self._log = log
        self.path = device["parameters"]["server_path"]
        self.serverIP = device["parameters"]["ip_server"]
        self.irTransIP = device["parameters"]["irtrans_ip"]
        self._remote = "client_{0}".format(device["id"])
        status, self.etat = commands.getstatusoutput('%s/irclient64 %s -remotelist' %(self.path,  self.serverIP)) 
        print "Etat : {0}\n Status : {1}".format(self.etat,  status)
        progOK,  servOK = False,  True
        if status == 0  :         # pas d"erreur
            for li in self.etat.split('\n') :
                print li
                if li.find('IRTrans ASCII Client') !=-1 : progOK = True
                if li.find('Error connecting to host') !=-1 : servOK = False
        if not progOK :
            print 'Programme irclient introuvable : %s/irclient' %(self.path)
        elif not servOK :
            print 'connexion au server %s impossible.' %(self.serverIP)
   #     print status,  self.etat
        
    def updateDevice(self,  device) :
        """Update device data."""
        self._device = device
        self.path = device["parameters"]["server_path"]
        self.serverIP = device["parameters"]["ip_server"]
        self.irTransIP = device["parameters"]["irtrans_ip"]
        self._remote = "client_{0}".format(device["id"])
        
    def sendCmd (self,  remote, cmd) :
        "Envoi la commande au server IRTrans"
        status,output = commands.getstatusoutput('%s/irclient %s %s %s' %(self.path, self.serverIP, remote, cmd))
        print "Command result, status : {0}\n output : {1}".format(status,  output)
        err=''
        if not status :         # pas d"erreur
            for li in output.split('\n') :
                if li.find('Error connecting to host') !=-1  or  li.find('IR Error:') !=-1 :  err = err + li
        else : err='IR server Error sending cmd : %s' %('%s/irclient %s %s %s' %(self.path, self.serverIP, remote, cmd))
        return err
                
    def sendNewCmd(self, remote='',  tgs = Timings() , cmd=CodeIRDaikin()) : 
        "Envoi une nouvelle commande, Ecrit le fichier fait un reload et envoi la commande"
        if remote =='' : remote =self._remote
        err=''
        err = self.ecritFichRemote(remote,  tgs, cmd)
        if not err :
           err = self.reloadIRTransDB()
           if not err : err = self.sendCmd(remote, cmd.nom)
        return err
        
    def ecritFichRemote(self,  remote='',  tgs = Timings() , cmd=CodeIRDaikin()) :
        "Ecrit un fichier type IRTrans comprenant la commande"
        try :
            f = open('%s/irTransClients/%s.rem' %(self.path, remote),  "w")
            f.write ("[REMOTE]\n  [NAME]" + remote + "\n\n[TIMING]\n")
            f.write (tgs.encodeTimingsIRTrans() + '\n[COMMANDS]\n')
            f.write (cmd.encodeCmdIRTrans() +'\n')
            f.close()
            return 0
        except IOError, e :
            return e
    
    def reloadIRTransDB(self):
        "Recharge la base de donnée de irTransClients"
        status,output = commands.getstatusoutput('%s/irclient %s -reload' %(self.path,  self.serverIP)) 
        err=''
        if not status :         # pas d"erreur
            for li in output.split('\n') :
                if li.find('Error connecting to host') !=-1  :  err = err + li
        else : err='IR server Error sending cmd : %s/irclient %s -reload' %(self.path,  self.serverIP)
        return err
        
    def handle_xpl_cmd(self,  xPLmessage):
        """Handle a xpl-cmnd message from hub"""
        if xPLmessage['command'] == 'send' :
            self._log.debug("IRTrans Client {0}, send code {1}".format(getIRTransId(self._device), xPLmessage['code']))
            
        else : self._log.debug(u"IRTrans Client {0}, recieved unknows command {1}".format(getIRTransId(self._device), xPLmessage['command']))
 
    
if __name__ == '__main__' :
    tims = Timings()
    cmd = CodeIRDaikin()
    cmd.nom = 'On'
    cmd.setCmd("ON/OFF","ON")
    cmd.setCmd("Température",  opt = 20)
    cl =IrtransClient('/usr/local/irtrans', 'localhost')
    tims.litFichIRTrans("/usr/local/irtrans/irTransClients/Daikin.rem")
    err = cl.sendNewCmd('essais', tims,cmd)
    if  err : print err
