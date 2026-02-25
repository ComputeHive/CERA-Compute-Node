#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/config"
source "$CONFIG_DIR/config.sh"

mkdir -p "$CERA_IMG_DIR"

shrink_image() {
    sudo e2fsck -fp "$ROOTFS_NAME" || {
        rc=$?
        if [ "$rc" -ne 0 ] && [ "$rc" -ne 1 ]; then
            return 1
        fi
    }

    local min_blocks=256
    local buffer_blocks=$((BUFFER_MB * 1024 * 1024 / 4096))
    local target_blocks=$((min_blocks + buffer_blocks))

    sudo resize2fs "$ROOTFS_NAME" "$target_blocks"

    local final_bytes=$((target_blocks * 4096))
    sudo truncate -s "$final_bytes" "$ROOTFS_NAME"
}

generate_netplan() {
    sed "s/{{VM_IP}}/$VM_IP/; s/{{TAP_IP}}/$TAP_IP/" \
        $SCRIPT_DIR/templates/01-netcfg.yaml.template >01-netcfg.yaml
}

configure_rootfs_chroot() {
    local rootfs=$1
    sudo chroot "$rootfs" /bin/sh -c "echo 'root:root' | chpasswd"
    sudo chroot "$rootfs" systemctl enable serial-getty@ttyS0.service
    sudo chroot "$rootfs" systemctl enable systemd-networkd
}

build_image_debootstrap() {
    if ! command -v debootstrap &>/dev/null; then
        sudo apt-get update && sudo apt-get install -y debootstrap
    fi

    truncate -s "${DISK_CAPACITY_MB}M" "$ROOTFS_NAME"
    sudo mkfs.ext4 -F "$ROOTFS_NAME" >/dev/null

    sudo mkdir -p "$MOUNT_POINT"
    sudo mount -o loop "$ROOTFS_NAME" "$MOUNT_POINT"

    sudo debootstrap --variant=minbase --arch amd64 \
        --include=systemd,udev,iproute2,isc-dhcp-client,kmod,openssh-server,nano \
        jammy "$MOUNT_POINT" http://archive.ubuntu.com/ubuntu/

    echo "fc-vm" | sudo tee "$MOUNT_POINT/etc/hostname" >/dev/null

    generate_netplan
    sudo mkdir -p "$MOUNT_POINT/etc/netplan"
    sudo cp 01-netcfg.yaml "$MOUNT_POINT/etc/netplan/01-netcfg.yaml"

    configure_rootfs_chroot "$MOUNT_POINT"

    sudo umount "$MOUNT_POINT"
    sudo rmdir "$MOUNT_POINT"

    sudo chown "$(id -u):$(id -g)" "$ROOTFS_NAME" "$CERA_IMG_DIR"

    rm -f 01-netcfg.yaml
    shrink_image
}

build_image_docker() {
    if ! command -v docker &>/dev/null; then
        echo "Error: Docker is required to build the rootfs."
        exit 1
    fi

    generate_netplan

    sudo docker build -t fc-ubuntu-builder -f Dockerfile.fc .

    sudo dd if=/dev/zero of="$ROOTFS_NAME" bs=1M count="$IMAGE_SIZE_MB" status=progress
    sudo mkfs.ext4 -F "$ROOTFS_NAME"

    sudo docker run --rm --privileged \
        -v "$ROOTFS_NAME":/disk.img \
        -v "$(pwd)/export_rootfs.sh":/export_rootfs.sh \
        fc-ubuntu-builder bash /export_rootfs.sh /disk.img

    sudo chown "$(id -u):$(id -g)" "$ROOTFS_NAME"

    rm -f 01-netcfg.yaml
    shrink_image
}

case "${1:-normal}" in
docker)
    build_image_docker
    ;;
normal)
    build_image_debootstrap
    ;;
*)
    echo "Usage: $0 <docker|normal>" >&2
    exit 1
    ;;
esac
