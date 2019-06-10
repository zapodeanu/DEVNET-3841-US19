

# developed by Gabi Zapodeanu, TME, Enterprise Networking, Cisco Systems


import requests
import ncclient
import xml
import xml.dom.minidom
import json

from ncclient import manager

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.auth import HTTPBasicAuth  # for Basic Auth
from config import IOS_XE_USER, IOS_XE_PASS, IOS_XE_HOST, IOS_XE_PORT


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # Disable insecure https warnings


ROUTER_AUTH = HTTPBasicAuth(IOS_XE_USER, IOS_XE_PASS)


def get_netconf_int_oper_status(interface):
    """
    This function will retrieve the IPv4 address configured on the interface via NETCONF
    :param interface: interface name
    :return: int_ip_add: the interface IPv4 address
    """

    with manager.connect(host=IOS_XE_HOST, port=IOS_XE_PORT, username=IOS_XE_USER,
                         password=IOS_XE_PASS, hostkey_verify=False,
                         device_params={'name': 'default'},
                         allow_agent=False, look_for_keys=False) as m:
        # XML filter to issue with the get operation
        # IOS-XE 16.6.2+        YANG model called "ietf-interfaces"

        interface_state_filter = '''
                                    <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                                        <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                                            <interface>
                                                <name>''' + interface + '''</name>
                                                <oper-status/>
                                            </interface>
                                        </interfaces-state>
                                    </filter>
                                '''

        result = m.get(interface_state_filter)
        xml_doc = xml.dom.minidom.parseString(result.xml)
        int_info = xml_doc.getElementsByTagName('oper-status')
        try:
            oper_status = int_info[0].firstChild.nodeValue
        except:
            oper_status = 'unknown'
        return oper_status


def get_restconf_int_oper_data(interface):

    url = 'https://' + IOS_XE_HOST + '/restconf/data/interfaces-state/interface=' + interface
    header = {'Content-type': 'application/yang-data+json', 'accept': 'application/yang-data+json'}
    response = requests.get(url, headers=header, verify=False, auth=ROUTER_AUTH)
    interface_info = response.json()
    oper_data = interface_info['ietf-interfaces:interface']
    return oper_data


def get_netconf_hostname():
    with manager.connect(host=IOS_XE_HOST, port=IOS_XE_PORT, username=IOS_XE_USER,
                         password=IOS_XE_PASS, hostkey_verify=False,
                         device_params={'name': 'default'},
                         allow_agent=False, look_for_keys=False) as m:
        # XML filter to issue with the get operation
        # IOS-XE 16.6.2+        YANG model called "Cisco-IOS-XE-native"

        hostname_filter = '''
                                <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                                    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                                        <hostname/>
                                    </native>
                                </filter>
                          '''

        result = m.get(hostname_filter)
        xml_doc = xml.dom.minidom.parseString(result.xml)
        int_info = xml_doc.getElementsByTagName('hostname')
        try:
            hostname = int_info[0].firstChild.nodeValue
        except:
            hostname = 'unknown'
        return hostname


def get_restconf_hostname():
    url = 'https://' + IOS_XE_HOST + '/restconf/data/Cisco-IOS-XE-native:native/hostname'
    header = {'Content-type': 'application/yang-data+json', 'accept': 'application/yang-data+json'}
    response = requests.get(url, headers=header, verify=False, auth=ROUTER_AUTH)
    hostname_json = response.json()
    hostname = hostname_json['Cisco-IOS-XE-native:hostname']
    return hostname



oper_data = get_restconf_int_oper_data('GigabitEthernet1')
print('Interface Operational Data via RESTCONF: \n')
print(json.dumps(oper_data, indent=4, separators=(' , ', ' : ')))

# print(str('Device Hostname via NETCONF: \n' + get_netconf_hostname()))

print(str('\nInterface Operational Status via NETCONF: \n' + get_netconf_int_oper_status('GigabitEthernet2')))

print(str('\nDevice Hostname via RESTCONF: \n' + get_restconf_hostname()))
