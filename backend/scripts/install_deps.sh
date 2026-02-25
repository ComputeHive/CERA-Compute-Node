#!/bin/bash
set -euo pipefail

INPUT_FLAGS=("$@")

TOOLS=("curl" "docker" "ip" "iptables" "mkfs.ext4" "debootstrap" "firecracker" "kvm")

if [ "${#INPUT_FLAGS[@]}" -lt "${#TOOLS[@]}" ]; then
    echo "Error: Expected ${#TOOLS[@]} binary flags, got ${#INPUT_FLAGS[@]}."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/config"
source "$CONFIG_DIR/config.sh"

install_docker() {
    echo "Installing Docker Now :>"
    sudo apt install -y ca-certificates gnupg apt-transport-https
    sudo install -m 0755 -d "${KEY_DIR}"
    curl -fsSL "${DOCKER_URL}/gpg" | sudo gpg --dearmor -o ${DOCKER_GPG_URL} --yes
    sudo chmod a+r ${DOCKER_GPG_URL}
    echo "deb [arch=$(dpkg --print-architecture) signed-by=${DOCKER_GPG_URL}] $DOCKER_URL $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee "$DOCKER_APT_REPO_DIR" >/dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl enable --now docker
}

install_firecracker_globally() {
    echo "Installing Firecracker Now :>"
    local tmp_dir
    tmp_dir=$(mktemp -d)
    sudo mkdir -p "$FC_DIR"
    curl -fsSL "$FC_URL" | tar -xz -C "$tmp_dir"
    sudo mv "$tmp_dir/firecracker-v1.7.0-${ARCH}" "$FC_DIR/firecracker"
    rm -rf "$tmp_dir"
    sudo chmod +x "$FC_DIR/firecracker"
}
configure_kvm() {
    echo "Configuring KVM permissions :>"
    if [ -e /dev/kvm ]; then
        sudo chown root:kvm /dev/kvm
        sudo chmod 660 /dev/kvm
        echo "KVM permissions configured successfully."
    else
        echo "[ERROR]: /dev/kvm not found. Enable virtualization in BIOS/UEFI."
        exit 1
    fi
}

sudo apt update

for i in "${!TOOLS[@]}"; do
    TOOL_NAME="${TOOLS[$i]}"
    SHOULD_INSTALL="${INPUT_FLAGS[$i]}"
    if [[ "$SHOULD_INSTALL" == "1" ]]; then
        case "$TOOL_NAME" in
        "docker")
            install_docker
            ;;
        "curl")
            echo "Installing Curl Now :>"
            sudo apt install -y curl
            ;;
        "ip")
            echo "Installing iproute Now :>"
            sudo apt install -y iproute2
            ;;
        "iptables")
            echo "Installing iptables Now :>"
            sudo apt install -y iptables
            ;;
        "mkfs.ext4")
            echo "Installing mkfs.ext4 Now :>"
            sudo apt install -y e2fsprogs
            ;;
        "debootstrap")
            echo "Installing debootstrap Now :>"
            sudo apt install -y debootstrap
            ;;
        "firecracker")
            install_firecracker_globally
            ;;
        esac
    fi
done
