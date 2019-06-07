#!/usr/bin/env python2


# developed by Gabi Zapodeanu, TME, ENBU, Cisco Systems


import cli
from cli import cli, execute, configure

from config import FOLDER_NAME

import os
os.chdir(FOLDER_NAME)


# This code is needed to run after every change made to the configuration of the switch


# check if 'Config_Files' folder exists and creates one if it does not

if not os.path.exists('Config_Files'):
    os.makedirs('Config_Files')

    # add additional vty lines, two required for EEM
    configure('no ip http active-session-modules none ; line vty 0 15 ; length 0 ; transport input ssh ; exit')

    print('Created additional vty lines')

    f = open('vasi_config.txt', 'r')
    cli_commands = f.read()
    configure(cli_commands)
    f.close()

    print('Configured VASI interfaces, vrf R, Loopback111, and routing')


    f = open('monitor_route_applet.txt', 'r')
    cli_commands = f.read()
    configure(cli_commands)
    f.close()

    print('Configured EEM applet')


# save baseline running configuration

output = execute('show run')

filename = 'Config_Files/base-config'

f = open(filename, 'w')
f.write(output)
f.close()

execute('copy run start')

execute('send log End of save_base_config.py Application Run')
print('\nEnd of save_base_config.py Application Run')
