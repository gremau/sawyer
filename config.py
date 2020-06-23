"""
Importing this loads configuration data for a sawyer project. Configuration
settings come primarily from the 'sawyer_config' directory found
either in the current working directory or its parent. A different
directory location can be given.

Return a 'conf' object containing:
    projectname (string): name of the project
    loggers (string list): name for each datalogger associated with project 
    spath (string): path to configuration file
    defpaths (dict): default data paths specified in sawyer_conf.yaml
    userpaths (dict): user defined data paths specified in sawyer_conf.yaml
    datapaths (dict): combined dictionary with defpaths and userpaths items,
                      keys refer to the datatype/subdirectory, values are the 
                      full path to that subdirectory abstracted for logger name
                      replacement
    sitedata_file (string): path of a site metadata file with variables for
                      sites where loggers are located.

There are other things this should do:
    Make sure all loggers have config directories
    Maybe check for os type and adjust things...
"""

import os
import warnings
from ruamel_yaml import YAML 
yaml=YAML(typ='safe')
import pdb

# Initialize some default path names
conf_dir_default = "sawyer_config"
project_c_default = "project.yaml"
logger_c_default = "loggers.yaml"

# Class for color terminal output
class tcol:
    """
    Simple class defining terminal colors for sawyer messages
    """
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    UNDERLINE = '\033[4m'


class SawyerConfig(object):
    """
    sawyer configuration class
    """

    def __init__(self, *args):
        self.import_uplots = False
        # Initialize path
        if len(args) == 0:
            print('No path given. Initializing empty sawyer configuration')
            self.spath = None
        else:
            print('Initializing sawyer configuration at path {0}'.format(
                args[0]))
            self.spath = args[0]


    def get_config(self, *args):
        """
        Method to assign the class 'spath' variable and fetch the configuration
        """
        if len(args) > 0:
            print('Fetching sawyer configurations at {0}'.format(args[0]))
            self.spath = args[0]
            self.fetch_config()
        elif self.spath is None:
            print(tcol.WARNING + 'Unspecified path, no sawyer configurations '
                'will be available' + tcol.ENDC)
            print(tcol.WARNING + 'A valid sawyer configuration can be added ' 
                    'with  ' + tcol.UNDERLINE + 'get_config(<path>)' +
                    tcol.ENDC)
            self.projectname='Unspecified'
            self.loggers=[]
            self.logger_c={}
            self.spath=''
            self.defpaths={}
            self.userpaths={}
            self.datapaths={}
            self.sitedata_file=''
            self.filename_dt_fmt = ''
            self.filename_dt_rexp = ''
        else:
            self.fetch_config()
            

    def fetch_config(self):
        """
        Method to fetch configurations from the class 'spath' variable
        """
        spath = self.spath
        try:
            # Load the project yaml file
            yaml_file = os.path.join(spath, project_c_default)
            print("Project configs: {0}".format(yaml_file))
            stream = open(yaml_file, 'r')
            project_c = yaml.load(stream)

            # Load the loggers yaml file
            yaml_file = os.path.join(spath, logger_c_default)
            print("Logger configs: {0}".format(yaml_file))
            stream = open(yaml_file, 'r')
            logger_c = yaml.load(stream)

            # Project name
            projectname = project_c['projectname']
            print(tcol.OKGREEN + '\nProject name: ' +
                    tcol.ENDC + '{0}'.format(projectname))

            # Project loggers
            loggers = [*logger_c.keys()]
            print(tcol.OKGREEN + 
                    '{0} loggers in project:'.format(len(loggers)) +
                    tcol.ENDC + '\n  {0}'.format(', '.join(loggers)))

            # Get filename datetime format and regexp strings
            filename_dt_fmt = project_c['filename_dt_fmt']
            filename_dt_rexp = project_c['filename_dt_rexp']

            # Get valid paths from project_c
            # NOTE - If base_path is unset, all other paths must be complete
            base_path = project_c['base_path']

            # Get default paths to where datalogger tree begins from yaml
            # config,
            # First clean out None values from the default path dict
            defpaths = {k:v for k,v in 
                    project_c['default_data_paths'].items() 
                    if v is not None}
            # 'qa' and 'raw_in' are required (key error if missing) and 
            # the rest are set to match qa path if they are missing
            for k in project_c['default_data_paths'].keys():
                if k=='raw_in' or k=='qa':
                    defpaths[k] = os.path.join(base_path, defpaths[k])
                else:
                    defpaths[k] = os.path.join(base_path, 
                            defpaths.get(k, defpaths['qa']))

            # Complete the user paths dictionary
            userpaths = {}
            for k, v in project_c['user_subdirs'].items():
                if os.path.isdir(str(v)):
                    userpaths[k] = os.path.join(v, '{LOGGER}', k, '')
                else:
                    userpaths[k] = os.path.join(defpaths['qa'],
                            '{LOGGER}', k, '')

            # Complete the default paths in a new dictionary
            datapaths = {}
            for k in defpaths.keys():
                datapaths[k] = os.path.join(defpaths[k], '{LOGGER}', k, '')

            # Merge the  default and user path dictionaries
            datapaths.update(userpaths)

            # Sawyer code path
            sawyer_py_path = os.path.join(base_path,
                    project_c['sawyer_py'])

            # Site metadata file
            sitedata_file = os.path.join(base_path,
                    project_c['site_metadata'])
            
            # If the config directory contains a userplots.py file, set
            # flag to import and append spath (plots imported by
            # plots module).
            if os.path.isfile(os.path.join(spath, 'userplots.py')):
                self.import_uplots=True
                import sys
                sys.path.append(spath)
            
            # Print available data subdirectories for user:
            datadirs = list(datapaths.keys())
            print(tcol.OKGREEN + '{0} data levels/directories available '
                    'per logger: '.format(len(datadirs)) +
                    tcol.ENDC + '\n  {0}\n'.format(', '.join(datadirs)) +
                    tcol.OKGREEN + 'Use ' + tcol.ENDC + tcol.UNDERLINE +
                    'get_datadir("loggername", "datalevel")' +tcol.ENDC +
                    tcol.OKGREEN + ' to return a path \n' + 'Use ' + 
                    tcol.ENDC + tcol.UNDERLINE +
                    'get_latest_df("loggername", "datalevel")' + tcol.ENDC +
                    tcol.OKGREEN + ' to load latest data\n' + tcol.ENDC)

            #Assign all the public variables of the class
            self.projectname = projectname
            self.loggers = loggers
            self.logger_c = logger_c
            self.spath = spath
            self.defpaths = defpaths
            self.userpaths = userpaths
            self.datapaths = datapaths
            self.sawyer_py_path = sawyer_py_path
            self.sitedata_file = sitedata_file
            self.filename_dt_fmt = filename_dt_fmt
            self.filename_dt_rexp = filename_dt_rexp
            
        except:
            # Warn that an invalid sawyer_config path was given
            warnings.warn('This is not a valid sawyer_config directory')

# Get the project configuration path. If `sawyer_config` is in the cwd or its
# parent, set that as the path and set the conf_flag. Otherwise, a basic,
# "unspecified" configuration is loaded.
if os.path.isfile(os.path.join(conf_dir_default, project_c_default)):
    spath = os.path.join(os.getcwd(), conf_dir_default)
    conf = SawyerConfig(spath)
    conf.get_config()
elif os.path.isfile(os.path.join('..', conf_dir_default, project_c_default)):
    spath = os.path.join(os.path.dirname(os.getcwd()), conf_dir_default)
    conf = SawyerConfig(spath)
    conf.get_config()
else:
    warnings.warn('sawyer_config directory is not in '
            'current or parent directory')
    conf = SawyerConfig()
    conf.get_config()
