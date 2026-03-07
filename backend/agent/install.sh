set -euo pipefail

ROOTFS="${1:?Usage: install.sh <rootfs_mount_point>}"
AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="${ROOTFS}/opt/cera-agent"

echo "Installing CERA agent into ${DEST} ..."

sudo mkdir -p "${DEST}/cera_agent"

sudo cp "${AGENT_DIR}/requirements.txt" "${DEST}/"
sudo chroot "${ROOTFS}" pip3 install -q -r "/opt/cera-agent/requirements.txt"

# Copy Python source
sudo cp "${AGENT_DIR}/cera_agent/__init__.py" "${DEST}/cera_agent/"
sudo cp "${AGENT_DIR}/cera_agent/main.py" "${DEST}/cera_agent/"
sudo cp "${AGENT_DIR}/cera_agent/metrics.py" "${DEST}/cera_agent/"
sudo cp "${AGENT_DIR}/cera_agent/protocol.py" "${DEST}/cera_agent/"
sudo cp "${AGENT_DIR}/cera_agent/task_runner.py" "${DEST}/cera_agent/"

# Copy systemd service
sudo cp "${AGENT_DIR}/cera-agent.service" "${ROOTFS}/etc/systemd/system/"

# Enable the service inside the chroot
sudo chroot "${ROOTFS}" systemctl enable cera-agent.service

echo "CERA agent installed and enabled."
