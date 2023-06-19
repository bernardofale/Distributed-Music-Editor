#!/bin/bash

# File to store the PIDs
pid_file="worker_pids.txt"

# Start RabbitMQ container
xterm -T "RabbitMQ and Mongo DB Containers" -hold -e "docker-compose up" &
pid=$!
echo "$pid" >> "$pid_file"

# Wait for RabbitMQ container to start
sleep 25

#Activate the virtual environment
#source /path/to/venv/bin/activate

# Run the Python script with different -i arguments
for ((i=0; i<=3; i++))
do
    xterm -T "Worker $i" -hold -e "source ./venv/bin/activate && python3 new_worker.py -i $i" &
    pid=$!
    echo "$pid" >> "$pid_file"
done


# Deactivate the virtual environment
#deactivate


