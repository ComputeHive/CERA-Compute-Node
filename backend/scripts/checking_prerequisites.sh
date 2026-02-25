#!/bin/bash

MISSING_TOOLS=""
REQUIRED_TOOLS=("curl" "docker" "ip" "iptables" "mkfs.ext4" "debootstrap" "firecracker" "kvm")

for tool in "${REQUIRED_TOOLS[@]}"; do
    if [ "$tool" = "kvm" ]; then
        if ! ([ -e /dev/kvm ] && [ -r /dev/kvm ] && [ -w /dev/kvm ]); then
            MISSING_TOOLS+="kvm "
        fi
    else
        if ! command -v "$tool" &>/dev/null; then
            MISSING_TOOLS+="$tool "
        fi
    fi
done

echo $MISSING_TOOLS
