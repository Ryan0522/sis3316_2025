## sis3316 GUI ###

Start the GUI, sis3316 readout server, and the live plotter using 

```
./START_GUI.sh
```

[Instructions for setting up the SIS3316](https://github.com/dougUCN/SIS3316)

If you would like the change the default gui launch settings, edit defaults.in

### Dependencies ###

See dependencies.txt

### Advanced Configuration Settings ###

Edit sis3316 settings in config.json

For documentation on advanced configuration file arguments, view `configHelp.txt` (easiest to just dump it to terminal with `cat`)

It will also be useful to refer to the manual for explanation on certain settings (this is also hosted on the OSF page)

### sis3316 Daq code ###

The sis3316 python interface code in this gui folder may not be up to date. [Latest, stable version](https://github.com/dougUCN/SIS3316)

Note that the sis3316 can be run entirely with command line programs, located in the `tools` folder

### File I/O ###

Use quickParse.py to make some quick plots from the binary files


