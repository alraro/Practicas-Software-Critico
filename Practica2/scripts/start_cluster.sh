#!/bin/bash

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd ${parent_path}
sudo docker compose -f ../docker-compose-redis-cluster.yml up -d