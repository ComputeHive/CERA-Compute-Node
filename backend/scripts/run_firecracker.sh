#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/config"
source "$CONFIG_DIR/config.sh"

VCPU_COUNT=$1
RAM_MEM_MB=$2
DISK_MEM_MB=$3

create_data_disk() {
    local size_mb=$1
    sudo mkdir -p "$CERA_DISKS_DIR"
    DATA_DISK_PATH="${CERA_DISKS_DIR}/data_$(date +%s).raw"
    sudo truncate -s "${size_mb}M" "$DATA_DISK_PATH"
    sudo mkfs.ext4 -F -q "$DATA_DISK_PATH" >/dev/null
    sudo chown root:root "$DATA_DISK_PATH"
    sudo chmod 0600 "$DATA_DISK_PATH"
}

cleanup() {
    if [ -n "${DATA_DISK_PATH:-}" ]; then
        sudo rm -f "$DATA_DISK_PATH" 2>/dev/null || true
    fi
    if ip link show "$TAP_DEV" >/dev/null 2>&1; then
        sudo ip link del "$TAP_DEV" 2>/dev/null || true
    fi
    if [ -n "${HOST_IFACE:-}" ]; then
        sudo iptables -t nat -D POSTROUTING -o "$HOST_IFACE" -j MASQUERADE 2>/dev/null || true
        sudo iptables -D FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
        sudo iptables -D FORWARD -i "$TAP_DEV" -o "$HOST_IFACE" -j ACCEPT 2>/dev/null || true
    fi
    sudo rm -f "$UDS_PATH" 2>/dev/null || true
}
trap cleanup EXIT

setup_network() {
    HOST_IFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
    if [ -z "$HOST_IFACE" ]; then
        echo "Warning: Could not detect host interface. Defaulting to eth0."
        HOST_IFACE="eth0"
    fi

    if ! ip link show "$TAP_DEV" >/dev/null 2>&1; then
        sudo ip tuntap add dev "$TAP_DEV" mode tap
    fi

    sudo ip addr add "$TAP_IP/24" dev "$TAP_DEV" 2>/dev/null || true
    sudo ip link set "$TAP_DEV" up

    sudo sysctl -w net.ipv4.ip_forward=1 >/dev/null

    sudo iptables -t nat -C POSTROUTING -o "$HOST_IFACE" -j MASQUERADE 2>/dev/null ||
        sudo iptables -t nat -A POSTROUTING -o "$HOST_IFACE" -j MASQUERADE
    sudo iptables -C FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null ||
        sudo iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    sudo iptables -C FORWARD -i "$TAP_DEV" -o "$HOST_IFACE" -j ACCEPT 2>/dev/null ||
        sudo iptables -A FORWARD -i "$TAP_DEV" -o "$HOST_IFACE" -j ACCEPT
}

run_vm() {
    if [ ! -f "$ROOTFS_NAME" ]; then
        echo "Error: rootfs image not found at $ROOTFS_NAME"
        exit 1
    fi

    sudo pkill -f "firecracker" 2>/dev/null || true
    sudo rm -f "$UDS_PATH"

    sudo mkdir -p "$CERA_RUN_DIR"
    sudo chown "$(id -u):$(id -g)" "$CERA_RUN_DIR"

    setup_network

    create_data_disk "$DISK_MEM_MB"

    if [ ! -f "$KERNEL_PATH" ]; then
        sudo mkdir -p "$(dirname "$KERNEL_PATH")"
        curl -fsSL -o "$KERNEL_PATH" "$KERNEL_URL"
    fi

    VM_CONFIG="${CERA_RUN_DIR}/vm_config.json"
    KERNEL_BOOT_ARGS="console=ttyS0 reboot=k panic=1 pci=off root=/dev/vda rw init=/sbin/init"

    sed \
        -e "s|{{KERNEL_PATH}}|$KERNEL_PATH|g" \
        -e "s|{{KERNEL_BOOT_ARGS}}|$KERNEL_BOOT_ARGS|g" \
        -e "s|{{ROOTFS_NAME}}|$ROOTFS_NAME|g" \
        -e "s|{{DATA_DISK_PATH}}|$DATA_DISK_PATH|g" \
        -e "s|{{VM_MAC}}|$VM_MAC|g" \
        -e "s|{{TAP_DEV}}|$TAP_DEV|g" \
        -e "s|{{VCPU_COUNT}}|$VCPU_COUNT|g" \
        -e "s|{{RAM_MEM_MB}}|$RAM_MEM_MB|g" \
        -e "s|{{GUEST_CID}}|$GUEST_CID|g" \
        -e "s|{{UDS_PATH}}|$UDS_PATH|g" \
        templates/vm_config.json.template >"$VM_CONFIG"

    sudo firecracker --no-api --config-file "$VM_CONFIG"
}

run_vm
