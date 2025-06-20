## sis3316 GUI ###

Adapted from [link to repo](https://github.com/dougUCN/sis3316_gui).

Start the GUI, sis3316 readout server, and the live plotter using 

```
./START_GUI.sh
```
### Setting up SIS3316 ###

To establish ethernet connection, a simple method is to assign a static IP to the digitizer's MAC-Address. 

First, create shell script (we call it `connect_ethernet.sh` here) with contents

```
#!/bin/bash

# Add static ARP entry for the SIS3316 digitizer
arp -i enp3s0 -s [IP_ADDRESS_OF_SIS3316] 00:00:56:31:61:XX

# Network TCP/UDP tuning to support high-bandwith applications
sysctl -w net.core.rmem_max=8388608
sysctl -w net.core.wmem_max=8388608
sysctl -w net.core.rmem_default=65536
sysctl -w net.core.wmem_default=65536
sysctl -w net.ipv4.udp_mem='8388608 8388608 8388608'
sysctl -w net.ipv4.tcp_rmem='4096 87380 8388608'
sysctl -w net.ipv4.tcp_wmem='4096 65536 8388608'
sysctl -w net.ipv4.tcp_mem='8388608 8388608 8388608'
sysctl -w net.ipv4.route.flush=1

# Enable jumbo frames
ip link set enp3s0 mtu 9000

# Show ARP Table
arp -a
```

After creating the script, run `chmod +x connect_ethernet.sh` followed by `sudo ./connect_ethernet.sh` to establish connection. (IMPORTANT!) This static IP is temporary so after every reboot `sudo ./connect_ethernet.sh` should be ran once. 

To test the connection, run `ping [IP_ADDRESS_OF_SIS3316]`, you should see the message `64 bytes from [IP_ADDRESS_OF_SIS3316]: icmp_seq...` repeatedly from the terminal.

If you would like the change the default gui launch settings, edit defaults.in

### Python Environment and Dependencies ###

Required libraries are located in dependencies.txt

A python virtual environment (venv) is recommended for all and required by some computers. Please install the required libraries in the virtual environment. To do so, follow:

1. Go to the desired directory through terminal
2. Use the command ```python -m venv venv``` to create a venv folder (the second venv is the name of the folder, feel free to change it to something else).
3. To activate the venv, enter the command ```source ./venv/bin/activate``` (Linux/macOS/Ubuntu) or ```venv\Scripts\activate.bat``` (Windows) in the terminal
4. Install desired Python libraries (```pip install -r dependencies.txt``` to install libraries listed in the text file dependencies.txt in one go).

### How the Program Works (Startup -> Data Acquisition Flow) ###

1. **Initialization & Configuration Load**
   - On launch, the program reads the `config.json` to fetch runtime flags and parameter values.
3. **Hardware and Driver Setup**
   - Initializes the SIS3316 digitizer: 
5. **Data Stream Configuration**
6. **Acquisition Start**
7. **Data Processing Loop**
8. **Shutdown**

### Advanced Configuration Settings ###

Edit sis3316 settings in config.json

For documentation on advanced configuration file arguments, view `configHelp.txt` (easiest to just dump it to terminal with `cat`)

It will also be useful to refer to the manual for explanation on certain settings (this is also hosted on the OSF page)

### sis3316 Daq code ###

The sis3316 python interface code in this gui folder may not be up to date. [Latest, stable version](https://github.com/dougUCN/SIS3316)

Note that the sis3316 can be run entirely with command line programs, located in the `tools` folder

### File I/O ###

Use quickParse.py to make some quick plots from the binary files


