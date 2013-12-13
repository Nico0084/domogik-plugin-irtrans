#!/usr/bin/python
#-*- coding: utf-8 -*-create_device.py

### configuration ######################################
REST_URL="http://192.168.1.195:40405"
HOST="vmdomogik0"
DEVICE_NAME="IRTrans_1"
DEVICE_PATH = "/usr/local/irtrans"
DEVICE_IP_SERVER = "localhost"
DEVICE_IP_IRTRANS = "162.168.0.175"
##################################################

from domogik.tests.common.testdevice import TestDevice
from domogik.common.utils import get_sanitized_hostname

def create_device():
    ### create the device, and if ok, get its id in device_id
    print("Creating the device...")
    td = TestDevice()
    print 'host :',  get_sanitized_hostname()
    device_id = td.create_device("plugin-irtrans.{0}".format(get_sanitized_hostname()), "test_IRTrans_Lan", "irtrans_lan.device")
    print "Device created"
    td.configure_global_parameters({"device" : DEVICE_NAME, "server_path" : DEVICE_PATH, "ip_server": DEVICE_IP_SERVER, "irtrans_ip": DEVICE_IP_IRTRANS})
    print "Device configured" 

if __name__ == "__main__":
    create_device()


# TODO : recup de la config rest
# TODO : passer les parametres a la fonction
# TODO : renommer le fichier pour pouvoir importer la fonction en lib
# TODO : create generic functions for device creation and global parameters
