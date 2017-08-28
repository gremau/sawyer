# datalog

The `datalog` python package helps users manage and quality assure incoming time-series data files. The package is built for environmental sensor networks that have one or more dataloggers that periodically return files containing continuous data to a specified directory. File management and quality assurance steps are defined using a set of YAML configuration files.

WARNING: Documentation here is still being built, so this may be challenging to use. Feel free to send me questions or suggestions...

## Incoming data expectations

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


