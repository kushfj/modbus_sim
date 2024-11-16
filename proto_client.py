#!/usr/bin/env python


# import library modules

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian


import argparse
import logging
import asyncio
import random


# declare contants

NUM_RUNS = 900000 # number of times to poll/invoke handlers

IP_ADDR = '127.0.0.1'
TCP_PORT = 502
SLAVE_ID = 0x01

COMMS_NAME='vPLC simulation'

# TODO: set to realistic values similar to actual PLC hardware, theoratical size 10K
# TODO: move these constants into a shared module, its duplicated on the client and serber and is currently manullay kept in sync - likely to break something in the future
# TODO: make log level a configurable parameter and accept it as a cli argument
# TODO: make type of client calls parameterised i.e., all for all, coil for read coils only, etc.

MAX_COIL_REG = 64
MAX_HOLD_REG = 60
MAX_DISCRETE_IN_REG = 123 
MAX_INPUT_REG = 123 # max is 125-word i.e. 256-bytes, but for modbus TCP this becomes 123-words

LOG_FILE = 'proto_client.log'


# declare global variables - this is a bad things, but...

# TODO: make logfile specific to slave and slave_id - init in main()
logging.basicConfig(filename=LOG_FILE, encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
LOGGER = logging.getLogger(__name__)

# TODO: modify handler functions to split read and write


def get_modbus_client(ipaddr:str = IP_ADDR, port:int = TCP_PORT):
    LOGGER.debug('get_modbus_client')

    # check parameters
    if not ipaddr or not port or int(port) < 0 or int(port) > 65535:
        msg = f'get_modbus_client: ipaddr: {ipaddr} or port {port} not specified or invalid'
        LOGGER.error(msg)
        print('[!] {msg}')
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

    # return the modbus client handle
    return modbus_client


async def modbus_poll_holding_register_handler(modbus_tcp_client, slave_id:int = SLAVE_ID):
    LOGGER.debug(f'modbus_poll_holding_register_handler: slave={slave_id}')

    # check parameters
    assert modbus_tcp_client
    assert slave_id

    # declare local variables
    start_address = 0x01
    num_holding_reg = 1
    modbus_response = None
    value = None
    fifty_fifty = [True,False]

    # read holding registers
    """
    A maximum of 125 registers in RTU mode resp. 60 registers in ASCII mode can be read with one message. The holding registers contain indications, measurand values and metered measurands
    """
    try:
        #print('[*] reading holding registers')
        print('.', end='', flush=True)
        modbus_response = await modbus_tcp_client.read_holding_registers(
                address=start_address, 
                count=num_holding_reg, 
                slave=slave_id
            )
    except ModbusException as me:
        msg = f'modbus_poll_holding_register_handler: unable to read holding registers at {start_address} count {num_holding_reg} for {slave_id}'
        LOGGER.error(msg)
        print(f'[!] {msg}')

    if modbus_response and not modbus_response.isError():
        LOGGER.info(f'modbus_poll_holding_register_handler: read holding register at: {start_address} count: {num_holding_reg} for: {slave_id}')
    else:
        msg = f'modbus_poll_holding_register_handler: error reading holding register at: {start_address} count: {num_holding_reg} for: {slave_id}'
        LOGGER.error(msg)
        print(f'[!] {msg}')

    # randomly write holding registers
    write_holding_registers = random.choice(fifty_fifty)
    if write_holding_registers:
        try:
            # random number of holdering registers between 1 and 60
            num_holding_reg = random.choice(range(1,MAX_HOLD_REG+1)) 

            # create random list of floats
            builder = BinaryPayloadBuilder(byteorder=Endian.LITTLE)
            for i in range(num_holding_reg):
                builder.add_32bit_float(random.uniform(0.0, 50.0))
            value = builder.build()

            # attempt to write holding register
            #print('[*] writing holding registers')
            print('.', end='')
            await modbus_tcp_client.write_registers(address=start_address, values=value, slave=slave_id)
            LOGGER.info(f'modbus_poll_holding_register_handler: wrote: {value} at: {start_address} for slave: {slave_id}')
        except ModbusException as me:
            msg = f'modbus_poll_holding_register_handler: unable to write holdering register: {value} at: {start_address} for slave: {slave_id}'
            LOGGER.error(msg)
            print(f'[!] {msg}')


async def modbus_poll_discrete_input_handler(modbus_tcp_client, slave_id:int = SLAVE_ID):
    LOGGER.debug(f'modbus_poll_discrete_input_handler: slave={slave_id}')

    # check parameters
    assert modbus_tcp_client
    assert slave_id

    # declare local variables
    start_address = 0x01
    num_registers = None
    modbus_response = None
    value = None

    # randomise the number of registers to read
    num_registers = random.randint(1,MAX_DISCRETE_IN_REG) # TODO: investigate if random.choice or random.randint should be used

    # read discrete input registers
    try:
        #print('[*] reading discrete input')
        print('.', end='')
        modbus_response = await modbus_tcp_client.read_discrete_inputs(
                address=start_address, 
                count=num_registers, 
                slave=slave_id
            )
    except ModbusException as me:
        msg = f'modbus_poll_discrete_input_handler: unable to read: {num_registers} discrete input registers at: {start_address} for slave: {slave_id}'
        LOGGER.error(msg)
        print(f'[!] {msg}')

    if modbus_response and not modbus_response.isError():
        LOGGER.info(f'modbus_poll_discrete_input_handler: read: {num_registers} discrete input registers at: {start_address} for slave: {slave_id}')
    else:
        msg= f'modbus_poll_discrete_input_handler: error reading: {num_registers} discrete input registers at: {start_address} for slave: {slave_id}'
        LOGGER.error(msg)
        print(f'[!] {msg}')


async def modbus_poll_input_registers_handler(modbus_tcp_client, slave_id:int = SLAVE_ID):
    LOGGER.debug(f'modbus_poll_input_registers_handler: slave={slave_id}')

    # check parameters
    assert modbus_tcp_client
    assert slave_id

    # declare local variables
    start_address = 0x01
    num_registers = None
    modbus_response = None
    value = None

    # randomise the number of registers to read
    num_registers = random.randint(1,MAX_INPUT_REG) 

    try:
        modbus_response = await modbus_tcp_client.read_input_registers(
                address=start_address, 
                count=num_registers, 
                slave=slave_id
            )
    except ModbusException as me:
        msg = f'modbus_poll_input_registers_handler: unable to read: {num_registers} input registers at: {start_address} for slave: {slave_id}'
        LOGGER.error(msg)
        print('!', end='', flush=True)
        return

    if modbus_response and not modbus_response.isError():
        LOGGER.info(f'modbus_poll_input_registers_handler: read: {num_registers} input registers at: {start_address} for slave: {slave_id}')
    else:
        msg = f'modbus_poll_input_registers_handler: error reading: {num_registers} input registers at: {start_address} for slave: {slave_id}'
        LOGGER.error(msg)
        print('!', end='', flush=True)



async def modbus_poll_coils_handler(modbus_tcp_client, slave_id:int = SLAVE_ID):
    LOGGER.debug(f'modbus_poll_coils_handler: slave={slave_id}')

    # check parameters
    assert modbus_tcp_client
    assert slave_id

    # declare local variables
    start_address = 0x01
    num_coils = 1
    modbus_response = None
    value = None
    fifty_fifty = [True,False]

    # read coils
    try:
        #print('[*] reading coils')
        print('.', end='')
        modbus_response = await modbus_tcp_client.read_coils(
                    address=start_address, 
                    count=num_coils, 
                    slave=slave_id
            )
    except ModbusException as me:
        msg = f'modbus_poll_coils_handler: unable to read: {num_coils} coils at: {start_address} for slave: {slave_id}'
        LOGGER.error(msg)
        print(f'[!] {msg}')

    if modbus_response and not modbus_response.isError():
        LOGGER.info(f'modbus_poll_coils_handler: read: {num_coils} coils at: {start_address}, response has {len(modbus_response.bits)}-bits for slave: {slave_id}')
    else:
        msg = f'modbus_poll_coils_handler: error reading: {num_coils} coils at: {start_address} for slave: {slave_id}'
        LOGGER.error(msg)
        print(f'[!] {msg}')

    # randomly write coils
    write_coils = random.choice(fifty_fifty)
    if write_coils:
        try:
            value = random.choice(fifty_fifty) # random value
            rand_len = random.choice(range(1,MAX_COIL_REG+1)) # random length from 1 to 64 bits 
            #print('[*] writing coils')
            print('.', end='')
            await modbus_tcp_client.write_coils(address=start_address, values=([value]*rand_len), slave=slave_id)
            LOGGER.info(f'modbus_poll_coils_handler: wrote: {rand_len} coils to: {value} at: {start_address} for slave: {slave_id}')
        except ModbusException as me:
            msg = f'modbus_poll_coils_handler: unable to write: {rand_len} coils to: {value} at: {start_address} for slave: {slave_id}'
            LOGGER.error(msg)
            print(f'[!] {msg}')


async def modbus_poll(modbus_tcp_client, slave_id:int = SLAVE_ID):
    LOGGER.debug('modbus_poll')

    # check parameters
    assert modbus_tcp_client

    # do client stuff
    # TODO - maybe thread these for more chaos
    # TODO - accept number of runs as a cli paramter, or run forever if nothing supplied
    print('[*] modbus master running: ', end='')
    for i in range(NUM_RUNS):
        await modbus_poll_coils_handler(modbus_tcp_client, slave_id)
        await modbus_poll_holding_register_handler(modbus_tcp_client, slave_id)
        await modbus_poll_discrete_input_handler(modbus_tcp_client, slave_id)
        await modbus_poll_input_registers_handler(modbus_tcp_client, slave_id)
    print('\n[+] done!')

    # TODO: do something sensible here
    #for i in range (10):
    #    LOGGER.info('modbus_poll: reading coil 32, 1-bit')
    #    rr = await modbus_tcp_client.read_coils(32, 1, slave=1)
    #    LOGGER.info('modbus_poll: reading holding register 4, 2-words, so we get reg4 and reg5 values')
    #    rr = await modbus_tcp_client.read_holding_registers(4, 2, slave=1)


async def run_modbus_client(ipaddr:str = IP_ADDR, port:int = TCP_PORT, slave_id:int = SLAVE_ID):
    LOGGER.debug(f'run_modbus_client: socket={ipaddr}:{port} slave={slave_id}')

    # check parameters
    if not ipaddr or not port or int(port) < 0 or int(port) > 65535:
        msg = f'run_modbus_client: ipaddr: {ipaddr} or port: {port} not specified or invalid'
        LOGGER.error(msg)
        print(f'[!] {msg}')
        return 
    if not slave_id or int(slave_id) < 1:
        msg = f'run_modbus_client: invalid modbus slave id: {slave_id}'
        LOGGER.error(msg)
        print(f'[!] {msg}')
        return 

    # get a modbus client reference
    modbus_client = get_modbus_client(ipaddr, port)
    if not modbus_client:
        LOGGER.error('run_modbus_client: unable to get modbus client')
        return

    # attempt connection to modbus slave
    await modbus_client.connect()
    if not modbus_client.connected:
        msg = f'run_modbus_client: unable to connect to socket {ipaddr}:{port}'
        LOGGER.error(msg)
        print(f'[!] {msg}')
        return 

    # modbus poll
    await modbus_poll(modbus_client, slave_id)

    # close connection
    modbus_client.close()


async def run_main():
    LOGGER.debug('run_main')

    # parse command line arguments
    parser = argparse.ArgumentParser(
                    prog='proto_client',
                    description='Prototype modbus client/master',
                    epilog='This client is intended to run a prototype modbus client')
    parser.add_argument('-i', '--ipaddr', help='ip address to poll, default = "127.0.0.1"') 
    parser.add_argument('-p', '--port', help='port to connect to, default = 502') 
    parser.add_argument('-s', '--slave', help='slave ID to connect to, default = 0x01') 
    args = parser.parse_args()

    # declare local variables
    ipaddr = None
    port = None
    slave_id = None

    # check parameters
    if not args.ipaddr:
        ipaddr = IP_ADDR
    else:
        ipaddr = args.ipaddr

    if not args.port:
        port = TCP_PORT
    else:
        port = args.port

    if not args.slave:
        slave_id = SLAVE_ID
    else:
        slave_id = int(args.slave)

    # run the client
    await run_modbus_client(ipaddr, port, slave_id)


if __name__ == "__main__":
    LOGGER.debug('proto_client starting')
    asyncio.run(run_main(), debug=True)
    LOGGER.debug('proto_client stopped')
