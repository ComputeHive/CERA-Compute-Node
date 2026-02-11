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
GUEST_CID=3
VCPU_COUNT=$1
RAM_MEM_MB=$2

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

run_vm() {
    if [ ! -f "$ROOTFS_NAME" ]; then
        exit 1
    fi

    pkill -f "./firecracker" || true
    rm -f "$UDS_PATH" vm_config.json

    setup_network

    if [ ! -f "$KERNEL_PATH" ]; then
        curl -fsSL -o "$KERNEL_PATH" "$KERNEL_URL"
    fi

    KERNEL_BOOT_ARGS="console=ttyS0 reboot=k panic=1 pci=off root=/dev/vda rw init=/sbin/init"

    sed \
        -e "s|{{KERNEL_PATH}}|$KERNEL_PATH|g" \
        -e "s|{{KERNEL_BOOT_ARGS}}|$KERNEL_BOOT_ARGS|g" \
        -e "s|{{ROOTFS_NAME}}|$ROOTFS_NAME|g" \
        -e "s|{{VM_MAC}}|$VM_MAC|g" \
        -e "s|{{TAP_DEV}}|$TAP_DEV|g" \
        -e "s|{{VCPU_COUNT}}|$VCPU_COUNT|g" \
        -e "s|{{RAM_MEM_MB}}|$RAM_MEM_MB|g" \
        -e "s|{{GUEST_CID}}|$GUEST_CID|g" \
        -e "s|{{UDS_PATH}}|$UDS_PATH|g" \
        templates/vm_config.json.template >vm_config.json

    ./firecracker --no-api --config-file vm_config.json
}

run_vm
