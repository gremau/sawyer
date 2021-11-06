# sawyer

The `sawyer` python package helps users manage workflows and develop
processing pipelines for time series data from datalogger and sensor networks.
The package is built with environmental observations, like meteorological
measurements, in mind. Data management and processing steps are defined using
a set of YAML configuration files.

`sawyer` is useful for small to medium sized projects, and using these tools
requires some proficiency with python scripting and using the command line.
The package requires `pandas`, `matplotlib`, `scipy` (for gapfilling), and
`ruamel.yaml`.

WARNING: Documentation here is still being built - feel free to send me
questions or suggestions.

## Assumptions and functionality

### Incoming data types

The `sawyer` package assumes incoming raw data are time series in a tabular
format. Data must be parsed into a `pandas` DataFrame with a [datetime row index](
https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#indexing)
and one or more observational variables in the column index. Missing observations
are ok, but in general `sawyer` will regularize the time series, and irregular
time series may not be handled well.

### Project organization

`Sawyer` projects are organized around data loggers (and their output tables)
as the fundamental sources for a data pipeline. There can be many loggers in
a `sawyer` project, but each logger should have a unique name, and `sawyer` 
processes and outputs data from each logger in the project separately.

### Data processing levels and quality flags

`Sawyer` data processing pipelines operate using data levels. The incoming data
files are designated as `raw` and will not be altered. As `raw` data are
processed, new files are created at a higher data level, and flag columns
will be added alongside each data column. Flag columns indicate the quality
checks, data filtering, or gapfilling applied to the data level. There can be
multiple data levels in a project, and data levels above `raw` typically become
the source for other, higher levels.

The default data levels are similar to the levels used by
[Ameriflux](https://ameriflux.lbl.gov/data/aboutdata/data-processing-levels/).
The AmeriFlux levels are a useful conceptual framework for processing
environmental data, but users may implement their own levels and naming using
the configuration files.

### Gapfilling

`Sawyer` can gapfill variables using a few straightforward methods. Some of
these methods are sound, and some might not be depending on the data. So, be
careful and look closely at the results you get.

### Metadata

The `sawyer` package aims to collect and preserve metadata during data
processing. I'm working on some ways to output structured metadata for
data publication, but still in early stages.

## Installation

You can install `sawyer` using `pip`, but its not at PyPI yet. Either clone
this repository to your local environment and install with:

    pip install path/to/sawyer/

or install direct from GitHub:

    pip install git+git://github.com/gremau/sawyer@main

Note that there is also a `dev` branch, which might be working great or broken.
Ask me if you want to know the status.

## Raw data preparation

It is best to try to collect your raw data following a few conventions, and
then organize your raw data logger files a little bit, before you start
with `sawyer`. 

### Time indexes and variable naming

Make sure your data logger is adding an appropriate timestamp, preferably in
[ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format, such as
`YYYY-MM-DD hh:mm:ss`, to every observation collected. Most data loggers will
do this already, but using files that have been modified from this standard
may be difficult to parse. It is also advisable to either avoid making any
timekeeping changes at the data logger level, such as adjusting the clock
for daylight savings, or document them thoroughly.

Also make sure that all variables recorded in your raw data files have
unique and intelligible names (column headers). Sensor networks can be complex
and often have multiple observations of the same variable from different
sensor positions or replicates. It is wise to program your datalogger to name
variables so that the source of the data stream is clear. AmeriFlux maintains
some [sensible conventions](
https://ameriflux.lbl.gov/data/aboutdata/data-variables/) for flux sites that
suggest using the pattern `VARTYPE_H_V_R`, where

 * VARTYPE is the variable/sensor identifier (AirTC, CO2sensor, etc)
 * H is the horizontal position (1, 2, 3 in an arbitrary number scheme, or a distance/direction)
 * V is the vertical position (depth or height)
 * R is the replicate number (optional)

If data logger programming changes, the name of a variable in the resulting
data file might change even though the underlying data stream or source hasn't.
Be sure to document all such variable name changes.`sawyer` will allow
consistent naming to be used in processed files if configurations are set
properly.

### Raw data directory

Make a raw data directory with the project name, and then create
subdirectories that are named uniquely for each logger. Then, put the raw data
files for each logger into these subdirectories. You will point `sawyer` to 
this directory using the project configuration file (see below).

## Configuration

Data processing pipelines are defined in a set of YAML configuration files. All
configurations should go in a `sawyer_config/` directory accesible from your
working directory. This directory contains several global configuration files
and a subdirectory with configuration files for each data logger in the project.
All loggers have a unique name `lname`. Configurations include:

 * `project.yaml`: defines project information, data source location, 
    data processing levels, and output locations.
 * `loggers.yaml`: defines a set of loggers, each with a unique name
    `lname`, that are collecting the data
 * `qa_flags.yaml`: defines data flagging and filtering steps for all
    loggers.
 * `{lname}/var_rename.yaml`: defines changes in column variable names over
    time in case sensors/data streams are renamed at logger `lname`.
 * `{lname}/qa_flags.yaml`: defines data flagging and filtering steps for
    logger `lname`.
 * `{lname}/gafill.yaml`: defines data gapfilling steps for logger `lname`.

## Licensing

MIT license


