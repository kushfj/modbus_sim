# Modbus Simulator


## Purpose

We need a tool to be able to generate Modbus traffic at scale with limited resources. The tool must be capable of generating actual network traffic dynamically instead of just replaying existing traffic.

Possible uses of the tools shall include:

  * To confirm functionality of OT IDS systems e.g., Claroty, Nozomi, Dragos, etc.
  * To validate IDS rules e.g., Snort

The problem appears to already have been solved to some extent at https://github.com/cmu-sei/SCADASim etc. However, one limitation with those solutions is that there seems to be limited options for scaling the master and slave, thus additional work will be required to customise them.

The alternative is to develop our own "light-weight" master and slave with some fixed function, but focus on a setup which allows us to simulate at scale. An introduces a whole bunch of randomness to the simulated "process" to attempt to ensure that the network traffic is dynamic.

Part of the scaling is dependent on the underlying operating system. The intention is to use Linux and network sub-interfaces with spoofed hardware MAC addresses to masquerade as PLC vendor.


## References

### Previous Work

  * https://github.com/cmu-sei/SCADASim
  * https://apmonitor.com/dde/index.php/Main/ModbusTransfer
  * https://github.com/Salto7/Modbus-Traffic-Generator

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

* FR1 - Need a customisable simulation systems to be able to simulate a large number of hosts communicating over Modbus e.g. up to an including 247 modbus servers/slaves
* FR2 - Need communication end-points to be customisable or variable so as not to have the same network traffic
* FR3 - Need communication payloads should be customisable or variable so as not to have the same network traffic
* FR4 - Need to modify ethernet hardware MAC address to masquerade as common vendors e.g., Rockwell Automation, Schneider Electric, Mitsubishi, GE, Yokogawa, etc.
* FR5 - Need to log messages to log file for audit and troubleshooting purposes
* FR6 - Need the client/master to randomly write to coils and holding registers
* FR7 - Need the server/slave to randomly set values for discrete input and input registers
* FR8 - Need a set of scripts to dynamically spin up virtual machines, set-up network interfaces, etc start the slaves, run masters to generate traffic, etc.

### Non-functional Requirements - How it does it

* NFR1 - Need software to be open source and developed using Python
* NFR2 - Need software to be deployable on Linux virtual machines


## Design

### High-level Design

* Use Linux network sub-interfaces to build source and destination aka. Modbus client and servers addresses
* Modify sub-interface MAC address to macquerade/spoof PLC hardware vendor OUI
* Pass IP address to bind to as a command line interface
* Have fixed 


## Development Environment

### Set-up

* python -m venv python_venv
* . ./python_venv/bin/activate
* pip install pymodbus


## Future Work

* User configurable payloads e.g. from a configuration file
* User customisable IP addresses
* Integrate with hardware process
