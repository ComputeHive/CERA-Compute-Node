#!/bin/bash
set -euo pipefail

ROOTFS_NAME="ubuntu-22.04.ext4"
IMAGE_SIZE_MB=2048
TAP_DEV="tap0"
TAP_IP="172.16.0.1"
VM_IP="172.16.0.2"
VM_MAC="AA:FC:00:00:00:01"
KERNEL_URL="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/v1.5/x86_64/vmlinux-5.10.186"
KERNEL_PATH="./vmlinux"
UDS_PATH="/tmp/firecracker.socket"

build_image_docker() {

    if ! command -v docker &>/dev/null; then
        echo "Error: Docker is required to build the rootfs."
        exit 1
    fi

    sed "/s{{VM_IP}}/$VM_IP/; s/{{TAP_IP}}/$TAP_IP/" 01-netcfg.yaml.template >01-netcfg.yaml

    docker build -t fc-ubuntu-builder -f Dockerfile.fc .

    dd if=/dev/zero of="$ROOTFS_NAME" bs=1M count="$IMAGE_SIZE_MB" status=progress
    mkfs.ext4 -F "$ROOTFS_NAME"

    docker run --rm --privileged \
        -v "$(pwd)/$ROOTFS_NAME":/disk.img \
        -v "$(pwd)/export_rootfs.sh":/export_rootfs.sh \
        fc-ubuntu-builder bash /export_rootfs.sh /disk.img
    rm -f 01-netcfg.yaml
}

setup_network() {

    HOST_IFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
    if [ -z "$HOST_IFACE" ]; then
        echo "Warning: Could not detect host internet interface. Defaulting to eth0."
        HOST_IFACE="eth0"
    fi
    if ! ip link show "$TAP_DEV" >/dev/null 2>&1; then
        ip tuntap add dev "$TAP_DEV" mode tap
    fi
    ip addr add "$TAP_IP/24" dev "$TAP_DEV" 2>/dev/null || true
    ip link set "$TAP_DEV" up
    echo 1 >/proc/sys/net/ipv4/ip_forward
    iptables -t nat -A POSTROUTING -o "$HOST_IFACE" -j MASQUERADE
    iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i "$TAP_DEV" -o "$HOST_IFACE" -j ACCEPT
}

build_image_debootstrap() {
    if ! command -v debootstrap &>/dev/null; then
        apt-get update && apt-get install -y debootstrap
    fi

    truncate -s "${DISK_CAPACITY_MB}M" "$ROOTFS_NAME"
    mkfs.ext4 -F "$ROOTFS_NAME" >/dev/null

    mkdir -p "$MOUNT_POINT"
    mount -o loop "$ROOTFS_NAME" "$MOUNT_POINT"
    debootstrap --variant=minbase --arch amd64 \
        --include=systemd,udev,iproute2,isc-dhcp-client,kmod,openssh-server,nano \
        jammy "$MOUNT_POINT" http://archive.ubuntu.com/ubuntu/

    echo "fc-vm" >"$MOUNT_POINT/etc/hostname"

    chroot "$MOUNT_POINT" /bin/sh -c "echo 'root:root' | chpasswd"
    chroot "$MOUNT_POINT" systemctl enable serial-getty@ttyS0.service

    cat <<EOF >"$MOUNT_POINT/etc/systemd/network/eth0.network"
[Match]
Name=eth0

[Network]
Address=$VM_IP/24
Gateway=$TAP_IP
DNS=8.8.8.8
EOF
    chroot "$MOUNT_POINT" systemctl enable systemd-networkd

    umount "$MOUNT_POINT"
    rmdir "$MOUNT_POINT"
    if [ -n "$SUDO_USER" ]; then
        chown "$SUDO_USER":"$SUDO_USER" "$ROOTFS_NAME"
    fi
}
