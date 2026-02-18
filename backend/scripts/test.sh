#!/bin/bash

CONFIG_DIR="config"
source $CONFIG_DIR/config.sh

echo "CERA_DATA_DIR: $CERA_DATA_DIR"
echo "CERA_IMG_DIR:  $CERA_IMG_DIR"
echo "CERA_DISKS_DIR:$CERA_DISKS_DIR"
echo "CERA_RUN_DIR:  $CERA_RUN_DIR"
echo "IMAGE_NAME:    $ROOTFS_NAME"
echo "KERNEL_PATH:   $KERNEL_PATH"
echo "UDS_PATH:      $UDS_PATH"
echo "MOUNT_POINT:   $MOUNT_POINT"
echo "FC_URL:        $FC_URL"
