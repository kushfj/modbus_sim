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
REG_SIZE = 200 # register size for coils, etc to use using init.

DEV_VERSION = '0.0'
DEV_MODEL_NAME = 'PyVirtPLC'
DEV_PROD_CODE = 'vPLC'
DEV_PROD_NAME = 'Virtual PLC Server'
DEV_USER_APP_NAME = 'PLC Simulator'
DEV_VENDOR_NAME = "Python"
DEV_VENDOR_URL = 'https://github.com/kushfj/modbus_sim'

IP_ADDR = '127.0.0.1'
TCP_PORT = 502

LOG_FILE = 'proto_server.log'


# declare global variables - this is a bad things, but...
logging.basicConfig(filename=LOG_FILE, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
LOGGER = logging.getLogger(__name__)
#LOGGER.setLevel(logging.INFO)


def get_modbus_data_model():
    LOGGER.debug('get_modbus_data_model')
    
    # declare local variables
    discrete_input_registers = ModbusSequentialDataBlock(0, [15]*REG_SIZE) # input registers block data store
    coil_output_registers = ModbusSequentialDataBlock(0, [16]*REG_SIZE) # coil/output block data store
    holding_registers = ModbusSequentialDataBlock(0, [17]*REG_SIZE) # holding registers block data store
    input_registers = ModbusSequentialDataBlock(0, [18]*REG_SIZE) # input registers block data store
    
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


async def run_modbus_server(ipaddr:str = IP_ADDR, port:int = TCP_PORT):
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

    # start and run async TCP modbus server
    try:
        LOGGER.debug(f'run_modbus_server {ipaddr}:{port}')
        modbus_server = await StartAsyncTcpServer(context=server_context, identity=server_id, address=server_addr) 
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
    asyncio.run(run_main(), debug=True)
    LOGGER.debug('proto_server stopped')
