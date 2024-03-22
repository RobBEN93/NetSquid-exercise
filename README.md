I was just tinkering with NetSquid, the quantum network simulator tutorial's Ping Pong program from the documentation. I included a simple bit flip from the QuantumErrorModel class and added memory to each node for storing and retrieving a quantum state before resending. The idea is to include a simple CSS codes implementation and other QEC techniques for different error models just for the learning process.

You'll need the NetSquid package to run this. 

## Installing NetSquid

This section provides a simplified guide to installing NetSquid, a tool for simulating quantum networks. Ensure your system meets the prerequisites before proceeding.

### Prerequisites

- **Operating System**: Linux or MacOS (64-bit). Windows users can use WSL (Windows Subsystem for Linux).
- **Python**: Version 3.6 or higher.
- **pip**: Version 19 or higher. Upgrade using `pip3 install --upgrade pip`.

### Installation Steps

1. **NetSquid Forum Account**: Register at the [NetSquid Forum](https://forum.netsquid.org) to obtain login credentials. You'll need these for the next step.

2. **Install NetSquid**: Open a terminal and run the following command, replacing `<username>` and `<password>` with your forum credentials:

    ```bash
    pip3 install --user --extra-index-url https://<username>:<password>@pypi.netsquid.org netsquid
    ```

    Remove `--user` to install system-wide (requires admin rights) or if using a virtual environment.

3. **Verify Installation**: Test if NetSquid is correctly installed by running:

    ```python
    import netsquid as ns
    ns.test()
    ```

If you encounter any issues, check your system meets the prerequisites or consult the NetSquid forum for support.
