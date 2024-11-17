#!/bin/bash

source ./python_env/bin/activate

python ./test_harness.py -s server -n 10 -l ids_slaves_list.txt > run_ids_servers.sh
python ./test_harness.py -s client -n 3 -l ids_slaves_list.txt > run_ids_clients.sh

deactivate
