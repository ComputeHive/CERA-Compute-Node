## CERA Compute Node

### Installation:

for linux systems, run the following command

```bash
    bash install.sh
```

for windows, run the following command

```powershell
    powershell -ExecutionPolicy Bypass -File setup.ps1
```

### Running the Compute Node for the first time

You must create a user to be able run the compute node system, follow these steps

1. Run the Compute Node Desktop application by running the following commands

```bash
    cd app/CERA-VM-Manager/
    npm run dev
```

2. Run the Coordinator Server which may exist in a subdirectory main CERA directory after installing it by running the following command

```bash
    poetry env activate # get the link of virtualenv to activate (run this command before continue to next command)
    python3 run.py # use python if you're on windows
```

3. Run the Blockchain network which may exist in a subdirectory of main CERA directory

```bash
    npm run node
```

4. Fill the data required in sign up page and choose a wallet address from those created by network you just ran previously

5. Run the backend of Compute Node by running the following command from Compute Node main directory

```bash
    source cera-backend/bin/activate
    python3 main.py
```

6. Sign in in the desktop using your credentials

### Running the Compute Node Later

the same steps as previous
