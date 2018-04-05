"""
Importing this loads configuration data for a datalog project. Configuration
settings come primarily from the 'datalog_config/datalog_conf.yaml' file found
either in the current working directory or its parent

Returns:
    projectname (string): name of the project
    loggers (string list): name for each datalogger associated with project 
    config_path (string): path to configuration file
    defpaths (dict): default data paths specified in datalog_conf.yaml
    userpaths (dict): user defined data paths specified in datalog_conf.yaml
    datapaths (dict): combined dictionary with defpaths and userpaths items,
                      keys refer to the datatype/subdirectory, values are the 
                      full path to that subdirectory abstracted for logger name
                      replacement
    sitedata_file (string): path of a site metadata file with variables for
                      sites where loggers are located.

There are other things this should do:
    Make sure all loggers have config directories
    Maybe check for os and adjust things...
"""

import os
import yaml
import pdb

conf_dir_default = "datalog_config"
project_c_default = "project.yaml"
logger_c_default = "loggers.yaml"
conf_flag = False
import_uplots = False

class tcol:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    UNDERLINE = '\033[4m'

# Get the project configuration path
if os.path.isfile(os.path.join(conf_dir_default, project_c_default)):
    config_path = os.path.join(os.getcwd(), conf_dir_default)
    conf_flag = True
elif os.path.isfile(os.path.join('..', conf_dir_default, project_c_default)):
    config_path = os.path.join(os.path.dirname(os.getcwd()), conf_dir_default)
    conf_flag = True
else:
    import warnings
    warnings.warn(tcol.WARNING + 
            '\ndatalog_config directory not in current'
            ' or parent directory.\nProject configs not found!' + tcol.ENDC)

if conf_flag:
    print('starting datalog...')
    # Load the project yaml file
    yaml_file = os.path.join(config_path, project_c_default)
    print("Load project config: {0}".format(yaml_file))
    stream = open(yaml_file, 'r')
    project_c = yaml.load(stream)

    # Load the loggers yaml file
    yaml_file = os.path.join(config_path, logger_c_default)
    print("Load logger config: {0}".format(yaml_file))
    stream = open(yaml_file, 'r')
    logger_c = yaml.load(stream)

    # Project name
    projectname = project_c['projectname']
    print(tcol.OKGREEN + '\nProject name: ' +
            tcol.ENDC + '{0}'.format(projectname))
    print(tcol.OKGREEN + 'Site configuration files in: ' +
            tcol.ENDC + '\n  {0}'.format(config_path))
    # Project loggers
    loggers = [*logger_c.keys()]
    print(tcol.OKGREEN + '{0} loggers in project:'.format(len(loggers)) +
            tcol.ENDC + '\n  {0}'.format(', '.join(loggers)))

    # Get filename datetime format and regexp strings
    filename_dt_fmt = project_c['filename_dt_fmt']
    filename_dt_rexp = project_c['filename_dt_rexp']

    # Get valid paths from project_c
    # NOTE - If base_path is unset, all other paths must be complete
    base_path = project_c['base_path']

    # Get 5 default paths from yaml config,
    # First clean out None values from the default path dict
    defpaths = {k:v for k,v in project_c['default_data_paths'].items()
            if v is not None}
    # The first 2 are required (key error if missing) and the rest are set
    # to match qa path by default
    defpaths['raw_in'] = os.path.join(base_path, defpaths['raw_in'])
    defpaths['qa'] = os.path.join(base_path, defpaths['qa'])
    defpaths['raw_bak'] = os.path.join(base_path,
            defpaths.get('raw_bak', defpaths['qa']))
    defpaths['raw_std'] = os.path.join(base_path,
            defpaths.get('raw_std', defpaths['qa']))
    defpaths['user'] = os.path.join(base_path,
            defpaths.get('user', defpaths['qa']))
    # Complete the user paths dictionary
    userpaths = {k:v for k,v in project_c['user_subdirs'].items()
            if v is not None}
    for k in userpaths.keys():
        userpaths[k] = os.path.join(defpaths['user'], '{LOGGER}', k, '')
    # Complete the default paths in a new dictionary
    datapaths = {}
    for k in ['raw_in', 'qa', 'raw_bak', 'raw_std']:
        datapaths[k] = os.path.join(defpaths[k], '{LOGGER}', k, '')
    
    # Merge the  default and user path dictionaries
    datapaths.update(userpaths)
    
    # Datalog code path
    datalog_py_path = os.path.join(base_path, project_c['datalog_py'])

    # Site metadata file
    sitedata_file = os.path.join(base_path, project_c['site_metadata'])

    # If the config directory contains a user_plots.py file, set flag to import
    # and append config_path (plots imported by plots module).
    if os.path.isfile(os.path.join(config_path, 'userplots.py')):
        import_uplots=True
        import sys
        sys.path.append(config_path)
    
    # Print available data subdirectories for user:
    datadirs = list(datapaths.keys())
    #print('Each logger has {0} data levels/directories available: \n {1} \n'
    #        'Use <io.get_datadir("loggername", "datalevel")>'
    #        ' to return a path'.format(len(datadirs), ', '.join(datadirs)))
    print(tcol.OKGREEN + 'Each logger has {0} data levels/directories'
            ' available: '.format(len(datadirs)) +
            tcol.ENDC + '\n  {0}\n'.format(', '.join(datadirs)) +
            tcol.OKGREEN + 'Use ' + tcol.ENDC + tcol.UNDERLINE +
            'io.get_datadir("loggername", "datalevel")' +tcol.ENDC +
            tcol.OKGREEN + ' to return a path \n' + tcol.ENDC)
else:
    print(tcol.WARNING + 'Unspecified project, no datalog configs or paths '
    'available' + tcol.ENDC)
    projectname='Unspecified'
    loggers=[]
    config_path=''
    defpaths={}
    userpaths={}
    datapaths={}
    sitedata_file=''
    filename_dt_fmt = ''
    filename_dt_rexp = ''
