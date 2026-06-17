#!/bin/bash
set -euo pipefail

ROOTFS="${1:?Usage: install.sh <rootfs_mount_point>}"
AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="${ROOTFS}/opt/cera-agent"

echo "Installing CERA agent into ${DEST} ..."

sudo mkdir -p "${DEST}"

# Install dependencies
sudo cp "${AGENT_DIR}/requirements.txt" "${DEST}/requirements.txt"
sudo chroot "${ROOTFS}" pip3 install -q -r "/opt/cera-agent/requirements.txt"

# Copy the entire package recursively (mirrors Dockerfile COPY agent/cera_agent/)
sudo cp -r "${AGENT_DIR}/cera_agent" "${DEST}/cera_agent"

# Copy systemd service
sudo cp "${AGENT_DIR}/cera-agent.service" "${ROOTFS}/etc/systemd/system/"

# Enable the service inside the chroot
sudo chroot "${ROOTFS}" systemctl enable cera-agent.service

echo "CERA agent installed and enabled."
