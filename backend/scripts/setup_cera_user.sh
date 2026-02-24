# #!/bin/bash

# set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# CONFIG_DIR="${SCRIPT_DIR}/config"
# source "$CONFIG_DIR/config.sh"
# create_app_user() {
#     if id "$APP_USER" &>/dev/null; then
#         echo "User '$APP_USER' already exists."
#     else
#         useradd -r -m -s /usr/sbin/nologin "$APP_USER"
#         echo "User '$APP_USER' created Successfully."
#     fi
# }

# configure_groups() {
#     for grp in kvm docker; do
#         if getent group "$grp" >/dev/null 2>&1; then
#             usermod -aG "$grp" "$APP_USER"
#             echo "Adding ${APP_USER} in ${grp}"
#         fi
#     done
# }

# install_sudoers() {
#     local sudoers_file="/etc/sudoers.d/${APP_USER}"

#     sed "s/{{APP_USER}}/$APP_USER/" "${SCRIPT_DIR}/templates/sudoer_file.template" > $sudoers_file
#     chmod 440 "$sudoers_file"

#     if !visudo -cf "$sudoers_file"; then
#         rm -f $sudoers_file
#         exit 1
#     fi
#     echo "${APP_USER} Added Successfully to sudoers"
# }

# create_directories() {
#     mkdir -p "$CERA_DATA_DIR" "$CERA_IMG_DIR" "$CERA_RUN_DIR" "$MOUNT_POINT"
#     chown "$APP_USER":"$APP_USER" "$CERA_DATA_DIR" "$CERA_IMG_DIR" "$CERA_RUN_DIR"
#     mkdir -p "$CERA_DISKS_DIR"
#     chown root:root "$CERA_DISKS_DIR"

# }
# configure_kvm() {
#     if [ -e /dev/kvm ]; then
#         chown root:kvm /dev/kvm
#         chmod 660 /dev/kvm
#     else
#         echo "[WARN] Enable virtualization in BIOS/UEFI."
#     fi
# }

# main() {
#     if [ "$(id -u)" -ne 0 ]; then
#         echo "This Script needs to be run as root" >&2
#         exit 1
#     fi
#     create_app_user
#     configure_groups
#     install_sudoers
#     create_directories
#     configure_kvm
# }

# main "$@"

#     # cat "${SCRIPT_DIR}/templates/sudoer_file.template"