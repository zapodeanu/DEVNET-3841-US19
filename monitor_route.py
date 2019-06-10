#!/usr/bin/env python2


# developed by Gabi Zapodeanu, TME, Enterprise Networking, Cisco Systems


import json
import requests
import utils
import service_now_apis
import config
import netconf_restconf
import dnac_apis
import cli
import argparse


from requests.auth import HTTPBasicAuth

from config import SNOW_DEV
from config import IOS_XE_PASS, IOS_XE_USER
from config import DNAC_URL, DNAC_USER, DNAC_PASS
from config import FOLDER_NAME

from cli import cli, execute, configure

parser = argparse.ArgumentParser()
parser.description = 'The monitored route the application will alert on'
parser.add_argument('route')
args = parser.parse_args()
monitored_route = args.route


DNAC_AUTH = HTTPBasicAuth(DNAC_USER, DNAC_PASS)

global IOS_XE_HOST_IP, DEVICE_HOSTNAME, DEVICE_LOCATION

# retrieve the ios xe device management ip address, Gi0/0, not the VPG IP address
IOS_XE_HOST_IP = execute('sh run int gi1 | in ip address').split(' ')[3]

# retrieve the device hostname using RESTCONF
DEVICE_HOSTNAME = netconf_restconf.get_restconf_hostname(IOS_XE_HOST_IP, IOS_XE_USER, IOS_XE_PASS)
print(str('\nThe device hostname: ' + DEVICE_HOSTNAME))

# create a new Service Now incident
description = 'Monitored route: ' + monitored_route + ' Lost, device hostname: ' + DEVICE_HOSTNAME

comment = 'The device with the name: ' + DEVICE_HOSTNAME + ' has detected the loss of a critical route'
comment += '\n\nThe route: ' + monitored_route + ' - is missing from the routing table'

snow_incident = service_now_apis.create_incident(description, comment, SNOW_DEV, 1)

# The following commands to be use when Cisco DNA Center is available

# get DNA C AUth JWT token
dnac_token = dnac_apis.get_dnac_jwt_token(DNAC_AUTH)

# get device location
DEVICE_LOCATION = dnac_apis.get_device_location(DEVICE_HOSTNAME, dnac_token)
print(str("\nDevice Location: " + DEVICE_LOCATION))

# get device details
epoch_time = utils.get_epoch_current_time()
device_details = dnac_apis.get_device_health(DEVICE_HOSTNAME, epoch_time, dnac_token)
device_sn = device_details['serialNumber']
device_management_ip = device_details['managementIpAddr']
device_family = device_details['platformId']
device_os_info = device_details['osType'] + ',  ' + device_details['softwareVersion']
device_health = device_details['overallHealth']

comment += "\nDevice management IP address: " + device_management_ip
comment += "\n\nDevice location: " + DEVICE_LOCATION
comment += "\nDevice family: " + device_family
comment += "\nDevice OS info: " + device_os_info
comment += "\nDevice Health: " + str(device_health) + "/10"

print(comment)

service_now_apis.update_incident(snow_incident, comment, SNOW_DEV)

execute('send log End of monitor_route.py Application Run')
print(str('\n\nEnd of monitor_route.py Application Run'))
