#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/config"
AGENT_DIR="${SCRIPT_DIR}/../agent"
source "$CONFIG_DIR/config.sh"

sudo mkdir -p "$(dirname "$CERA_IMG_DIR")"
sudo chown "$(id -u):$(id -g)" "$(dirname "$CERA_IMG_DIR")"
sudo mkdir -p "$CERA_IMG_DIR"

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

cleanup_mount() {
    local mount_point=$1
    local loop_dev=${2:-}

    if mountpoint -q "$mount_point"; then
        sudo umount "$mount_point" 2>/dev/null || true
    fi
    if [ -n "$loop_dev" ]; then
        sudo losetup -d "$loop_dev" 2>/dev/null || true
    fi
}

create_rootfs_image() {
    sudo mkdir -p "$CERA_IMG_DIR"
    sudo rm -f "$ROOTFS_NAME"
    sudo truncate -s "${DISK_CAPACITY_MB}M" "$ROOTFS_NAME"
    sudo mkfs.ext4 -F -E lazy_itable_init=0,lazy_journal_init=0 "$ROOTFS_NAME" >/dev/null
    sudo e2fsck -fy "$ROOTFS_NAME" >/dev/null
}

configure_rootfs_chroot() {
    local rootfs=$1
    sudo chroot "$rootfs" /bin/sh -c "echo 'root:root' | chpasswd"
    sudo chroot "$rootfs" systemctl enable serial-getty@ttyS0.service
    sudo chroot "$rootfs" systemctl enable systemd-networkd
    # Enable docker service
    sudo chroot "$rootfs" systemctl enable docker

    # Set hostname
    echo "fc-vm" | sudo tee "$rootfs/etc/hostname" >/dev/null
    # Override poweroff to reboot (Firecracker has no ACPI, reboot=k makes reboot exit the VM)
    sudo mkdir -p "$rootfs/etc/systemd/system/systemd-poweroff.service.d"
    cat <<'EOF' | sudo tee "$rootfs/etc/systemd/system/systemd-poweroff.service.d/override.conf" >/dev/null
[Service]
ExecStart=
ExecStart=/bin/systemctl --force reboot
EOF
}

build_image_debootstrap() {
    if ! command -v debootstrap &>/dev/null; then
        sudo apt-get update && sudo apt-get install -y debootstrap
    fi

    create_rootfs_image

    sudo mkdir -p "$MOUNT_POINT"
    sudo mount -o loop "$ROOTFS_NAME" "$MOUNT_POINT"

    sudo debootstrap --variant=minbase --arch amd64 \
        --include=systemd,systemd-sysv,udev,iproute2,net-tools,curl,kmod,openssh-server,nano,passwd,netplan.io,python3,python3-pip,dbus,docker.io \
        jammy "$MOUNT_POINT" http://archive.ubuntu.com/ubuntu/

    generate_netplan
    sudo mkdir -p "$MOUNT_POINT/etc/netplan"
    sudo cp 01-netcfg.yaml "$MOUNT_POINT/etc/netplan/01-netcfg.yaml"

    configure_rootfs_chroot "$MOUNT_POINT"

    # Install the CERA guest agent
    bash "$AGENT_DIR/install.sh" "$MOUNT_POINT"


    sudo umount "$MOUNT_POINT"
    sudo rmdir "$MOUNT_POINT" 2>/dev/null || true

    sudo chown "$(id -u):$(id -g)" "$ROOTFS_NAME" "$CERA_IMG_DIR"

    rm -f 01-netcfg.yaml
    # shrink_image
}

build_image_docker() {
    if ! command -v docker &>/dev/null; then
        echo "Error: Docker is required to build the rootfs."
        exit 1
    fi

    local LOOP_DEV=""
    local TAR_FILE="/tmp/fc-rootfs-$$.tar"
    trap 'cleanup_mount "$MOUNT_POINT" "$LOOP_DEV"; sudo rm -f "$TAR_FILE"; rm -f 01-netcfg.yaml' RETURN

    generate_netplan

    sudo docker build -t fc-ubuntu-builder -f "$SCRIPT_DIR/Dockerfile.fc" "$SCRIPT_DIR/.."

    local CONTAINER_ID
    CONTAINER_ID=$(sudo docker create fc-ubuntu-builder)

    sudo docker export "$CONTAINER_ID" -o "$TAR_FILE"
    sudo docker rm "$CONTAINER_ID" >/dev/null

    create_rootfs_image

    sudo mkdir -p "$MOUNT_POINT"
    cleanup_mount "$MOUNT_POINT"
    LOOP_DEV=$(sudo losetup --find --show "$ROOTFS_NAME")
    sudo mount "$LOOP_DEV" "$MOUNT_POINT"

    sudo tar xf "$TAR_FILE" -C "$MOUNT_POINT"
    sudo rm -f "$TAR_FILE"

    sudo mkdir -p "$MOUNT_POINT"/{dev,proc,run,sys,tmp,mnt,media}
    sudo chmod 1777 "$MOUNT_POINT/tmp"


    sync
    cleanup_mount "$MOUNT_POINT" "$LOOP_DEV"
    LOOP_DEV=""
    sudo rmdir "$MOUNT_POINT" 2>/dev/null || true

    sudo chown "$(id -u):$(id -g)" "$ROOTFS_NAME"

    rm -f 01-netcfg.yaml
    # shrink_image
    echo "Image Build Successfully"
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
