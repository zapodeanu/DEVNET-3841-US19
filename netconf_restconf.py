#!/usr/bin/env python2


# developed by Gabi Zapodeanu, TME, ENBU, Cisco Systems


import requests
import urllib3
import ncclient
import xml
import xml.dom.minidom
import json
import utils

from ncclient import manager

from urllib3.exceptions import InsecureRequestWarning
from requests.auth import HTTPBasicAuth  # for Basic Auth

urllib3.disable_warnings(InsecureRequestWarning)  # Disable insecure https warnings


def get_netconf_hostname(ios_xe_host, ios_xe_port, ios_xe_user, ios_xe_pass):
    """
    This function will retrieve the device hostname via NETCONF
    :param ios_xe_host: device IPv4 address
    :param ios_xe_port: NETCONF port
    :param ios_xe_user: username
    :param ios_xe_pass: password
    :return: IOS XE device hostname
    """

    with manager.connect(host=ios_xe_host, port=ios_xe_port, username=ios_xe_user,
                         password=ios_xe_pass, hostkey_verify=False,
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


def get_restconf_hostname(ios_xe_host, ios_xe_user, ios_xe_pass):
    """
    This function will retrieve the device hostname via RESTCONF
    :param ios_xe_host: device IPv4 address
    :param ios_xe_user: username
    :param ios_xe_pass: password
    :return: IOS XE device hostname
    """

    dev_auth = HTTPBasicAuth(ios_xe_user, ios_xe_pass)
    url = 'https://' + ios_xe_host + '/restconf/data/Cisco-IOS-XE-native:native/hostname'
    header = {'Content-type': 'application/yang-data+json', 'accept': 'application/yang-data+json'}
    response = requests.get(url, headers=header, verify=False, auth=dev_auth)
    hostname_json = response.json()
    hostname = hostname_json['Cisco-IOS-XE-native:hostname']
    return hostname


def get_netconf_int_oper_data(interface, ios_xe_host, ios_xe_port, ios_xe_user, ios_xe_pass):
    """
    This function will retrieve the operational data for the interface via NETCONF
    :param interface: interface name
    :param ios_xe_host: device IPv4 address
    :param ios_xe_port: NETCONF port
    :param ios_xe_user: username
    :param ios_xe_pass: password
    :return: interface operational data in XML
    """

    with manager.connect(host=ios_xe_host, port=ios_xe_port, username=ios_xe_user,
                         password=ios_xe_pass, hostkey_verify=False,
                         device_params={'name': 'default'},
                         allow_agent=False, look_for_keys=False) as m:
        # XML filter to issue with the get operation
        # IOS-XE 16.6.2+        YANG model called "ietf-interfaces"

        interface_state_filter = '''
                                            <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                                                <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                                                    <interface>
                                                        <name>''' + interface + '''</name>
                                                    </interface>
                                                </interfaces-state>
                                            </filter>
                                        '''

        try:
            result = m.get(interface_state_filter)
            oper_data = xml.dom.minidom.parseString(result.xml)
        except:
            oper_data = 'unknown'
        return oper_data


def get_restconf_int_oper_data(interface, ios_xe_host, ios_xe_user, ios_xe_pass):
    """
    This function will retrieve the operational data for the interface via RESTCONF
    :param interface: interface name
    :param ios_xe_host: device IPv4 address
    :param ios_xe_user: username
    :param ios_xe_pass: password
    :return: interface operational data in JSON
    """

    # encode the interface URI: GigabitEthernet0/0/2 - http://10.104.50.97/restconf/data/Cisco-IOS-XE-native:native/interface/GigabitEthernet=0%2F0%2F2
    # ref.: https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/166/b_166_programmability_cg/restconf_prog_int.html

    interface_uri = interface.replace('/', '%2F')
    interface_uri = interface_uri.replace('.', '%2E')
    dev_auth = HTTPBasicAuth(ios_xe_user, ios_xe_pass)
    url = 'https://' + ios_xe_host + '/restconf/data/ietf-interfaces:interfaces-state/interface=' + interface_uri
    print('The RESTCONF API resource is located: ' + url)
    header = {'Content-type': 'application/yang-data+json', 'accept': 'application/yang-data+json'}
    response = requests.get(url, headers=header, verify=False, auth=dev_auth)
    interface_info = response.json()
    oper_data = interface_info['ietf-interfaces:interface']
    return oper_data


def get_restconf_capabilities(ios_xe_host, ios_xe_user, ios_xe_pass):
    """
    This function will retrieve the device capabilities via RESTCONF
    :param ios_xe_host: device IPv4 address
    :param ios_xe_user: username
    :param ios_xe_pass: password
    :return: device capabilities
    """
    dev_auth = HTTPBasicAuth(ios_xe_user, ios_xe_pass)
    url = 'https://' + ios_xe_host + '/restconf/data/netconf-state/capabilities'
    header = {'Content-type': 'application/yang-data+json', 'accept': 'application/yang-data+json'}
    response = requests.get(url, headers=header, verify=False, auth=dev_auth)
    capabilities_json =  response.json()
    return capabilities_json['ietf-netconf-monitoring:capabilities']

