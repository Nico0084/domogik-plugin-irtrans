#!/usr/bin/python
#-*- coding: utf-8 -*-create_device.py

### configuration ######################################
ENCODER = "DAIKIN"

DEVICE_NAME="IRTrans_1"
DEVICE_PATH = "/usr/local/irtrans"
DEVICE_IP_SERVER = "localhost"
DEVICE_IP_IRTRANS = "192.168.0.175"
##################################################
DEVICE2_NAME="IRTrans_ws"
DEVICE2_IP_SERVER = "192.168.0.172"
DEVICE2_PORT_SERVER = 5590
DEVICE2_SSL = False
DEVICE2_CERTIFICATE = ""
DEVICE2_KEY =""
##################################################

from domogik.tests.common.testdevice import TestDevice
from domogik.common.utils import get_sanitized_hostname

plugin =  "irtrans"

def create_device():
    ### create the device, and if ok, get its id in device_id
    client_id  = "plugin-{0}.{1}".format(plugin, get_sanitized_hostname())
    print("Creating the irtrans device...")
    td = TestDevice()
    params = td.get_params(client_id, "irtrans.irtrans_lan")
        # fill in the params
    params["device_type"] = "irtrans.irtrans_lan"
    params["name"] = "test_IRTrans_LAN"
    params["reference"] = "IRTrans Lan client"
    params["description"] = "Handle IRTrans modul"
    for idx, val in enumerate(params['no-xpl']):
        if params['no-xpl'][idx]['key'] == 'ir_coder' :  params['no-xpl'][idx]['value'] = ENCODER
        if params['no-xpl'][idx]['key'] == 'server_path' :  params['no-xpl'][idx]['value'] = DEVICE_PATH
        if params['no-xpl'][idx]['key'] == 'ip_server' :  params['no-xpl'][idx]['value'] = DEVICE_IP_SERVER
        if params['no-xpl'][idx]['key'] == 'irtrans_ip' :  params['no-xpl'][idx]['value'] = DEVICE_IP_IRTRANS

    for idx, val in enumerate(params['xpl']):
        params['xpl'][idx]['value'] = DEVICE_NAME

    # go and create
    td.create_device(params)
    print "Device IRTrans Lan {0} configured".format(DEVICE_NAME) 
    
    print("Creating the irwsserver device...")
    td = TestDevice()
    params = td.get_params(client_id, "irtrans.irwsserver")
        # fill in the params
    params["device_type"] = "irtrans.irwsserver"
    params["name"] = "test_IRTrans_WS"
    params["reference"] = "IR WebSockect client"
    params["description"] = "Handle IR WebSockect modul"
    for idx, val in enumerate(params['no-xpl']):
        if params['no-xpl'][idx]['key'] == 'ir_coder' :  params['no-xpl'][idx]['value'] = ENCODER
        elif params['no-xpl'][idx]['key'] == 'ip_server' :  params['no-xpl'][idx]['value'] = DEVICE2_IP_SERVER
        elif params['no-xpl'][idx]['key'] == 'port_server' :  params['no-xpl'][idx]['value'] = DEVICE2_PORT_SERVER
        elif params['no-xpl'][idx]['key'] == 'ssl_activate' :  params['no-xpl'][idx]['value'] = DEVICE2_SSL
        elif params['no-xpl'][idx]['key'] == 'ssl_certificate' :  params['no-xpl'][idx]['value'] = DEVICE2_CERTIFICATE
        elif params['no-xpl'][idx]['key'] == 'ssl_key' :  params['no-xpl'][idx]['value'] = DEVICE2_KEY
        elif params['no-xpl'][idx]['key'] == 'ir_repeat' :  params['no-xpl'][idx]['value'] = 3
        elif params['no-xpl'][idx]['key'] == 'ir_tolerance' :  params['no-xpl'][idx]['value'] = 150
        elif params['no-xpl'][idx]['key'] == 'ir_large_tolerance' :  params['no-xpl'][idx]['value'] = 300
        elif params['no-xpl'][idx]['key'] == 'ir_max_out' :  params['no-xpl'][idx]['value'] = 10

    for idx, val in enumerate(params['xpl']):
        params['xpl'][idx]['value'] = DEVICE2_NAME

    # go and create
    td.create_device(params)
    print "Device irwsserver {0} configured".format(DEVICE2_NAME) 
    
if __name__ == "__main__":
    create_device()
