#!/bin/bash
set -e

OUTPUT="$1"
SIZE_MB="${IMAGE_SIZE_MB:-2048}"
LOCAL_IMG="/tmp/rootfs.img"

# Create and format the image locally (not on a bind mount)
dd if=/dev/zero of="$LOCAL_IMG" bs=1M count="$SIZE_MB" status=progress
mkfs.ext4 -F "$LOCAL_IMG"

mkdir -p /mnt/disk
mount -o loop "$LOCAL_IMG" /mnt/disk

cp -a /bin /boot /etc /home /lib /lib64 /opt /root /sbin /srv /usr /var /mnt/disk/

mkdir -p /mnt/disk/{dev,proc,run,sys,tmp,mnt,media}
chmod 1777 /mnt/disk/tmp

umount /mnt/disk

# Copy the finished image to the bind-mounted output path
cp "$LOCAL_IMG" "$OUTPUT"
rm -f "$LOCAL_IMG"
