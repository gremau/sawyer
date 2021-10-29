""" 
Functions for loading various environmental monitoring data files

Greg Maurer
"""

import numpy as np
import datetime as dt
import pandas as pd
import subprocess as sp
from ruamel.yaml import YAML 
yaml=YAML(typ='safe')
import os
import shutil
import re
import sawyer.config as sy
from IPython.core.debugger import set_trace

def get_config(path):
    """
    Access the get_config method to change SawyerConfig configs from
    this namespace
    """
    sy.conf.get_config(path)

def validate_logger(lname):
    """
    Make sure the datalogger name (lname) is a valid datalogger in the current
    configuration.

    Raises:
        ValueError
    """
    if lname in sy.conf.loggers:
        pass
    else:
        print('Available logger names are {0}'.format(sy.conf.loggers))
        raise ValueError('Not a valid datalogger name for this configuration')

def get_datadir(lname, datalevel='qa'):
    """
    Retrieve correct directory path for given logger and data level

    Args:
        lname (string): name of logger
        datalevel (string): name of desired data level (each has a directory)

    Returns:
        p (string): a validated path name
        
    """
    # Validate logger name, then find or create correct data directory
    validate_logger(lname)
    if datalevel in sy.conf.datapaths.keys():
        p = sy.conf.datapaths[datalevel].replace('{LOGGER}', lname)
        try:
            os.makedirs(p)
            print('New directory created: ' + p)
        except FileExistsError:
            # directory already exists
            pass
    else:
        raise ValueError('Available data levels/directories are {0}'.format(
            sy.conf.datapaths.keys()))
    return p

def dt_from_filename(filename, rexp=None, fmt=None):
    """
    Retrieve a datatime object from a given filename in sawyer format

    (\d{4}){1}([_-]\d{2}){5}
    """
    if rexp is None:
        rexp = sy.conf.filename_dt_rexp
    if fmt is None:
        fmt = sy.conf.filename_dt_fmt
    # Regexp search
    srchresult = re.search(rexp, filename)
    if srchresult is None:
        return None
    else:
        dtstr = srchresult.group(0)
        # Some files may be missing seconds - parse date anyway
        try:
            dtobj = dt.datetime.strptime(dtstr, fmt)
        except:
            dtobj = dt.datetime.strptime(dtstr, fmt[:-3])
        return dtobj

def get_file_list(datapath, optmatch=None, parsedt=False, fullpath=True):
    """
    Return a list of filenames and datestamps (optional) for a given 
    data directory. of each file. If datestamp parsing is requested, the
    function expects to find files that have a date/time timestamp that can
    be parsed with dt_from_filename() using the project default formats.

    Only returns filenames matching the optmatch strings, if given.

    Args:
        datapath (string): a full path to a directory of data files
        optmatch (string): optional string to match in filenames
        parsedt (bool): parse timestamp in filename (False by default)
        fullpath (bool): return full path. If False only filenames are returned
    Returns:
        files: list of file names/paths
        file_dt: list of datetime objects corresponding to items in files
                 (optional)
    """
    # Get a list of filenames in provided data directory
    filelist =  os.listdir(datapath) 
    # Match optional strings if given
    if isinstance(optmatch, str): # optmatch must be a list
        optmatch = [optmatch]
    if optmatch is not None:
        for m in optmatch:
            filelist = [f for f in filelist if m in f]
    # Create full path if requested
    if fullpath:
        files = [os.path.join(datapath, f) for f in filelist]
    else:
        files = filelist
    # Parse dates if requested. Format specified in project configuration.
    if parsedt:
        return files, [dt_from_filename(f) for f in filelist]
    else:
        return files


def get_latest_file(datapath, optmatch=None, fullpath=True):
    """
    Return name of most recent file in a directory with optional pattern
    matching.
    """
    files, fdates = get_file_list(datapath, optmatch=optmatch,
            parsedt=True, fullpath=fullpath)
    return files[fdates.index(max(fdates))], max(fdates)

    
def get_latest_df(lname, datalevel, optmatch=None):
    """
    Load the most recent file in a directory and return as pandas dataframe
    (with optional pattern matching)
    """
    p = get_datadir(lname, datalevel)

    if 'raw' in datalevel:
        raw_freq = sy.conf.logger_c[lname]['rawfreq']
        fs, f_dt = get_file_list(p, optmatch=optmatch, parsedt=True)
        df = concat_raw_files(fs, optmatch=optmatch, iofunc=load_toa5,
                reindex=raw_freq)
    else:
        f, f_dt = get_latest_file(p, optmatch)
        df = sawyer_in(os.path.join(p, f), lname=lname)
    
    return df, f_dt


#def read_project_conf(confdir=sy.conf.spath):
#    """
#    Read the project YAML configuration file from the sawyer
#    configuration directory.
#
#    Args:
#        confdir (string): directory to look for YAML configuration files
#
#    Returns:
#        yamlf (dict): Returns a dictionary of configuration values
#                      from the YAML file
#    """
#    yamlfile = os.path.join(confdir, 'sawyer_conf.yaml')
#    stream = open(yamlfile, 'r')
#    yamlf = yaml.load(stream)
#    return yamlf


def read_yaml_conf(lname, yamltype, confdir=None):
    """
    Read a specified YAML configuration file from a given logger's sawyer
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
    if confdir is None:
        confdir = sy.conf.spath
    if lname is 'all':
        yamlfile = os.path.join(confdir, yamltype + '.yaml')
    else:
        validate_logger(lname)
        yamlfile = os.path.join(confdir, lname, yamltype + '.yaml')
    if os.path.isfile(yamlfile):
        stream = open(yamlfile, 'r')
        yamlf = yaml.load(stream)
        ylogger = yamlf['meta']['logger']==lname
        ytype = yamlf['meta']['conftype']==yamltype
        if not(ylogger) or not(ytype):
            raise ValueError('YAML file logger/type mismatch.')
        else:
            if yamlf['items'] is not None:
                return yamlf['items']
            else:
                return {}
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


def load_toa5(fdatapath, **kwargs) :
    """
    Load a specified TOA5 datalogger file (a Campbell standard output format)
    and return a pandas DataFrame object. DataFrame has a datetime index
    and can be reindexed to fill in missing periods with NAN (reindex_to()).

    Args:
        fdatapath (str) : path and filename of desired TOA5 file
    Return:
        parsed_df   : pandas DataFrame containing file data 
    """

    print('Parsing ' + fdatapath)
    
    skip=[0,2,3]
    if 'skiprows' in kwargs:
        skip = skip + kwargs.pop('skiprows')

    # Parse using Campbell timestamp
    parsed_df = pd.read_csv(fdatapath, skiprows=skip, header=0,
            parse_dates = { 'Date': [0]}, index_col='Date',
            na_values=['NaN', 'NAN', 'INF', '-INF'], **kwargs)
    
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
    # files, files_dt = get_file_list(datapath, optmatch=optmatch)
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


def rename_raw_variables(lname, rawpath, rnpath, confdir=None):
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
    if confdir is None:
        confdir = sy.conf.spath

    # Get var_rename configuration file for logger
    yamlf = read_yaml_conf(lname, 'var_rename', confdir=confdir)
    # Get list of filenames and their file datestamps from the raw directory
    files, file_dt = get_file_list(rawpath, parsedt=True, fullpath=False)
    if bool(yamlf):
        # For each file, loop through each rename event and change headers
        for i, filename in enumerate(files):
            print(' Renaming headers for: ' + filename)
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


def sawyer_out(df, lname, outpath, datestamp=None,
        prefix=None, suffix='00', ext='.txt'):
    """
    Write a delimited text file with a metadata header.
    """
    # Remove any underscores in suffix
    suffix = suffix.replace("_", "")

    if datestamp is not None:
        datestamp = datestamp.strftime(sy.conf.filename_dt_fmt)
    # Put together the output file name
    strlist = [prefix, lname, datestamp, suffix]
    outfile = os.path.join(outpath,
            '_'.join(filter(None, strlist)) + ext)
    # Get name of currently running script and git SHA for metadata
    import __main__ as main # "main.__file__" names script calling sawyer_out
    try:
        scriptname = main.__file__
    except AttributeError:
        scriptname = 'interactive'
    git_sha = sp.check_output(
            ['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    # Write metadata block
    meta_data = pd.Series([('location: {0}'.format(lname)),
        ('date generated: {0}'.format(str(dt.datetime.now()))),
        ('writer: sawyer.io.sawyer_out'),
        ('writer HEAD SHA: {0}'.format(git_sha)),
        ('called from: {0}'.format(scriptname)),
        ('-------------------')])
    with open(outfile, 'w') as fout:
        fout.write('---file metadata---\n')
    #fout.close()
        meta_data.to_csv(fout, mode='a', index=False, header=False)
        df.to_csv(fout, mode='a', na_rep='NA')

def sawyer_in(filename, lname=None):
    """
    Read an sawyer delimited text file with a metadata header. If requested
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
