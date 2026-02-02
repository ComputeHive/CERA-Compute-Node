import subprocess
import os
import sys

# --- Configuration ---
IMAGE_FILE = "ubuntu-22.04.ext4"
BUFFER_MB = 256  # Free space to leave on the disk (Vital for logs/temp files)


def run_cmd(cmd):
    """Runs a shell command and returns stdout."""
    print(f"-> Running: {cmd}")
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command:\n{e.output.decode('utf-8')}")
        sys.exit(1)


def main():
    if not os.path.exists(IMAGE_FILE):
        print(f"Error: {IMAGE_FILE} not found.")
        sys.exit(1)

    print(f"=== Shrinking {IMAGE_FILE} to used size + {BUFFER_MB}MB buffer ===")

    # 1. Check Filesystem (Required before resizing)
    print("[1/4] Checking filesystem integrity...")
    try:
        # -f forces check, -p automatically repairs safely
        subprocess.check_call(f"e2fsck -fp {IMAGE_FILE}", shell=True)
    except subprocess.CalledProcessError as e:
        # e2fsck returns 1 if it corrected errors, which is fine
        if e.returncode not in [0, 1]:
            print("Filesystem check failed critically.")
            sys.exit(1)

    # 2. Calculate Minimum Size
    print("[2/4] Calculating minimum size...")
    output = run_cmd(f"resize2fs -P {IMAGE_FILE}")
    # Output format: "Estimated minimum size of the filesystem: 12345"
    min_blocks = int(output.strip().split(":")[-1])

    # Calculate new size in blocks (4KB blocks usually)
    # resize2fs -P gives 4k blocks.
    # We add the buffer: (BUFFER_MB * 1024 * 1024) / 4096 blocks
    buffer_blocks = int((BUFFER_MB * 1024 * 1024) / 4096)
    target_blocks = min_blocks + buffer_blocks

    # Calculate target size in standard units for display (e.g. "500M")
    target_size_mb = (target_blocks * 4096) / (1024 * 1024)
    print(f"      Min Blocks: {min_blocks}")
    print(f"      New Blocks: {target_blocks} (~{target_size_mb:.2f} MB)")

    # 3. Resize Filesystem
    print(f"[3/4] Resizing filesystem to {target_blocks} blocks...")
    run_cmd(f"resize2fs {IMAGE_FILE} {target_blocks}")

    # 4. Truncate File
    # resize2fs shrinks the logic, but the file size remains. truncate cuts the file.
    # Block size is almost always 4096 for ext4 created by our script.
    final_bytes = target_blocks * 4096
    print(f"[4/4] Truncating file to {final_bytes} bytes...")
    run_cmd(f"truncate -s {final_bytes} {IMAGE_FILE}")

    print("=== Success! Image shrunk. ===")
    print(f"Run 'ls -lh {IMAGE_FILE}' to see the new size.")


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run with sudo (required for filesystem checks).")
        sys.exit(1)
    main()
