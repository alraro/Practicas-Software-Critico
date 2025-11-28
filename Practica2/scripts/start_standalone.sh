#!/bin/bash

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd ${parent_path}

sudo docker swarm init
sudo docker stack deploy -c ../docker-compose-standard.yml practica2_standalone