## sis3316 GUI ###

Adapted from [link to repo](https://github.com/dougUCN/sis3316_gui).

Start the GUI, sis3316 readout server, and the live plotter using 

```
./START_GUI.sh
```

---

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

After creating the script, run `chmod +x connect_ethernet.sh` followed by `sudo ./connect_ethernet.sh` to establish connection. 

> ⚠️ The static IP assignment is temporary and must be redone after reboot.

To test the connection:

```bash
ping [IP_ADDRESS_OF_SIS3316]
```

If you would like to change the default GUI launch settings, edit `defaults.in`.

---

### Python Environment and Dependencies ###

Required libraries are located in dependencies.txt

A python virtual environment (venv) is recommended.

```bash
python -m venv venv
source ./venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat   # Windows

pip install -r dependencies.txt
```

---

### How the Program Works (Startup -> Data Acquisition Flow) ###

#### **Startup Sequence** ####
1. **Connection:** Set up a static IP for the SIS3316 digitizer (via `connect_ethernet.sh`)
2. **Launching GUI:** Run `./START_GUI.sh` which:
      - Starts the `readoutServer.py` (DAQ data puller)
      - Launches the Qt GUI (`sis3316_gui.py`)
      - Initiates `livePlotter.py` for online visualization

#### **Data Acquisition Flow** ####
1. **Hardware Initialization:**
      - Loads setting from `config.json` (path specified in `defaults.in`)
      - Configurates digitizer channels, groups, and trigger parameters via the Python wrapper (in `sis3316/`)
2. **Trigger and Buffer Setup:**
      - Internal or external triggers can be selected per-channel via flags like `"intern_trig"` or `"extern_trig"`
      - FIFO and MAW buffers are enabled based on `event_maw_ena`, `event_format_mask`, and timing windows
3. **Streaming & Storage:**
      - Once acquisition starts, binary waveform data is streamed via UDP and written to `.dat` files
4. **Real-time Display:**
      - `livePlotter.py` parses `.dat` files on the fly and generates:
           - ADC histogram
           - Time histogram
5. **Post-Processing:**
      - Use `quickParse.py` or `Peak_Analysis.ipynb` to extract peaks, visualize events, and perform further analysis

---

### Configuration Settings Guide (`config.json`) ###

To modify runtime settings, edit `config.json`. It supports:

#### Global Flags

| Flag               | Description |
|--------------------|-------------|
| `jumbo_ena`        | Enables jumbo Ethernet frames (MTU = 9000) |
| `extern_ts_clr_ena`| Enables external timestamp clear |
| `extern_trig_ena`  | Enables external triggers |
| `nim_ui_as_veto`   | Treat NIM UI input as veto source |
| `nim_ui_as_ts_clear` | Use NIM input to clear timestamp |
| `nim_ti_as_te`     | NIM input as trigger enable |
| `trig_as_veto`     | Converts any trigger into veto logic |
| ...                | See `configHelp.txt` for complete list |

#### Channel-Level Configuration

| Key                   | Description |
|------------------------|-------------|
| `flags`               | e.g., `intern_trig`, `invert`, etc. |
| `gain`                | `0` = ±5V, `1` = ±2V, `2` = ±1.9V |
| `termination`         | Enable 50Ω input termination |
| `event_maw_ena`       | Enable moving average buffer |
| `event_format_mask`   | Controls saved data format (bitmask) |
| `fir_energy_peaking_time` | Peaking time for FIR filter |
| `fir_energy_gap_time`     | Gap time for FIR filter |
| `event_pickup_index`  | Sets event pickup strategy |

#### Group-Level Configuration

| Key              | Description |
|------------------|-------------|
| `enable`         | Enables this digitizer group |
| `gate_window`    | Trigger gate duration |
| `maw_window`     | MAW buffer size |
| `pileup_window`  | Pileup rejection window |
| `delay`          | Pre-trigger delay |
| `accumN_window`  | Accumulators for integration |

#### Trigger Configuration

| Key              | Description |
|------------------|-------------|
| `enable`         | Enables trigger logic |
| `threshold`      | Trigger threshold (trapezoidal sum + 0x8000000) |
| `maw_peaking_time` | MAW filter peaking time |
| `maw_gap_time`     | MAW flat-top time |
| `cfd_ena`        | Constant Fraction Discrimination (0: off, 3: on) |

> For extended documentation, run `cat configHelp.txt` or refer to the SIS3316 manual.

---

### sis3316 Daq code ###

The sis3316 python interface code in this gui folder may not be up to date. [latest stable repo](https://github.com/dougUCN/SIS3316)

Command-line tools for scripting DAQ without GUI are located in the `tools/` folder.

---

### File I/O ###

Use quickParse.py for simple waveform analysis

Example:
```
python quickParse.py -f ./Tests/runX/ch00.dat -adc -eventSpacing
```
Advanced analysis is available via `Peak_Analysis.ipynb`

---
