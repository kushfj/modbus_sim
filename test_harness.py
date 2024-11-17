#!/usr/bin/env python

#
# import library modules
#

import sys
import os
import argparse
import logging
import time
import ipaddress
import random
import math


### README
# This version of the script has only been tested on Ubuntu server
# - Install Virtuabox Ubuntu server minimal VM - sudo apt update && sudo apt full-upgrade
# - Install Virtualbox Guest Additions - sudo apt install virtualbox-guest-additions-iso virtualbox-guest-utils virtualbox-dkms
# - Reboot
# - Install pip - sudo apt install python3-pip
# - Install git - sudo apt install git
# - Install Network Tools - sudo apt install net-tools
# - Clone repository
# - Install requirements
# - Run test harness for slaves/servers
# - Run test harness for masters/clients


# TODO
# * Process slave IPs and chunks so that source IP address can be optimised for specific subnets
# * Parametereris subnet so that master and slave subnets can be specified on the command line
# * Parameterise hardware interface names instead of using globals
# * Parameterise output filenames for master script, cleanup scripts and slave script names 
# * Dynamically determine full path for commands based on Linux distribution e.g. ifconfig, route, etc.


#
# declare global variables - yes I know this is terrible, but meh for now!
#

IFACE='enp0s3'
DEFAULT_SLAVES_LIST_FILENAME='slaves.txt'
LINE_SEPARATOR='\n' # TODO - use platform detection to determine separator

LOGGER = None
SLAVE_LIST_HANDLE = None


#
# function definitions
#

def append_to_slave_list(ip_addr : str, slaves_list_filename : str = DEFAULT_SLAVES_LIST_FILENAME):
    """
    Function to write the specified IP address to the slaves list file. If not slaves list filename is specified the default DEFAULT_SLAVES_LIST_FILENAME filename is used. If no IP address is specified then the function simply returns
    """
    # check parameters - TODO: validate IP address
    if not ip_addr:
        return

    # declare variables
    global SLAVE_LIST_HANDLE

    # get a handle to the file if we dont have one
    if not SLAVE_LIST_HANDLE:

        # get the slaves list filename
        if not slaves_list_filename:
            slaves_list_filename = DEFAULT_SLAVES_LIST_FILENAME

        # attempt to open file for appending 
        try: 
            SLAVE_LIST_HANDLE = open(slaves_list_filename, 'a')
        except OSError:
            msg = f'# [!] unable to opern file: {slaves_list_filename} for writing'
            return

    # write the ip address to the file
    SLAVE_LIST_HANDLE.write(f'{ip_addr}{LINE_SEPARATOR}')



def setup_logging(logfile_name:str = 'test_harness.log'):
    """
    Function to set-up logging for this script
    """
    # declare variables
    global LOGGER

    logging.basicConfig(filename=logfile_name, encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s') 
    LOGGER = logging.getLogger(__name__)
    return


def log_info(msg:str, show:bool = True):
    """
    Function to log INFO entries to log and print to standard out (default) if show is True or be quiet if False
    """
    # check parameters
    if not msg:
        print('# [!] log: cannot log an empty log entry')
        return

    # declare variables
    global LOGGER

    if not LOGGER:
        setup_logging()

    LOGGER.info(msg)
    if show:
        print(msg)
    return


def slaves_ready():
    """
    Function to prompt user to confirm that slaves/servers are ready
    """
    # declare local variables
    cont = False # continue flag set to False

    # loop
    while True:
        resp = input('Are the slaves ready? y or n\n')
        if resp in ['y','Y']:
            cont = True
            break
        else:
            print('OK, sleep for 5 seconds')
            time.sleep(5)


    return cont


def is_valid_slaves_list(slaves_list: str ) -> []:
    """
    Function to verify if the slaves list file is valid
    """
    # declare local variables
    is_valid = [] # list if valid IP addresses
    line_num = 0 # number of lines parsed
    found_ip = 0 # number of IP addresses found

    # check parameters
    if not slaves_list:
        log_info(f'# [!] is_valid_slaves_list: slaves list {slaves_list} is invalid')
    # check if file exists and is readable
    elif not os.path.isfile(slaves_list):
        log_info(f'# [!] is_valid_slaves_list: {slaves_list} is not a valid file')
    # check file contents
    else:
        # check if file is empty
        file_size = os.path.getsize(slaves_list)
        if not file_size:
            log_info(f'# [!] is_valid_slaves_list: file {slaves_list} is empty')
        # check that file only contains IP addresses
        else:
            file_handle = open(slaves_list, 'r')
            print('# ', end='')
            for line in file_handle:
                line_num += 1
                line = line.strip()
                if not line: 
                    #log_info(f'# [!] is_valid_slaves_list: empty line on line {line} in {slaves_list}, skipping line')
                    print('!', end='')
                    continue
                else:
                    try:
                        ipaddr = ipaddress.ip_address(line)
                        is_valid.append(line)
                        found_ip += 1
                        print('.', end='')
                    except ValueError as ve: 
                        #log_info(f'# [!] is_valid_slaves_list: {line} not a valid IP address, skipping line')
                        print('!', end='')
                        continue

            print('')
            file_handle.close

    # remove duplicates and return list
    is_valid = list(set(is_valid))
    if is_valid:
        log_info(f'# [!] is_valid_slaves_list: found {len(is_valid)} unique from {found_ip} IPs in {line_num} lines')

    return is_valid


def chunkify(big_list : [], chunk_size : int = 1):
    """
    Function to return list of list of at most chunk_size of a big_list
    """
    # check paramaters
    if not big_list or chunk_size < 1:
        return []

    # looping till length of big_list
    for i in range(0, len(big_list), chunk_size): 
        yield big_list[i:i + chunk_size]


def create_mac_addr() -> str:
    """
    Function to generate Ethernet MAC address
    https://stackoverflow.com/questions/8484877/mac-address-generator-in-python

    Siemens = 00:1B:1B
    Rockwell = 00:00:BC
    """
    mac = [ 0x00, 0x1B, 0x1B, # siemens
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff) ]
    return str(':'.join(map(lambda x: "%02x" % x, mac)))


#
# main entry point
#

def main():
    # declare variables
    global SLAVE_LIST_HANDLE
    slaves_list = None

    # parse command line arguments
    parser = argparse.ArgumentParser(
                    prog='test_harness.py',
                    description='Test harness for the MODBUS simulator',
                    epilog='This test harness script is intended to setup the client or server to run the modbus simulation')
    parser.add_argument('-s', '--setup',
                        type=str,
                        choices=['client', 'master', 'server', 'slave'],
                        help='set-up client or server using the test harness script')
    parser.add_argument('-n', '--num',
                        type=int,
                        default=1,
                        help='number of masters or slaves to instantiate, ignored for server/slave setup, max is 254, default="1"')
    parser.add_argument('-l', '--slaves_list',
                        type=str,
                        default=DEFAULT_SLAVES_LIST_FILENAME,
                        help=f'file containing line separated list of IP addresses for slaves for masters to poll, ignored for master/client setup, default="{DEFAULT_SLAVES_LIST_FILENAME}"')
    args = parser.parse_args()


    # check set-up type
    if not args.setup:
        log_info('# [!] main: must specify setup type to setup a client or a server')
        #sys.exit() # DEBUG - Remove this in prod
    elif args.setup == 'client' or args.setup == 'master':
        # check if slaves list specified
        if not args.slaves_list:
            log_info('# [!] main: slaves list must be supplied for master set-up')
            #sys.exit() # DEBUG - Remove this in prod
            return # DEBUG

        # get slaves list
        slaves = is_valid_slaves_list(args.slaves_list)
        if not slaves:
            log_info('# [!] main: slaves list must have valid IP addresses')
            #sys.exit() # DEBUG - Remove this in prod
            return # DEBUG

        # run harness to setup client/master
        log_info('# [+] main: preparing to run harness for client/master')
        
        # create virtual box host - TODO: implement this
        # check and install python - TODO: implement this
        # copy the modbus prototypes onto the VM - TODO: implement this

        # split list into number of hosts per master
        if not args.num or args.num < 1:
            num= 1
        elif args.num > 254:
            num = 254
        else:
            num = args.num
        num_per_chunk = math.ceil(len(slaves)/num)
        slave_chunks = list(chunkify(slaves, num_per_chunk))

        # generate commands to create sub-interfaces on VM for each master, we iterate using the slave_chunks in case the number of chunks is less than the number of masters specified
        for i in range(len(slave_chunks)):
            mac_addr = create_mac_addr()
            ip_addr = f'10.10.10.{i+1}'

            # create sub-interface - TODO: accept network address as parameter
            #command = f'ifconfig {IFACE}.{i+1} hw ether {mac_addr} {ip_addr} netmask 255.0.0.0 up'

            command = f'sudo /usr/sbin/ifconfig {IFACE}:{i+1} {ip_addr} hw ether {mac_addr} up'
            print(command)

            # delete the route created 
            command = f'sudo /usr/sbin/route del -net 10.0.0.0 netmask 255.0.0.0 dev {IFACE}.{i+1}'
            print(command)

            # process each slave in the current chunk
            for slave_ip in slave_chunks[i]:

                # add static route for slave via the current sub-interface
                command = f'sudo /usr/sbin/ip route add {slave_ip} dev {IFACE}.{i+1}'
                print(command)

                # execute the modbus prototype server on each sub-interface
                command = f'sudo python3 proto_client.py -i {slave_ip} 502' 
                print(command)

        pass
    elif args.setup == 'server' or args.setup == 'slave':
        # run harness to setup server/slave
        log_info('# [+] main: preparing to run harness for server/slave')

        # create virtual box host - TODO: implement this
        # install python on virtual box host - TODO: implement this
        # copy the modbus prototypes onto the VM - TODO: implement this

        # get the number of slaves to instantiate
        if not args.num or args.num < 1:
            num= 1
        elif args.num > 254:
            num = 254
        else:
            num = args.num

        # check if slaves list specified
        if not args.slaves_list:
            slaves_list = DEFAULT_SLAVES_LIST_FILENAME
        else:
            slaves_list = args.slaves_list

        # generate commands to create sub-interfaces on VM for each slave
        for i in range(num):
            mac_addr = create_mac_addr()
            ip_addr = f'10.20.20.{i+1}'

            #command = f'ifconfig {IFACE}.{i+1} hw ether {mac_addr} {ip_addr} netmask 255.0.0.0 up'
            command = f'sudo /usr/sbin/ifconfig {IFACE}:{i+1} {ip_addr} hw ether {mac_addr} up'
            print(command)

            # execute the modbus prototype client on each sub-interface - and send to background
            command = f'sudo python3 proto_server.py -i {ip_addr} 502 &'
            print(command)

            # write the slave IP address to the slave list output file
            append_to_slave_list(ip_addr, slaves_list)


        # close the slaves list file
        SLAVE_LIST_HANDLE.close
        pass
    else:
        # technically should never ever get here since argparse should handle invalid options
        log_info(f'# [!] main: setup type {args.setup} not supported!')


if __name__ == "__main__":
    # check operating system
    if not sys.platform == 'linux':
        print(f'# [!] unsupported operating system, currently only runs on Linux')
        #sys.exit() # DEBUG - Remove this in prod

    # check if user is root
    if os.geteuid() != 0:
        print(f'# [!] must be run with root privileges')
        #sys.exit() # DEBUG - Remove this in prod

    # call the main function
    main()
