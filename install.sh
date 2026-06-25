#!/bin/bash
set -e

for cmd in node npm python3 poetry docker; do
  command -v $cmd &>/dev/null || { echo "Error: $cmd is not installed"; exit 1; }
done

cd app/CERA-VM-Manager && npm install
cd ../../backend && poetry install
