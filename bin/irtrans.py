#!/usr/bin/python
# -*- coding: utf-8 -*-

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

- irtrans device manager

@author: Nico <nico84dev@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
# A debugging code checking import error
try:
    from domogik.xpl.common.xplconnector import Listener
    from domogik.xpl.common.xplmessage import XplMessage
    from domogik.xpl.common.plugin import XplPlugin
    from domogik.mq.reqrep.client import MQSyncReq
    from domogik.mq.message import MQMessage

    from domogik_packages.plugin_irtrans.lib.irtrans import IRTransServer,  getIRTransId,  ManagerClients
    
    import threading
    import traceback
except ImportError as exc :
    import logging
    logging.basicConfig(filename='/var/log/domogik/irtrans_start_error.log',level=logging.DEBUG)
    log = logging.getLogger('irtrans_start_error')
    err = "Error: Plugin Starting failed to import module ({})".format(exc) 
    print err
    logging.error(err)
    print log
 #  logging.removeHandler(log)

class IRTransManager(XplPlugin):
    """ Envois et recois des codes xPL IR DAIKIN
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='irtrans')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        if not self.check_configured():
            return

        # get the devices list
        self.devices = self.get_device_list(quit_if_no_device = False)
        # get the config values
        self.managerClients = ManagerClients(self,  self.send_xplTrig)
        for a_device in self.devices :
            try :
                if (a_device['device_type_id'] != 'irtrans.irtrans_lan') and (a_device['device_type_id'] != 'irtrans.irwsserver') :
                    self.log.error(u"No a device type reconized : {0}".format(a_device['device_type_id']))
                    break
                else :
                    if self.managerClients.addClient(a_device) :
                        self.log.info("Ready to work with device {0}".format(getIRTransId(a_device)))
                    else : self.log.info("Device parameters not configured, can't create IRTrans Client : {0}".format(getIRTransId(a_device)))
            except:
                self.log.error(traceback.format_exc())
                # we don't quit plugin if an error occured
                #self.force_leave()
                #return
        # Create the xpl listeners
        Listener(self.handle_xpl_cmd, self.myxpl,{'schema': 'irtrans.basic',
                                                                        'xpltype': 'xpl-cmnd'})
        print "Plugin ready :)"
        self.log.info("Plugin ready :)")
        self.ready()

    def send_xplStat(self, data):
        """ Send xPL cmd message on network
        """
        msg = XplMessage()
        msg.set_type("xpl-stat")
        msg.set_schema("ir.basic")
        msg.add_data(data)
        self.myxpl.send(msg)

    def send_xplTrig(self, data):
        """ Send xPL message on network
        """
        self.log.debug("Xpl Trig for {0}".format(data))
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema("ir.basic")
        msg.add_data(data)
        self.myxpl.send(msg)
        
    def handle_xpl_trig(self, massage):
        self.log.debug("xpl-trig listener received message:{0}".format(message))
        print message
    
    def handle_xpl_cmd(self,  message):
        """ Process xpl schema irtrans.basic
        """
        self.log.debug("xpl-cmds listener received message:{0}".format(message))
        device_name = message.data['device']
        self.log.debug("device :" + device_name)
        idsClient = self.managerClients.getIdsClient(device_name)
        find = False
        if idsClient != [] :
            for id in idsClient :       
                client = self.managerClients.getClient(id)
                if client :
                    self.log.debug("Handle xpl-cmds for IRTrans :{0}".format(message.data['device']))
                    find = True
                    client.handle_xpl_cmd(message.data)
        if not find : self.log.debug("xpl-cmds received for unknowns IRTrans :{0}".format(message.data['device']))
    

if __name__ == "__main__":
    IRTransManager()

