#!/usr/bin/env python

# import library modules
from pymodbus.server import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext
from pymodbus.datastore import ModbusServerContext

import argparse
import logging
import asyncio


# declare contants
# TODO: set to realistic values similar to actual PLC hardware, theoratical size 10K
#REG_SIZE = 3 # register size for coils, etc to use using init.
MAX_COIL_REG_SIZE = 64
MAX_HOLD_REG_SIZE = 60
MAX_DISCRETE_IN_REG_SIZE = 123 
MAX_INPUT_REG_SIZE = 123


"""
General modbus registers

| Register Type | Address Range | Data Type        | Typical Data Size | R/W |
| ---           | ---           | ---              | ---               | --- |
| Digital output| 1–9999        | Coil             | 1 bit             | RW  |
| Digital input | 10001–19999   | Discrete input   | 1 bit             | RO  |
| Analog input  | 30001–39999   | Input register   | 16 bits           | RO  |
| Analog output | 40001–49999   | Holding register | 16 bits           | RW  |


General modbus function codes

| Function Code | Description                    | Function Type |
| ---           | ---                            | ---           |
| 0x01          | Read coil status               | Read          |
| 0x02          | Read discrete input status     | Read          |
| 0x03          | Read holding registers         | Read          |
| 0x04          | Read input registers           | Read          |
| 0x05          | Force single coil              | Write         |
| 0x06          | Preset single holding register | Write         |
"""

DEV_VERSION = '0.0'
DEV_MODEL_NAME = 'PyVirtPLC'
DEV_PROD_CODE = 'vPLC'
DEV_PROD_NAME = 'Virtual PLC Server'
DEV_USER_APP_NAME = 'PLC Simulator'
DEV_VENDOR_NAME = "Python"
DEV_VENDOR_URL = 'https://github.com/kushfj/modbus_sim'

IP_ADDR = '127.0.0.1'
TCP_PORT = 502
SLAVE_ID = 0x01

LOG_FILE = 'proto_server.log'


# declare global variables - this is a bad things, but...
logging.basicConfig(filename=LOG_FILE, encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
LOGGER = logging.getLogger(__name__)
#LOGGER.setLevel(logging.INFO)


def get_modbus_data_model():
    LOGGER.debug('get_modbus_data_model')
    
    # declare local variables
    discrete_input_registers = ModbusSequentialDataBlock(0, [15]*MAX_DISCRETE_IN_REG_SIZE) # input registers block data store
    coil_output_registers = ModbusSequentialDataBlock(0, [16]*MAX_COIL_REG_SIZE) # coil/output block data store
    holding_registers = ModbusSequentialDataBlock(0, [17]*MAX_HOLD_REG_SIZE) # holding registers block data store
    input_registers = ModbusSequentialDataBlock(0, [18]*MAX_INPUT_REG_SIZE) # input registers block data store
    
    # construct modbus data model using block data stores
    modbus_data_model = ModbusSlaveContext(
        discrete_input_registers,
        coil_output_registers,
        holding_registers,
        input_registers
    )

    return modbus_data_model



def get_server_identity():
    LOGGER.debug('get_server_identity')

    # declare local variables
    modbus_device_id = ModbusDeviceIdentification()

    # initialise device id
    modbus_device_id.MajorMinorRevision = DEV_VERSION
    modbus_device_id.ModelName = DEV_MODEL_NAME
    modbus_device_id.ProductCode = DEV_PROD_CODE
    modbus_device_id.ProductName = DEV_PROD_NAME
    modbus_device_id.UserApplicationName = DEV_USER_APP_NAME
    modbus_device_id.VendorName = DEV_VENDOR_NAME
    modbus_device_id.VendorUrl = DEV_VENDOR_URL

    return modbus_device_id



async def modbus_server_input_register_updates(modbus_server_context, slave_id:int = SLAVE_ID):
    LOGGER.debug('modbus_server_input_register_updates')
    await modbus_server_register_updates(
            modbus_server_context, 
            modbus_function_code=0x04, 
            address=0,
            count=MAX_INPUT_REG_SIZE,
            slave_id=slave_id
        )
    return


async def modbus_server_discrete_input_register_updates(modbus_server_context, slave_id:int = SLAVE_ID):
    LOGGER.debug('modbus_server_discrete_input_register_updates')
    await modbus_server_register_updates(
            modbus_server_context, 
            modbus_function_code=0x02, 
            address=0,
            count=MAX_DISCRETE_IN_REG_SIZE,
            slave_id=slave_id
        )
    return


async def modbus_server_register_updates(modbus_server_context, modbus_function_code:int = 0x02, address:int = 0, count:int = 1, slave_id:int = SLAVE_ID):
    LOGGER.debug('modbus_server_register_updates')

    # check parameters
    assert modbus_server_context
    assert modbus_function_code
    if modbus_function_code < 0x01 or modbus_function_code > 0x06:
        msg = f'modbus_server_register_updates: invalid function code: {function_code}, must be in range 0x01 - 0x06'
        LOGGER.error(msg)
        print(msg)
        return

    # declare local variables
    starting_address = address
    num_registers = count
    values = None
    fifty_fifty = [0,1]

    # set values to zero
    values = modbus_server_context[slave_id].getValues(
            modbus_function_code,
            address=starting_address, 
            count=num_registers
        )
    values = [0 for v in values]
    modbus_server_context[slave_id].setValues(
            modbus_function_code,
            address=starting_address, 
            values=values)
    LOGGER.info(f'modbus_server_register_updates: initialised {num_registers} registers to 0')

    # continuous loop to randomise values in discrete input registers every second
    flip = True # DEBUG
    while True:
        await asyncio.sleep(1)

        # randomise the registers to process each time
        #num_registers = random.randint(1,MAX_DISCRETE_IN_REG_SIZE) # FIXME: blocks here
        values = modbus_server_context[slave_id].getValues(
                modbus_function_code, 
                address=starting_address, 
                count=num_registers
            )

        # randomise bit-flip each time
        for value_idx, value in enumerate(values):
            #flip = random.choice(fifty_fifty) # FIXME: blocks here
            #flip = await random.choice(fifty_fifty) # FIXME: blocks here
            if flip:
                values[value_idx] = not bool(values[value_idx])
                flip = False # DEBUG
            else:
                flip = True # DEBUG

        # set the register values
        modbus_server_context[slave_id].setValues(
                modbus_function_code, 
                address=starting_address, 
                values=values
            )
        #LOGGER.info(f"modbus_server_discrete_input_register_updates: set values: {values!s} at: {starting_address!s} for slave: {slave_id}")


async def run_modbus_server(ipaddr:str = IP_ADDR, port:int = TCP_PORT, slave_id:int = SLAVE_ID):
    LOGGER.debug('run_modbus_server')

    # check parameters
    if not ipaddr or not port or int(port) < 0 or int(port) > 65535:
        LOGGER.error('run_modbus_server: ipaddr or port not specified or invalid')
        return

    # declare local variables
    data_model = get_modbus_data_model()
    server_context = ModbusServerContext(data_model, True) # create a single context for the server/slave
    server_id = get_server_identity()
    server_addr = (ipaddr, port) # socket tuple of ipaddr and port

    # create a task to update discret input registers
    discrete_input_reg_updater_task = asyncio.create_task(modbus_server_discrete_input_register_updates(server_context, slave_id))
    discrete_input_reg_updater_task.set_name("Distrete input register updater task")

    # create a task to update input registers
    input_reg_updater_task = asyncio.create_task(modbus_server_input_register_updates(server_context, slave_id))
    input_reg_updater_task.set_name("Input register updater task")

    # start and run async TCP modbus server
    try:
        LOGGER.debug(f'run_modbus_server {ipaddr}:{port}')
        print(f'attempting to start modbus slave on socket {ipaddr}:{port}...')
        modbus_server = await StartAsyncTcpServer(context=server_context, identity=server_id, address=server_addr) 
        discrete_input_reg_updater_task.cancel() # kill the async thread too
        input_reg_updater_task.cancel() # kill the async thread too
    except PermissionError as pe:
        LOGGER.error('run_modbus_server: no permission to bind socket')
    

async def run_main():
    LOGGER.debug('run_main')
    # parse command line arguments
    parser = argparse.ArgumentParser( 
        prog='proto_server',
        description='Prototype modbus server',
        epilog='This server is intended to be run a prototype modbus server')
    parser.add_argument(
        '-i', '--ipaddr', 
        help='ip address to bind to, default = "127.0.0.1"') 
    parser.add_argument(
        '-p', '--port', 
        help='port to bind to, default = 502')
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

    await run_modbus_server(ipaddr, port)


if __name__ == "__main__":
    LOGGER.debug('proto_server starting')
    asyncio.run(run_main(), debug=False)
    LOGGER.debug('proto_server done')
