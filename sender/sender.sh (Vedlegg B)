#!/usr/bin/env bash

#PATHS
TORRC="/path/to/custom_torrc"
PYTHON_SCRIPT="/path/to/sender_program"
PORT=9061

PID=$(lsof -i :${PORT} -t)

if [[ -n "${PID}" ]]; then
    echo "Port ${PORT} already in use by PID ${PID}"
    echo "Attempting to kill ${PID}"
    kill ${PID}
    if [[ $? -eq 0 ]]; then
        echo "Process ${PID} killed successfully."
    else
        echo "Failed to kill process ${PID}."
    fi
else
    echo "Port ${PORT} not in use."
fi

#Start tor with custom torrc file
sudo service tor stop
echo "Starting Tor with custom torrc"
tor -f $TORRC > /dev/null 2>&1 &

#Small delay to allow the Tor process to initialize
sleep 3

#Execute python script
echo "Starting python sender script"
python3 $PYTHON_SCRIPT
exit
