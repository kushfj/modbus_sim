# Modbus Simulator

## Purpose

We need a tool to be able to generate Modbus traffic at scale with limited resources. The tool must be capable of generating actual network traffic dynamically instead of just replaying existing traffic.

Possible uses of the tools shall include:

  * To confirm functionality of OT IDS systems e.g., Claroty, Nozomi, Dragos, etc.
  * To validate IDS rules e.g., Snort

The problem appears to already have been solved to some extent at https://apmonitor.com/dde/index.php/Main/ModbusTransfer, so we just need to modify it for our purposes

## References

### Previous Work

  * https://apmonitor.com/dde/index.php/Main/ModbusTransfer

### Documentation

  * https://modbus.org

### Libraries

  * https://pypi.org/project/pymodbus/
  * https://pypi.org/project/pyModbusTCP/

**Not Actively Maintianed**
  * https://github.com/AdvancedClimateSystems/uModbus 
  * https://github.com/ipal0/modbus
  * https://github.com/ljean/modbus-tk

## Development Requirements

### Functional Requirements - What it does

* Need a customisable simulation systems to be able to simulate a large number of hosts communicating over Modbus e.g. up to an including 247 modbus servers/slaves
* Need communication end-points to be customisable or variable so as not to have the same network traffic
* Need communication payloads should be customisable or variable so as not to have the same network traffic
* Need to modify ethernet hardware MAC address to masquerade as common vendors e.g., Rockwell Automation, Schneider Electric, Mitsubishi, GE, Yokogawa, etc.
* Need to log messages to log file for audit and troubleshooting purposes

### Non-functional Requirements - How it does it

* Need software to be open source and developed using Python
* Need software to be deployable on Linux virtual machines

## Design

### High-level Design

* Use Linux network sub-interfaces to build source and destination aka. Modbus client and servers addresses
* Modify sub-interface MAC address to macquerade/spoof PLC hardware vendor OUI
* Pass IP address to bind to as a command line interface


## Development Environment

### Set-up

* python -m venv python_venv
* . ./python_venv/bin/activate
* pip install pymodbus
* pip install notebook # using jupyter notebook for rapid prototyping only

## Future Work

* Include IPv6
* User configurable payloads e.g. from a configuration file
* User customisable IP addresses
