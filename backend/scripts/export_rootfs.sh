#!/bin/bash
set -e

IMG="$1"
mkdir -p /mnt/disk
mount -o loop "$IMG" /mnt/disk

cp -a /bin /boot /etc /home /lib /lib64 /opt /root /sbin /srv /usr /var /mnt/disk/

mkdir -p /mnt/disk/{dev,proc,run,sys,tmp,mnt,media}
chmod 1777 /mnt/disk/tmp

umount /mnt/disk
