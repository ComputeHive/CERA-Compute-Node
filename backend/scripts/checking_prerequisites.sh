#!/bin/bash

MISSING_TOOLS=""
REQUIRED_TOOLS=("curl" "docker" "ip" "iptables" "mkfs.ext4" "debootstrap" "firecracker")

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &>/dev/null; then
        MISSING_TOOLS+="$tool "
    fi
done

if ! ([ -e /dev/kvm ] && [ -r /dev/kvm ] && [ -w /dev/kvm ]); then
    MISSING_TOOLS+="enable virtualization in BIOS/UEFI "
fi

echo $MISSING_TOOLS
