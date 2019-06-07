#!/usr/bin/env python2


# developed by Gabi Zapodeanu, TME, ENBU, Cisco Systems


import json
import requests
import pubnub
import utils
import service_now_apis
import cli
import logging


from config import PUB_KEY, SUB_KEY, CHANNEL
from config import IOS_XE_PASS, IOS_XE_USER
from config import DNAC_URL, DNAC_USER, DNAC_PASS

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNOperationType, PNStatusCategory

from requests.auth import HTTPBasicAuth

from config import SNOW_DEV

from cli import configure, execute, cli

import netconf_restconf
import dnac_apis


DNAC_AUTH = HTTPBasicAuth(DNAC_USER, DNAC_PASS)


def pubnub_init(device_uuid):

    # initialize the channel, with the device hostname

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = SUB_KEY
    pnconfig.publish_key = PUB_KEY
    pnconfig.ssl = False
    pnconfig.uuid = str(device_uuid)
    pubnub = PubNub(pnconfig)
    return pubnub



class MySubscribeCallback(SubscribeCallback):
    def status(self, pubnub, status):
        pass
        # The status object returned is always related to subscribe but could contain
        # information about subscribe, heartbeat, or errors
        # use the operationType to switch on different options
        if status.operation == PNOperationType.PNSubscribeOperation \
                or status.operation == PNOperationType.PNUnsubscribeOperation:
            if status.category == PNStatusCategory.PNConnectedCategory:
                # This is expected for a subscribe, this means there is no error or issue whatsoever
                print(str('\nSubscriber connected successfully\n\n'))
            elif status.category == PNStatusCategory.PNReconnectedCategory:
                # This usually occurs if subscribe temporarily fails but reconnects. This means
                # there was an error but there is no longer any issue
                print('Subscriber drop connectivity and reconnected successfully')
            elif status.category == PNStatusCategory.PNDisconnectedCategory:
                # This is the expected category for an unsubscribe. This means there
                # was no error in unsubscribing from everything
                print('Unsubscribing from everything was successful')
            elif status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
                # This is usually an issue with the internet connection, this is an error, handle
                # appropriately retry will be called automatically
                print('Connection lost, will try to reconnect')
            elif status.category == PNStatusCategory.PNAccessDeniedCategory:
                pass
                # This means that PAM does allow this client to subscribe to this
                # channel and channel group configuration. This is another explicit error
            else:
                pass
                # This is usually an issue with the internet connection, this is an error, handle appropriately
                # retry will be called automatically
        elif status.operation == PNOperationType.PNSubscribeOperation:
            # Heartbeat operations can in fact have errors, so it is important to check first for an error.
            # For more information on how to configure heartbeat notifications through the status
            # PNObjectEventListener callback, consult <link to the PNCONFIGURATION heartbeart config>
            if status.is_error():
                pass
                # There was an error with the heartbeat operation, handle here
            else:
                pass
                # Heartbeat operation was successful
        else:
            pass
            # Encountered unknown status type

    def presence(self, pubnub, presence):
        pass  # handle incoming presence data

    def message(self, pubnub, message):
        output_message = ''
        new_message = message.message
        print("\nNew message received: ")
        utils.pprint(new_message)
        device = new_message['device']
        if device == DEVICE_HOSTNAME or device == "all":
            command_type = new_message['command_type']
            incident = new_message['incident']

            # execute the configuration type of commands
            if command_type == 'config':
                try:
                    # parse the config commands or command
                    command = new_message['commands']
                    command_list = command.split('!')
                    comment = 'Configuration commands received: ' + command

                    # print to Python console, log to host device, and update ServiceNow
                    print(comment)
                    execute('send log WhatsOp:   ' + comment)
                    service_now_apis.update_incident(incident, comment, SNOW_DEV)

                    # submit the command using Python CLI, update incident with result
                    output = configure(command_list)
                    output_message = (str(output).replace('),', '),\n')).replace('[', ' ').replace(']', ' ')
                    print(output_message)
                    service_now_apis.update_incident(incident, output_message, SNOW_DEV)
                    status_message = 'Configuration command Successful'
                except:
                    status_message = "Configuration Command Executed"
            print(output_message)

            # execute the exec type of commands
            if command_type == 'exec':
                try:

                    # parse the exec command
                    command = new_message['commands']
                    comment = str('Exec command received: ' + command)

                    # print to Python console, log to host device, and update ServiceNow
                    print(comment)
                    execute('send log WhatsOp:   ' + comment)
                    service_now_apis.update_incident(incident, comment, SNOW_DEV)

                    # send the command to device using Python CLI
                    output_message = execute(str(command))
                    service_now_apis.update_incident(incident, output_message, SNOW_DEV)

                    # pretty print the command output to console
                    out_list = output_message.split('\n')
                    for items in out_list:
                        if items is not "":
                            print(items)
                    status_message = 'Successful'
                except:
                    status_message = 'Unsuccessful'

            print(str('\nCommand result:  ' + status_message))


def main():
    execute('send log Application subscriber_listener.py started')

    logging.basicConfig(
        filename='application_run.log',
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    global IOS_XE_HOST_IP, DEVICE_HOSTNAME, DEVICE_LOCATION

    # retrieve the ios xe device management ip address, Gi0/0
    IOS_XE_HOST_IP = execute('sh run int gi1 | in ip address').split(' ')[3]

    # retrieve the device hostname using RESTCONF
    DEVICE_HOSTNAME = netconf_restconf.get_restconf_hostname(IOS_XE_HOST_IP, IOS_XE_USER, IOS_XE_PASS)
    print(str('\nThe device hostname: ' + DEVICE_HOSTNAME))

    """
    
    The following commands are if Cisco DNA Center is available
    
    # get DNA C AUth JWT token
    dnac_token = dnac_apis.get_dnac_jwt_token(DNAC_AUTH)
    DEVICE_LOCATION = dnac_apis.get_device_location(DEVICE_HOSTNAME, dnac_token)
    print(str("\nDevice Location: " + DEVICE_LOCATION))
    
    """

    # init the PubNub channel
    pubnub = pubnub_init(DEVICE_HOSTNAME)

    pubnub.add_listener(MySubscribeCallback())
    pubnub.subscribe().channels(CHANNEL).execute()


if __name__ == '__main__':
    main()
