#!/bin/bash
set -e

# --- Configuration ---
ROOTFS_NAME="ubuntu-22.04.ext4"
IMAGE_SIZE_MB=2048
TAP_DEV="tap0"
TAP_IP="172.16.0.1"
VM_IP="172.16.0.2"
VM_MAC="AA:FC:00:00:00:01"
KERNEL_URL="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/v1.5/x86_64/vmlinux-5.10.186"
KERNEL_PATH="./vmlinux"
UDS_PATH="/tmp/firecracker.socket"

# --- Function: Build the Ubuntu Image ---
mode_build() {
    echo ">>> [Build] Starting Ubuntu RootFS generation..."

    if ! command -v docker &>/dev/null; then
        echo "Error: Docker is required to build the rootfs."
        exit 1
    fi

    # 1. Create Dockerfile
    cat <<EOF >Dockerfile.fc
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# Install core packages
RUN apt-get update && apt-get install -y \\
    systemd \\
    systemd-sysv \\
    udev \\
    iproute2 \\
    net-tools \\
    curl \\
    openssh-server \\
    nano \\
    passwd \\
    kmod \\
    netplan.io

# Set root password to 'root'
RUN echo 'root:root' | chpasswd

# Enable serial console login
RUN systemctl enable serial-getty@ttyS0.service

# Network Configuration
RUN mkdir -p /etc/netplan
RUN echo "network:\\n\
  version: 2\\n\
  renderer: networkd\\n\
  ethernets:\\n\
    eth0:\\n\
      dhcp4: no\\n\
      addresses: [$VM_IP/24]\\n\
      routes:\\n\
        - to: default\\n\
          via: $TAP_IP\\n\
      nameservers:\\n\
        addresses: [8.8.8.8, 1.1.1.1]" > /etc/netplan/01-netcfg.yaml
# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
EOF

    echo ">>> [Build] Building Docker image..."
    docker build -t fc-ubuntu-builder -f Dockerfile.fc .

    # 2. Create empty disk image
    echo ">>> [Build] Creating empty disk image ($IMAGE_SIZE_MB MB)..."
    dd if=/dev/zero of="$ROOTFS_NAME" bs=1M count="$IMAGE_SIZE_MB" status=progress
    mkfs.ext4 -F "$ROOTFS_NAME"

    # 3. Export filesystem
    echo ">>> [Build] Exporting filesystem..."

    # FIX: We now selectively copy folders to avoid /sys, /proc and recursion errors
    docker run --rm --privileged -v "$(pwd)/$ROOTFS_NAME":/disk.img fc-ubuntu-builder \
        bash -c "
            mkdir -p /mnt/disk && mount -o loop /disk.img /mnt/disk && \
            echo '>>> Copying real files...' && \
            cp -a /bin /boot /etc /home /lib /lib64 /opt /root /sbin /srv /usr /var /mnt/disk/ && \
            echo '>>> Creating virtual directories...' && \
            mkdir -p /mnt/disk/{dev,proc,run,sys,tmp,mnt,media} && \
            chmod 1777 /mnt/disk/tmp && \
            umount /mnt/disk
        "

    echo ">>> [Build] Cleanup..."
    rm Dockerfile.fc
    echo ">>> [Build] Success! $ROOTFS_NAME created."
}
setup_network() {
    echo ">>> [Network] Setting up TAP device $TAP_DEV..."

    # Auto-detect the interface with the default route (internet access)
    HOST_IFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
    if [ -z "$HOST_IFACE" ]; then
        echo "Warning: Could not detect host internet interface. Defaulting to eth0."
        HOST_IFACE="eth0"
    else
        echo ">>> [Network] Detected host internet interface: $HOST_IFACE"
    fi

    # Create TAP if it doesn't exist
    if ! ip link show "$TAP_DEV" >/dev/null 2>&1; then
        ip tuntap add dev "$TAP_DEV" mode tap
    fi

    ip addr add "$TAP_IP/24" dev "$TAP_DEV" 2>/dev/null || true
    ip link set "$TAP_DEV" up

    # Enable Packet Forwarding
    echo 1 >/proc/sys/net/ipv4/ip_forward

    # Flush old rules for a clean slate (optional, be careful if you have complex firewall rules)
    # iptables -F
    # iptables -t nat -F

    # Setup NAT (Masquerading)
    echo ">>> [Network] Enabling NAT on $HOST_IFACE..."
    iptables -t nat -A POSTROUTING -o "$HOST_IFACE" -j MASQUERADE
    iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i "$TAP_DEV" -o "$HOST_IFACE" -j ACCEPT
}

# --- Function: Run Firecracker ---
mode_run() {
    if [ ! -f "$ROOTFS_NAME" ]; then
        echo "Error: $ROOTFS_NAME missing. Run './fc_ubuntu.sh build' first."
        exit 1
    fi

    # Cleanup Old Socket
    echo ">>> [Run] Cleaning up..."
    pkill -f "./firecracker" || true
    rm -f "$UDS_PATH"

    setup_network

    # Ensure kernel exists
    if [ ! -f "$KERNEL_PATH" ]; then
        echo ">>> [Run] Downloading Kernel..."
        curl -fsSL -o "$KERNEL_PATH" "$KERNEL_URL"
    fi

    echo ">>> [Run] Launching Firecracker..."

    # Updated Boot Args:
    # 1. console=ttyS0 -> Sends output to current terminal
    # 2. init=/sbin/init -> Starts Systemd
    # 3. root=/dev/vda -> Points to our drive
    KERNEL_BOOT_ARGS="console=ttyS0 reboot=k panic=1 pci=off root=/dev/vda rw init=/sbin/init"

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
          "guest_mac": "$VM_MAC",
          "host_dev_name": "$TAP_DEV" 
      } 
  ],
  "machine-config": { "vcpu_count": 2, "mem_size_mib": 1024 },
  "vsock": { "guest_cid": 3, "uds_path": "$UDS_PATH" }
}
CONFIG

    # Run Firecracker attached to terminal
    ./firecracker --no-api --config-file vm_config.json
}

# --- Main Entry Point ---
case "$1" in
build)
    mode_build
    ;;
run)
    mode_run
    ;;
*)
    echo "Usage: $0 {build|run}"
    echo "  build : Create the Ubuntu rootfs (requires Docker)"
    echo "  run   : Launch the VM in Firecracker"
    exit 1
    ;;
esac
