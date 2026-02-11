#!/bin/bash
set -euo pipefail

INPUT_FLAGS=("$@") # Capture all arguments as array

ARCH="$(uname -m)"
FC_URL="https://github.com/firecracker-microvm/firecracker/releases/download/v1.7.0/firecracker-v1.7.0-${ARCH}.tgz"
FC_DIR="/usr/local/bin"
DOCKER_URL="https://download.docker.com/linux/ubuntu"
TOOLS=("curl" "docker" "ip" "iptables" "mkfs.ext4" "debootstrap" "firecracker" "kvm")
KEY_DIR="/etc/apt/keyrings"
DOCKER_GPG_URL="${KEY_DIR}/docker.gpg"
DOCKER_APT_REPO_DIR="/etc/apt/sources.list.d/docker.list"
APP_USER="vm_manager"

if [ "${#INPUT_FLAGS[@]}" -lt "${#TOOLS[@]}" ]; then
    echo "Error: Expected ${#TOOLS[@]} binary flags, got ${#INPUT_FLAGS[@]}."
    exit 1
fi

install_docker() {
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
    local tmp_dir
    tmp_dir=$(mktemp -d)
    sudo mkdir -p "$FC_DIR"
    curl -fsSL "$FC_URL" | tar -xz -C "$tmp_dir"
    sudo mv "$tmp_dir/firecracker-v1.7.0-${ARCH}" "$FC_DIR/firecracker"
    rm -rf "$tmp_dir"
    sudo chmod +x "$FC_DIR/firecracker"
}

create_vm_manager_user() {
    if ! id "$APP_USER" &>/dev/null; then
        sudo useradd -r -m -s /usr/sbin/nologin "$APP_USER"
    fi
    if getent group kvm >/dev/null; then
        sudo usermod -aG kvm "$APP_USER"
    fi
    sudo tee /etc/sudoers.d/${APP_USER} <<EOF
${APP_USER} ALL=NOPASSWD: /usr/local/bin/firecracker, /usr/bin/debootstrap, /sbin/iptables, /usr/bin/ip
EOF

    sudo chmod 440 /etc/sudoers.d/${APP_USER}
    sudo visudo -cf /etc/sudoers.d/${APP_USER}
}

sudo apt update
create_vm_manager_user
for i in "${!TOOLS[@]}"; do
    TOOL_NAME="${TOOLS[$i]}"
    SHOULD_INSTALL="${INPUT_FLAGS[$i]}"
    if [[ "$SHOULD_INSTALL" == "1" ]]; then
        case "$TOOL_NAME" in
        "docker")
            install_docker
            ;;
        "curl")
            sudo apt install -y curl
            ;;
        "ip")
            sudo apt install -y iproute2
            ;;
        "iptables")
            sudo apt install -y iptables
            ;;
        "mkfs.ext4")
            sudo apt install -y e2fsprogs
            ;;
        "debootstrap")
            sudo apt install -y debootstrap
            ;;
        "firecracker")
            install_firecracker_globally
            ;;
        esac
    fi
done
echo "CERA Deps success"
