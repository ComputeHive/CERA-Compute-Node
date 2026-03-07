#!/bin/bash
set -e

OUTPUT="$1"
SIZE_MB="${IMAGE_SIZE_MB:-3076}"
TAR_FILE="$2"

truncate -s "${SIZE_MB}M" "$OUTPUT"
mkfs.ext4 -F "$OUTPUT"

mkdir -p /mnt/disk
mount -o loop "$OUTPUT" /mnt/disk

tar xf "$TAR_FILE" -C /mnt/disk

mkdir -p /mnt/disk/{dev,proc,run,sys,tmp,mnt,media}
chmod 1777 /mnt/disk/tmp

umount /mnt/disk
