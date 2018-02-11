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
import datalog.config as conf
import pdb

conf_path = conf.config_path
qa_path = conf.qadata_path
raw_incoming_path = conf.rawdata_incoming_path
raw_backup_path = conf.rawdata_backup_path

datadirs = conf.datadirs
datasubdirs = conf.datasubdirs

def site_datadir(sitename, datadir='quality_assured'):
    """
    """
    if datadir in datadirs:
        if datadir=='rawdata_incoming':
            path = os.path.join(raw_incoming_path, sitename)
        elif datadir=='rawdata_backup':
            path = os.path.join(raw_backup_path, sitename, datasubdirs[datadir])
        else:
            path = os.path.join(qa_path, sitename, datasubdirs[datadir])
    else:
        raise ValueError('Available data directories are {0}'.format(datadirs))
    return path


def get_file_collection(sitename, datapath, ext='.dat', optmatch=None):
    """
    Read a list of filenames from a data directory, match against desired site,
    and return the list and the file datestamps of each file. This function
    expects to find a directory full of files with the format 
    "prefix_<sitename>_<Y>_<m>_<d>_<H>_<M>_optionalsuffix.dat". For example:

    MNPclimoseq_Creosote_2017_03_17_11_55_00.dat

    Only returns filenames matching the sitename and extension (.dat by 
    default) strings.

    If a list of strings in optmatch is given, additional strings can be
    matched
    """
    # Get a list of filenames in provided data directory
    files = os.listdir(datapath)
    # Select desired filenames from the list (by site)
    # This could easily fail if other parts of filename contain the 
    # site or extension name
    site_files = [f for f in files if sitename in f and ext in f ]
    # Match optional strings if given
    if isinstance(optmatch, str): # optmatch must be a list
        optmatch = [optmatch]
    if optmatch is not None:
        for m in optmatch:
            site_files = [f for f in files if m in f]
    
    # Get file date for each file. The file datestamp is in the 
    # filename with fields delimited by '_'
    file_dt = []
    for i in site_files:
        tokens = i.split('_')
        file_dt.append(dt.datetime.strptime('-'.join(tokens[-6:-1]),
            '%Y-%m-%d-%H-%M'))
    return site_files, file_dt


def most_recent_filematch(sitename, datapath, ext='.dat', optmatch=None):
    """
    Return the most recent file in a directory matching the given site and
    extension. Other optional matching strings can be supplied
    """
    files, dates = get_file_collection(sitename, datapath, ext=ext,
            optmatch=optmatch)
    return files[dates.index(max(dates))], max(dates)
    

def read_project_conf(confdir=conf_path):
    """
    Read the project YAML configuration file from the datalog
    configuration directory.

    Args:
        confdir (string): directory to look for YAML configuration files

    Returns:
        yamlf (dict): Returns a dictionary of configuration values
                      from the YAML file
    """
    yamlfile = os.path.join(confdir, 'datalog_conf.yaml')
    stream = open(yamlfile, 'r')
    yamlf = yaml.load(stream)
    return yamlf


def read_yaml_conf(sitename, yamltype, confdir=conf_path):
    """
    Read a specified YAML configuration file from a given site's datalog
    configuration directory. Checks the YAML file meta dictionary to ensure
    configuration is for the correct site and type.

    Args:
        sitename (string): site identifier
        yamltype (string): identifies the YAML filename and configuration type
        confdir (string): directory to look for YAML configuration files

    Returns:
        yamlf (dict): Returns the "items" dictionary of configuration values
                      from the YAML file

    Raises:
        ValueError: Raises ValueError if the sitename or yamltype parameters
                    do not match those found in the yaml file
    """
    yamlfile = os.path.join(confdir, sitename, yamltype + '.yaml')
    if os.path.isfile(yamlfile):
        stream = open(yamlfile, 'r')
        yamlf = yaml.load(stream)
        ysite = yamlf['meta']['site']==sitename
        ytype = yamlf['meta']['conftype']==yamltype
        if not(ysite) or not(ytype):
            raise ValueError('YAML file site/type mismatch.')
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


def load_toa5(fpathname, reindex=False) :
    """
    Load a specified TOA5 datalogger file (a Campbell standard output format)
    and return a pandas DataFrame object. DataFrame has a datetime index and
    user is warned if any measurement periods appear to be missing. Dataframe
    can be reindexed to fill in missing periods with NAN.

    Args:
        fpathname (str) : path and filename of desired AF file
        efreq (str)     : expected frequency of data file, used to reindex
    Return:
        parsed_df   : pandas DataFrame    
    """

    print('Parsing ' + fpathname)

    # Parse using Campbell timestamp
    parsed_df = pd.read_csv(fpathname, skiprows=( 0,2,3 ), header=0,
            parse_dates = { 'Date': [0]}, index_col='Date',
            na_values=['NaN', 'NAN', 'INF', '-INF'])
    
    cfreq = calculate_freq(parsed_df.index)
    # Create an index that includes every period between the first and
    # last datetimes in the file
    startd = parsed_df.index.min()
    endd = parsed_df.index.max()
    fullidx = pd.date_range( startd, endd, freq=cfreq)
    # Warn if observations are missing
    if len( parsed_df.index ) < len( fullidx ):
        print("WARNING: index frequency is less than expected!")
        print("Reindexing will introduce NaN values")
    elif len( parsed_df.index ) > len( fullidx ):
        print("WARNING: index frequency is greater than expected!")
        print("Reindexing may remove valid values")
    if reindex:
        print("Reindexing dataframe...")
        parsed_df_ret =  parsed_df.reindex(fullidx)
    else:
        parsed_df_ret = parsed_df
    return parsed_df_ret


def site_raw_concat(sitename, datapath, setfreq='10min', ext='.dat',
        optmatch=None, iofunc=load_toa5):
    """
    Load a list of raw datalogger files, append them, and then return a pandas
    DataFrame object. Also returns a list of file datestamps. 

    Note that files don't load in chronological order, so the resulting 
    dataframe is reindexed based on the min/max dates in the indices. This 
    will fill in any missing values with NAN.
    
    Warns if observations are missing. Fails if indices of concatenated files
    have different frequencies.
    
    Args:
        sitename: Site name
        datapath: Path to directory of data files
        iofunc  : function used to load each file
    Returns:
        sitedf  : pandas DataFrame containing concatenated raw data
                      from one site
        file_dt : list of datetime objects parsed from the filenames 
                      (file datestamp)
    """
            
    # Get list of datalogger filenames and file datestamps from directory
    files, file_dt = get_file_collection(sitename, datapath, ext=ext,
            optmatch=optmatch)
    # Initialize DataFrame
    sitedf = pd.DataFrame()
    # Loop through each year and fill the dataframe
    for i in files:
        # Call load_toa5_file
        filedf = iofunc(os.path.join(datapath , i))
        # And append to site_df, 'verify_integrity' warns if there are
        # duplicate indices
        sitedf = sitedf.append(filedf, verify_integrity=True)
    # Calculate frequency
    cfreq = calculate_freq(sitedf.index)
    # Create index spanning all days from min to max date
    fullidx = pd.date_range(sitedf.index.min(), sitedf.index.max(),
            freq = setfreq)
    # Warn if observations are missing
    if len( sitedf.index ) < len( fullidx ):
        print("WARNING: index frequency is less than expected!")
        print("Reindexing will introduce NaN values")
    elif len( sitedf.index ) > len( fullidx ):
        print("WARNING: index frequency is greater than expected!")
        print("Reindexing may remove valid values")
    # Now reindex the dataframe
    print("Reindexing dataframe...")
    sitedf = sitedf.reindex( fullidx )
    return sitedf, file_dt


def rename_raw_variables(sitename, rawpath, rnpath, confdir=conf_path):
    """
    Rename raw datalogger variables according to YAML configuration file

    Args:
        sitename (string): site identifier
        rawpath (string): raw datalogger file path
        rnpath (string): path to write renamed data files
        confdir (string): directory to look for YAML configuration files

    Returns:
        Does not return anything but writes new files in rnpath
    """
    import re
    
    # Get var_rename configuration file for site
    yamlf = read_yaml_conf(sitename, 'var_rename', confdir=confdir)
    # Get list of filenames and their file datestamps from the raw directory
    files, file_dt = get_file_collection(sitename, rawpath)
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
            sitename))
        for filename in files:
            shutil.copy(os.path.join(rawpath, filename), rnpath)


def datalog_out(df, sitename, outpath, datestamp=None,
        prefix=None, suffix='00'):
    """
    Write a delimited text file with a metadata header.
    """
    # Remove any underscores in suffix
    suffix = suffix.replace("_", "")

    if datestamp is not None:
        datestamp = datestamp.strftime('%Y_%m_%d_%H_%M')
    # Put together the output file name
    strlist = [prefix, sitename, datestamp, suffix]
    outfile = os.path.join(outpath,
            '_'.join(filter(None, strlist)) + '.txt')
    # Get name of currently running script and git SHA for metadata
    import __main__ as main # "main.__file__" names script calling datalog_out
    git_sha = sp.check_output(
            ['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    # Write metadata block
    meta_data = pd.Series([('location: {0}'.format(sitename)),
        ('date generated: {0}'.format(str(dt.datetime.now()))),
        ('writer: datalog.iodat.datalog_out'),
        ('writer HEAD SHA: {0}'.format(git_sha)),
        ('called from: {0}'.format(main.__file__)),
        ('-------------------')])
    with open(outfile, 'w') as fout:
        fout.write('---file metadata---\n')
        meta_data.to_csv(fout, index=False)
        df.to_csv(fout, na_rep='NA')

def datalog_in(filename, sitename=None):
    """
    Read an datalog delimited text file with a metadata header.
    """
    print('Opening ' + filename)
    with open(filename) as myfile:
        [print(next(myfile).replace('\n', "")) for x in range(7)]

    df = pd.read_csv(filename, skiprows=7, parse_dates=True, index_col=0)
    return df
