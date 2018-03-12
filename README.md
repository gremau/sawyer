# datalog

The `datalog` python package helps users manage and quality assure incoming time-series data files. The package is built for environmental sensor networks that have one or more dataloggers that periodically return files containing time series data to a specified directory. File management and quality assurance steps are defined using a set of YAML configuration files.

Requires pandas (which brings in NumPy) and pyYAML packages. Matplotlib should be installed to use the plotting functions. If you use the Anaconda package manager these are easy to get.

WARNING: Documentation here is still being built, so this may be challenging to use. Feel free to send me questions or suggestions...

## Project and site organization

Datalog is used to organize and qa data at the project level.

Projects consist of one or more sites. 

Sites have one or more data sources, with the default data source called 'main'.

Project names and data paths are specified in the project_conf.yaml file. Site 

## Incoming data expectations

Variable names = VARTYPE_H_V_R

Where:

    * VARTYPE is the variable/sensor identifier (AirTC, CO2sensor, etc)
    * H is the horizontal position (1, 2, 3 in an arbitrary number scheme, or a distance/direction)
    * V is the vertical position (depth or height) (
    * R is the replicate number (optional)

### Datalogger file naming

### Sites, dataloggers, and sensor replication




## Classes:

### Projects

The top-level class. Configured with `proj.yml`. Each project may consist of many individual research sites, each of which may have many measurements from dataloggers or other sources.

### Site

Class referring to a research location. Configured with `sitename.yaml`. The location has a bunch of attributes and a set of measurement locations. It may contain zero or more dataloggers, and zero or more data tables.

Within each site, measuremnets are identified with H_V_R (horizontal, vertical, replicate) notation.

### Datalogger

### Datatable


