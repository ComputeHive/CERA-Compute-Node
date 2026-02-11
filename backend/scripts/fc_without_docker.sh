#!/bin/bash
set -e

# --- Configuration ---
ROOTFS_NAME="ubuntu-min.ext4"
DISK_CAPACITY_MB=2048 # Maximum capacity (won't use this space immediately)
TAP_DEV="tap0"
TAP_IP="172.16.0.1"
VM_IP="172.16.0.2"
KERNEL_URL="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/v1.5/x86_64/vmlinux-5.10.186"
KERNEL_PATH="./vmlinux"
MOUNT_POINT="/mnt/fc_rootfs"

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Run as root (sudo)."
    exit 1
fi

mode_build() {
    echo ">>> [Build] Starting Minimal RootFS generation..."

    # 1. Install Dependencies (only if missing)
    if ! command -v debootstrap &>/dev/null; then
        echo ">>> [Build] Installing debootstrap..."
        apt-get update && apt-get install -y debootstrap
    fi

    # 2. Create SPARSE disk image
    # 'truncate' creates a file that reports 2GB size but takes 0 bytes on disk initially.
    echo ">>> [Build] Creating sparse disk image..."
    truncate -s "${DISK_CAPACITY_MB}M" "$ROOTFS_NAME"
    mkfs.ext4 -F "$ROOTFS_NAME" >/dev/null

    # 3. Mount
    mkdir -p "$MOUNT_POINT"
    mount -o loop "$ROOTFS_NAME" "$MOUNT_POINT"

    # 4. Bootstrap Minimal Ubuntu
    # --variant=minbase: Downloads ONLY essential packages (~150MB total)
    # --include: We explicitly add systemd and networking tools because minbase excludes them.
    echo ">>> [Build] Downloading minimal OS (this is small, ~180MB)..."
    debootstrap --variant=minbase --arch amd64 \
        --include=systemd,udev,iproute2,isc-dhcp-client,kmod,openssh-server,nano \
        jammy "$MOUNT_POINT" http://archive.ubuntu.com/ubuntu/

    # 5. Configure Inside Chroot
    echo ">>> [Build] Configuring..."

    # Set Hostname
    echo "fc-vm" >"$MOUNT_POINT/etc/hostname"

    # Set Root Password (root:root)
    # We use chroot to run commands 'inside' the image
    chroot "$MOUNT_POINT" /bin/sh -c "echo 'root:root' | chpasswd"

    # Enable Serial Console (Critical for Firecracker)
    chroot "$MOUNT_POINT" systemctl enable serial-getty@ttyS0.service

    # Configure Networking (Systemd-networkd is lighter than netplan)
    cat <<EOF >"$MOUNT_POINT/etc/systemd/network/eth0.network"
[Match]
Name=eth0

[Network]
Address=$VM_IP/24
Gateway=$TAP_IP
DNS=8.8.8.8
EOF
    # Enable networkd
    chroot "$MOUNT_POINT" systemctl enable systemd-networkd

    # 6. Unmount
    umount "$MOUNT_POINT"
    rmdir "$MOUNT_POINT"

    # Fix permissions for the user
    if [ -n "$SUDO_USER" ]; then
        chown "$SUDO_USER":"$SUDO_USER" "$ROOTFS_NAME"
    fi

    echo ">>> [Build] Done! Image created: $ROOTFS_NAME"
    echo ">>> Note: Actual disk usage is only ~200MB."
}

mode_run() {
    # Check for Kernel
    if [ ! -f "$KERNEL_PATH" ]; then
        echo ">>> [Run] Downloading Kernel..."
        curl -fsSL -o "$KERNEL_PATH" "$KERNEL_URL"
    fi

    # Network Setup
    ip link show "$TAP_DEV" >/dev/null 2>&1 || ip tuntap add dev "$TAP_DEV" mode tap
    ip addr add "$TAP_IP/24" dev "$TAP_DEV" 2>/dev/null || true
    ip link set "$TAP_DEV" up
    sysctl -w net.ipv4.ip_forward=1 >/dev/null
    iptables -t nat -A POSTROUTING -o $(ip route show default | awk '/default/ {print $5}') -j MASQUERADE

    # Firecracker Config
    KERNEL_BOOT_ARGS="console=ttyS0 reboot=k panic=1 pci=off root=/dev/vda rw init=/lib/systemd/systemd"

    cat <<CONFIG >vm_config.json
{
  "boot-source": {
    "kernel_image_path": "$KERNEL_PATH",
    "boot_args": "$KERNEL_BOOT_ARGS"
  },
  "drives": [
    {
      "drive_id": "rootfs",
      "path_on_host": "$ROOTFS_NAME",
      "is_root_device": true,
      "is_read_only": false
    }
  ],
  "network-interfaces": [
      {
          "iface_id": "eth0",
          "host_dev_name": "$TAP_DEV",
          "guest_mac": "AA:FC:00:00:00:01"
      }
  ],
  "machine-config": { "vcpu_count": 1, "mem_size_mib": 512 }
}
CONFIG

    echo ">>> [Run] Launching..."
    ./firecracker --no-api --config-file vm_config.json

    # Cleanup after exit
    rm -f vm_config.json
}

case "$1" in
build) mode_build ;;
run) mode_run ;;
*) echo "Usage: sudo $0 {build|run}" ;;
esac
