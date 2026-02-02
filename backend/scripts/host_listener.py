import socket
import sys
import time

# Configuration
# This must match the 'uds_path' in your Firecracker config
UDS_PATH = "/tmp/firecracker.socket"
VM_PORT = 5005


def connect_to_vm():
    print(f"Connecting to VM via {UDS_PATH}...")
    try:
        # Connect to the Firecracker Unix Socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(UDS_PATH)

        # Firecracker Protocol: Send "CONNECT <PORT>\n" to bridge to the Guest
        # This tells Firecracker: "Please connect me to Port 5005 inside the VM"
        command = f"CONNECT {VM_PORT}\n"
        sock.sendall(command.encode())

        print("Connected! Waiting for messages...")

        # Read the stream
        while True:
            data = sock.recv(1024)
            if not data:
                print("Connection closed by VM.")
                break
            sys.stdout.write(data.decode())
            sys.stdout.flush()

    except ConnectionRefusedError:
        print("Error: Could not connect to Firecracker. Is the VM running?")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    connect_to_vm()
