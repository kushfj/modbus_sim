#!/usr/bin/env python

# import library modules
from pymodbus.client import AsyncModbusTcpClient

import argparse
import logging
import asyncio


# declare contants
IP_ADDR = '127.0.0.1'
TCP_PORT = 502

COMMS_NAME='vPLC simulation'

LOG_FILE = 'proto_client.log'


# declare global variables - this is a bad things, but...
logging.basicConfig(filename=LOG_FILE, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
LOGGER = logging.getLogger(__name__)


def get_modbus_client(ipaddr:str = IP_ADDR, port:int = TCP_PORT):
    LOGGER.debug('get_modbus_client')

    # check parameters
    if not ipaddr or not port or int(port) < 0 or int(port) > 65535:
        LOGGER.error('get_modbus_client: ipaddr or port not specified or invalid')
        return None
    
    # declare local variables
    modbus_client = AsyncModbusTcpClient(
            host=ipaddr,
            port=port,
            name=COMMS_NAME,
            reconnect_delay = 100, # 500ms max delay before retrying
            reconnect_delay_max = 500, # 500ms max delay before retrying
            timeout = 30, # 30s before timing out
            retries = 3, # re-try 3 time before giving up
            )

    return modbus_client


async def modbus_poll(modbus_tcp_cient):
    LOGGER.debug('modbus_poll')

    # check parameters
    assert modbus_tcp_cient

    # TODO: do something sensible here
    for i in range (10):
        LOGGER.info('modbus_poll: reading coil 32, 1-bit')
        rr = await modbus_tcp_cient.read_coils(32, 1, slave=1)
        LOGGER.info('modbus_poll: reading holding register 4, 2-words, so we get reg4 and reg5 values')
        rr = await modbus_tcp_cient.read_holding_registers(4, 2, slave=1)


async def run_modbus_client(ipaddr:str = IP_ADDR, port:int = TCP_PORT):
    LOGGER.debug('run_modbus_client')

    # check parameters
    if not ipaddr or not port or int(port) < 0 or int(port) > 65535:
        LOGGER.error('run_modbus_client: ipaddr or port not specified or invalid')
        return None

    modbus_client = get_modbus_client(ipaddr, port)
    if not modbus_client:
        LOGGER.error('run_modbus_client: unable to get modbus client')
        return

    await modbus_client.connect()
    if not modbus_client.connected:
        LOGGER.error(f'run_modbus_client: unable to connect to socket {ipaddr}:{port}')
        return

    # modbus poll
    await modbus_poll(modbus_client)

    # close connection
    modbus_client.close()


async def run_main():
    LOGGER.debug('run_main')

    # parse command line arguments
    parser = argparse.ArgumentParser(
                    prog='proto_client',
                    description='Prototype modbus client/master',
                    epilog='This client is intended to run a prototype modbus client')
    parser.add_argument('-i', '--ipaddr', help='ip address to poll, default = "127.0.0.1"') # the IP address to bind to, default 127.0.0.1
    parser.add_argument('-p', '--port', help='port to connect to, default = 502') # the port to bind to, default 502
    args = parser.parse_args()

    # declare local variables
    ipaddr = None
    port = None

    # check parameters
    if not args.ipaddr:
        ipaddr = IP_ADDR
    else:
        ipaddr = args.ipaddr

    if not args.port:
        port = TCP_PORT
    else:
        port = args.port

    await run_modbus_client(ipaddr, port)


if __name__ == "__main__":
    LOGGER.debug('proto_client starting')
    asyncio.run(run_main(), debug=True)
    LOGGER.debug('proto_client stopped')
