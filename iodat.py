""" 
Functions for loading various environmental monitoring data files

Greg Maurer
"""

import numpy as np
import datetime as dt
import pandas as pd
import subprocess as sp
import yaml
import os
import shutil
import re
import datalog.config as conf
import pdb

conf_path = conf.config_path
loggers = conf.loggers
datadirs = conf.datapaths
filename_dt_rexp = conf.filename_dt_rexp
filename_dt_fmt = conf.filename_dt_fmt

def get_datadir(logger, datadir='qa'):
    """
    Retrieve correct directory path for given logger and datadir type

    Args:
        logger (string): name of logger
        datadir (string): name of desired data directory (member of datadirs)

    Returns:
        p (string): a validated path name
        
    """
    if datadir in datadirs.keys():
        p = datadirs[datadir].replace('{LOGGER}', logger)
        if not os.path.isdir(p):
            raise ValueError('Query produced invalid path {0}'.format(p))
    else:
        raise ValueError('Available data directories are {0}'.format(
            datadirs.keys()))
    return p

def dt_from_filename(filename, rexp=filename_dt_rexp, fmt=filename_dt_fmt):
    """
    (\d{4}){1}([_-]\d{2}){5}
    """
    dtstr = re.search(rexp, filename).group(0)
    # Older files may be missing seconds - parse date anyway
    try:
        dtobj = dt.datetime.strptime(dtstr, fmt)
    except:
        dtobj = dt.datetime.strptime(dtstr, fmt[:-3])
    return dtobj

def get_file_collection(datapath, optmatch=None):
    """
    Read a list of filenames from a data directory, match against desired logger,
    and return the list and the file datestamps of each file. This function
    expects to find a directory full of files with the format 
    "prefix_<loggername>_<Y>_<m>_<d>_<H>_<M>_optionalsuffix.dat". For example:

    MNPclimoseq_Creosote_2017_03_17_11_55_00.dat

    Only returns filenames matching the lname (and optmatch) strings.
    """
    # Get a list of filenames in provided data directory
    files = os.listdir(datapath)
    files_m = files
    # Match optional strings if given
    if isinstance(optmatch, str): # optmatch must be a list
        optmatch = [optmatch]
    if optmatch is not None:
        for m in optmatch:
            files_m = [f for f in files_m if m in f]
    
    # Get file date and full path for each file. The file datestamp is
    # specified in the project configuration file.
    file_dt = []
    files_full = []
    for i in files_m:
        file_dt.append(dt_from_filename(i))
        files_full.append(os.path.join(datapath, i))
    return files_m, file_dt, files_full


def most_recent_filematch(datapath, optmatch=None):
    """
    Return name of most recent file in a directory with optional pattern
    matching.
    """
    files, dates, _ = get_file_collection(datapath, optmatch=optmatch)
    return files[dates.index(max(dates))], max(dates)

    
def load_most_recent(lname, datadir, optmatch=None):
    """
    Load the most recent file in a directory and return as pandas dataframe
    (with optional pattern matching)
    """
    p = get_datadir(lname, datadir)

    if 'raw' in datadir:
        raw_freq = conf.logger_c[lname]['rawfreq']
        _, f_dt, fs = get_file_collection(p, optmatch=optmatch)
        df = concat_raw_files(fs, optmatch=optmatch, iofunc=load_toa5,
                reindex=raw_freq)
    else:
        f, f_dt = most_recent_filematch(p, optmatch)
        df = datalog_in(os.path.join(p, f), lname=lname)
    
    return df, f_dt


#def read_project_conf(confdir=conf_path):
#    """
#    Read the project YAML configuration file from the datalog
#    configuration directory.
#
#    Args:
#        confdir (string): directory to look for YAML configuration files
#
#    Returns:
#        yamlf (dict): Returns a dictionary of configuration values
#                      from the YAML file
#    """
#    yamlfile = os.path.join(confdir, 'datalog_conf.yaml')
#    stream = open(yamlfile, 'r')
#    yamlf = yaml.load(stream)
#    return yamlf


def read_yaml_conf(lname, yamltype, confdir=conf_path):
    """
    Read a specified YAML configuration file from a given logger's datalog
    configuration directory. Checks the YAML file meta dictionary to ensure
    configuration is for the correct logger and type.

    Args:
        lname (string): logger identifier
        yamltype (string): identifies the YAML filename and configuration type
        confdir (string): directory to look for YAML configuration files

    Returns:
        yamlf (dict): Returns the "items" dictionary of configuration values
                      from the YAML file

    Raises:
        ValueError: Raises ValueError if the lname or yamltype parameters
                    do not match those found in the yaml file
    """
    if lname is 'all':
        yamlfile = os.path.join(confdir, yamltype + '.yaml')
    else:
        yamlfile = os.path.join(confdir, lname, yamltype + '.yaml')
    if os.path.isfile(yamlfile):
        stream = open(yamlfile, 'r')
        yamlf = yaml.load(stream)
        ylogger = yamlf['meta']['logger']==lname
        ytype = yamlf['meta']['conftype']==yamltype
        if not(ylogger) or not(ytype):
            raise ValueError('YAML file logger/type mismatch.')
        else:
            return yamlf['items']
    else:
        warn = "Warning: The requested YAML configuration ({0}) not present"
        print(warn.format(yamlfile))
        return dict()


def calculate_freq(idx):
    """
    Estimate the sampling frequency of a pandas datetime index
    """
    cfreq = (idx.max()-idx.min())/(len(idx)-1)
    cfreq = cfreq.seconds/60
    print("Calculated frequency is " + "{:5.3f}".format(cfreq) + " minutes")
    print("Rounding to " + str(round(cfreq)) + 'min')
    return str(round(cfreq)) + "min"


def load_toa5(fpathname) :
    """
    Load a specified TOA5 datalogger file (a Campbell standard output format)
    and return a pandas DataFrame object. DataFrame has a datetime index and
    user is warned if any measurement periods appear to be missing. Dataframe
    can be reindexed to fill in missing periods with NAN.

    Args:
        fpathname (str) : path and filename of desired AF file
    Return:
        parsed_df   : pandas DataFrame containing file data 
    """

    print('Parsing ' + fpathname)

    # Parse using Campbell timestamp
    parsed_df = pd.read_csv(fpathname, skiprows=( 0,2,3 ), header=0,
            parse_dates = { 'Date': [0]}, index_col='Date',
            na_values=['NaN', 'NAN', 'INF', '-INF'])
    
    return parsed_df


def concat_raw_files(files, iofunc=load_toa5, optmatch=None, reindex=None):
    """
    Load a list of raw datalogger files, append them, and then return a pandas
    DataFrame object. 

    Since files don't load in chronological order the resulting dataframe
    must either be reindexed with a requested value (reindex arg) or reordered
    with the index. Reindexing may add or remove rows (see reindex_to)
      
    Args:
        datapath: Path to directory of data files
        iofunc  : function used to load each file
        optmatch: optional string for matching filenames
        reindex: optional string with pandas frequency (default is None)
    Returns:
        ldf  : pandas DataFrame containing concatenated raw data
                      from one logger
    """
            
    # Get list of datalogger filenames and file datestamps from directory
    # files, files_dt = get_file_collection(datapath, optmatch=optmatch)
    # Initialize DataFrame
    ldf = pd.DataFrame()
    # Loop through each year and fill the dataframe
    for i in files:
        # Call load_toa5_file
        filedf = iofunc(i)
        # And append to ldf, 'verify_integrity' warns if there are
        # duplicate indices
        ldf = ldf.append(filedf, verify_integrity=True)
    # Either reindex (if requested) or order by index
    if reindex is not None:
        ldf = reindex_to(ldf, reindex)
    else:
        ldf.sort_index(inplace=True)

    return ldf

def reindex_to(df, freq_in='10T'):
    """
    Reindex dataframe to desired frequency
    """
    # Calculate frequency
    cfreq = calculate_freq(df.index)
    # Create index spanning all days from min to max date
    fullidx = pd.date_range(df.index.min(), df.index.max(), freq=freq_in)
    # Warn if observations are missing
    if len( df.index ) < len( fullidx ):
        print("WARNING: index frequency is less than expected!")
        print("Reindexing will introduce NaN values")
    elif len( df.index ) > len( fullidx ):
        print("WARNING: index frequency is greater than expected!")
        print("Reindexing may remove valid values")
    # Now reindex the dataframe
    print("Reindexing dataframe...")
    ridf = df.reindex( fullidx )
    return ridf


def rename_raw_variables(lname, rawpath, rnpath, confdir=conf_path):
    """
    Rename raw datalogger variables according to YAML configuration file

    Args:
        lname (string): logger identifier
        rawpath (string): raw datalogger file path
        rnpath (string): path to write renamed data files
        confdir (string): directory to look for YAML configuration files

    Returns:
        Does not return anything but writes new files in rnpath
    """
    # Get var_rename configuration file for logger
    yamlf = read_yaml_conf(lname, 'var_rename', confdir=confdir)
    # Get list of filenames and their file datestamps from the raw directory
    files, file_dt, _ = get_file_collection(rawpath)
    if bool(yamlf):
        # For each file, loop through each rename event and change headers
        for i, filename in enumerate(files):
            findvars, repvars = ([],[])
            # For each rename event, add variable changes to findvar/repvar
            # if the changes occurred after the file datestamp
            for j, key in enumerate(sorted(yamlf.keys())):
                rn = yamlf[key] # Get rename event j
                if rn["first_changed_dt"] > file_dt[i]:
                    findvars = findvars + rn["from"]
                    repvars = repvars + rn["to"]

            # Now read in file, replace target strings, write a new file
            filepath = os.path.join(rawpath, filename)
            with open(filepath, 'r') as file:
                filedata = file.read()
            for k, findvar in enumerate(findvars):
                repvar = repvars[k]
                #filedata = filedata.replace(findvar, repvar)
                filedata = re.sub(findvar, repvar, filedata)
            rn_filepath = os.path.join(rnpath, filename)
            with open(rn_filepath, 'w') as file:
                file.write(filedata)
    else:
        print('No rename configuration for {0}, copying raw files'.format(
            lname))
        for filename in files:
            shutil.copy(os.path.join(rawpath, filename), rnpath)


def datalog_out(df, lname, outpath, datestamp=None,
        prefix=None, suffix='00', ext='.txt'):
    """
    Write a delimited text file with a metadata header.
    """
    # Remove any underscores in suffix
    suffix = suffix.replace("_", "")

    if datestamp is not None:
        datestamp = datestamp.strftime(filename_dt_fmt)
    # Put together the output file name
    strlist = [prefix, lname, datestamp, suffix]
    outfile = os.path.join(outpath,
            '_'.join(filter(None, strlist)) + ext)
    # Get name of currently running script and git SHA for metadata
    import __main__ as main # "main.__file__" names script calling datalog_out
    git_sha = sp.check_output(
            ['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    # Write metadata block
    meta_data = pd.Series([('location: {0}'.format(lname)),
        ('date generated: {0}'.format(str(dt.datetime.now()))),
        ('writer: datalog.iodat.datalog_out'),
        ('writer HEAD SHA: {0}'.format(git_sha)),
        ('called from: {0}'.format(main.__file__)),
        ('-------------------')])
    with open(outfile, 'w') as fout:
        fout.write('---file metadata---\n')
        meta_data.to_csv(fout, index=False)
        df.to_csv(fout, na_rep='NA')

def datalog_in(filename, lname=None):
    """
    Read an datalog delimited text file with a metadata header. If requested
    check line 1 of header to ensure data comes from lname.
    """
    def retpr(line):
        print(line.replace('\n', ""))
        return(str(line))

    print('Opening ' + filename)
    with open(filename) as myfile:
        #[print(next(myfile).replace('\n', "")) for x in range(7)]
        fheader = [retpr(next(myfile)) for x in range(7)]
    
    if (lname is not None) and (
            'location: {0}'.format(lname) not in fheader[1]):
        raise ValueError('File contains data from incorrect logger')
    
    df = pd.read_csv(filename, skiprows=7, parse_dates=True, index_col=0)

    return df
