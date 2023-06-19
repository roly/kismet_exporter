#!/bin/bash -eu
set -o pipefail

#docker build -t zedzed9/kismet_exporter:latest .
docker-compose up --force-recreate --build -d
docker image prune -f
