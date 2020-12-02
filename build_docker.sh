#!/bin/bash -eu
set -o pipefail

docker build -t zedzed9/kismet_exporter:latest .
