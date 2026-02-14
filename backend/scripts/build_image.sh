#!/bin/bash
set -euo pipefail
CONFIG_DIR="config"
source $CONFIG_DIR/config.sh

mkdir -p "$CERA_IMG_DIR" "$MOUNT_POINT"

shrink_image() {
    if ! e2fsck -fp "$ROOTFS_NAME"; then
        rc=$?
        if [ "$rc" -ne 0 ] && [ "$rc" -ne 1 ]; then
            return 1
        fi
    fi
    min_blocks=256

    buffer_blocks=$((BUFFER_MB * 1024 * 1024 / 4096))
    target_blocks=$((min_blocks + buffer_blocks))
    resize2fs "$ROOTFS_NAME" "$target_blocks"
    final_bytes=$((target_blocks * 4096))
    truncate -s "$final_bytes" "$ROOTFS_NAME"

}
generate_netplan() {
    sed "s/{{VM_IP}}/$VM_IP/; s/{{TAP_IP}}/$TAP_IP/" 01-netcfg.yaml.template >01-netcfg.yaml
}

configure_rootfs_chroot() {
    local rootfs=$1
    chroot "$rootfs" /bin/sh -c "echo 'root:root' | chpasswd"
    chroot "$rootfs" systemctl enable serial-getty@ttyS0.service
    chroot "$rootfs" systemctl enable systemd-networkd
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

    generate_netplan
    mkdir -p "$MOUNT_POINT/etc/netplan"
    cp 01-netcfg.yaml "$MOUNT_POINT/etc/netplan/01-netcfg.yaml"

    configure_rootfs_chroot "$MOUNT_POINT"

    umount "$MOUNT_POINT"
    rmdir "$MOUNT_POINT"

    if [ -n "${SUDO_USER:-}" ]; then
        chown "$SUDO_USER":"$SUDO_USER" "$ROOTFS_NAME"
        chown "$SUDO_USER":"$SUDO_USER" "$CERA_IMG_DIR"
    fi
    rm -f 01-netcfg.yaml
    shrink_image
}

build_image_docker() {
    if ! command -v docker &>/dev/null; then
        echo "Error: Docker is required to build the rootfs."
        exit 1
    fi

    generate_netplan

    docker build -t fc-ubuntu-builder -f Dockerfile.fc .

    dd if=/dev/zero of="$ROOTFS_NAME" bs=1M count="$IMAGE_SIZE_MB" status=progress
    mkfs.ext4 -F "$ROOTFS_NAME"

    docker run --rm --privileged \
        -v "$ROOTFS_NAME":/disk.img \
        -v "$(pwd)/export_rootfs.sh":/export_rootfs.sh \
        fc-ubuntu-builder bash /export_rootfs.sh /disk.img

    rm -f 01-netcfg.yaml
    shrink_image
}

case "$1" in
docker)
    build_image_docker
    ;;
normal)
    build_image_debootstrap
    ;;
esac
setup_network
