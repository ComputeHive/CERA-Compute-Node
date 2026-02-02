from socket import socket, SOCK_STREAM, AF_VSOCK
from time import sleep
from datetime import datetime

# CID 2 is ALWAYS the host in VSOCK
HOST_CID = 2
HOST_PORT = 5252

print(">>> VM Sender Starting...")

while True:
    try:
        # Create VSOCK socket
        s = socket(AF_VSOCK, SOCK_STREAM)
        s.connect((HOST_CID, HOST_PORT))

        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            msg = f"Hello from VM! Time is {current_time}"
            s.sendall(msg.encode())
            sleep(1)

    except Exception as e:
        print(f"Connection failed ({e}). Retrying in 2s...")
        sleep(2)
