## sis3316 GUI ###

Adapted from [link to repo](https://github.com/dougUCN/sis3316_gui).

Start the GUI, sis3316 readout server, and the live plotter using 

```
./START_GUI.sh
```

[Instructions for setting up the SIS3316](https://github.com/dougUCN/SIS3316)

If you would like the change the default gui launch settings, edit defaults.in

### Python Environment and Dependencies ###

Required libraries are located in dependencies.txt

A python virtual environment (venv) is recommended for all and required by some computers. Please install the required libraries in the virtual environment. To do so, follow:

1. Go to the desired directory through terminal
2. Use the command ```python -m venv venv``` to create a venv folder (the second venv is the name of the folder, feel free to change it to something else).
3. To activate the venv, enter the command ```source ./venv/bin/activate``` (Linux/macOS/Ubuntu) or ```venv\Scripts\activate.bat``` (Windows) in the terminal
4. Install desired Python libraries (```pip install -r dependencies.txt``` to install libraries listed in the text file dependencies.txt in one go).

### Advanced Configuration Settings ###

Edit sis3316 settings in config.json

For documentation on advanced configuration file arguments, view `configHelp.txt` (easiest to just dump it to terminal with `cat`)

It will also be useful to refer to the manual for explanation on certain settings (this is also hosted on the OSF page)

### sis3316 Daq code ###

The sis3316 python interface code in this gui folder may not be up to date. [Latest, stable version](https://github.com/dougUCN/SIS3316)

Note that the sis3316 can be run entirely with command line programs, located in the `tools` folder

### File I/O ###

Use quickParse.py to make some quick plots from the binary files


