"""
Importing this loads configuration data for a datalog project. Configuration
settings come primarily from the 'datalog_config/datalog_conf.yaml' file found
either in the current working directory or its parent

Returns:
    projectname (string): name of the project
    projectsites (string list): name for each site associated with project 
    config_path (string): path to configuration file
    defpaths (dict): default data paths specified in datalog_conf.yaml
    userpaths (dict): user defined data paths specified in datalog_conf.yaml
    datapaths (dict): combined dictionary with defpaths and userpaths items,
                      keys refer to the datatype/subdirectory, values are the 
                      full path to that subdirectory abstracted for site name
                      replacement
    sitedata_file (string): path of a site metadata file with variables for
                      each site in the project.

There are other things this should do:
    Make sure all sites have config directories
    Maybe check for os and adjust things...
"""

import os
import yaml
import pdb

conf_dir_default = "datalog_config"
conf_file_default = "datalog_conf.yaml"
conf_flag = False

# Get the project configuration path
if os.path.isfile(os.path.join(conf_dir_default, conf_file_default)):
    config_path = os.path.join(os.getcwd(), conf_dir_default)
    conf_flag = True
elif os.path.isfile(os.path.join('..', conf_dir_default, conf_file_default)):
    config_path = os.path.join(os.path.dirname(os.getcwd()), conf_dir_default)
    conf_flag = True
else:
    import warnings
    warnings.warn('Warning: Project configuration directory not in current'
            ' or parent directory. Project configs not found!')

if conf_flag:
    # Load the yaml file
    yaml_file = os.path.join(config_path, conf_file_default)
    print("Load datalog config: {0}".format(yaml_file))
    stream = open(yaml_file, 'r')
    conf = yaml.load(stream)

    # Project name
    projectname = conf['projectname']
    print('Project name: {0}'.format(projectname))
    print('Site configuration files in {0}'.format(config_path))
    # Project sites
    projectsites = conf['projectsites']
    print('{0} sites in project: \n {1}'.format(
        len(projectsites), ', '.join(projectsites)))

    # Get valid paths from configuration
    # NOTE - If base_path is unset in conf, all other paths must be complete
    base_path = conf['base_path']

    # Get 5 default paths from yaml config,
    # First clean out None values from the default path dict
    defpaths = {k:v for k,v in conf['default_data_paths'].items()
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
    userpaths = {k:v for k,v in conf['user_subdirs'].items() if v is not None}
    for k in userpaths.keys():
        userpaths[k] = os.path.join(defpaths['user'], '{SITE}', k, '')
    # Complete the default paths in a new dictionary
    datapaths = {}
    for k in ['raw_in', 'qa', 'raw_bak', 'raw_std']:
        datapaths[k] = os.path.join(defpaths[k], '{SITE}', k, '')
    
    # Merge the  default and user path dictionaries
    datapaths.update(userpaths)
    
    # Datalog code path
    datalog_py_path = os.path.join(base_path, conf['datalog_py'])

    # Site metadata file
    sitedata_file = os.path.join(base_path, conf['site_metadata'])
    
    # Print available data subdirectories for user:
    datadirs = list(datapaths.keys())
    print('Each site has {0} data directories available: \n {1} \n'
            'Use "iodat.site_datadir(sitename, datadir=datadir_name)"'
            ' to get proper path'.format(len(datadirs), ', '.join(datadirs)))

else:
    print('Project configs not loaded!')
    projectname='Unspecified'
    projectsites=[]
    config_path=''
    defpaths={}
    userpaths={}
    datapaths={}
    sitedata_file=''
