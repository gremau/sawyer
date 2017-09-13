import os
import yaml
import pdb

conf_dir_default = "datalog_config"
conf_file_default = "datalog_conf.yaml"
# Get the project configuration path
if os.path.isfile(os.path.join(conf_dir_default, conf_file_default)):
    config_path = os.path.join(os.getcwd(), conf_dir_default)
elif os.path.isfile(os.path.join('..', conf_dir_default, conf_file_default)):
    config_path = os.path.join(os.path.dirname(os.getcwd()), conf_dir_default)
else:
    raise ValueError('Project configuration directory not in current'
            ' or parent directory')

# Load the yaml file
yaml_file = os.path.join(config_path, conf_file_default)
print("Loading datalog configuration file {0}".format(yaml_file))
stream = open(yaml_file, 'r')
projconf = yaml.load(stream)
# Project name
projectname = projconf['projectname']
print('Configuration for project {0}'.format(projectname))
print('Using configuration files in {0}'.format(config_path))

# Get valid paths from configuration
# NOTE - If base_path is unset in conf, all other paths must be complete
base_path = projconf['paths']['base']

#config_path_user = os.path.join(base_path,
#        projconf['paths']['config'])
rawdata_incoming_path = os.path.join(base_path,
        projconf['paths']['rawdata_incoming'])
rawdata_backup_path = os.path.join(base_path,
        projconf['paths']['rawdata_backup'])
qadata_path = os.path.join(base_path,
        projconf['paths']['qadata'])
datalog_py_path = os.path.join(base_path,
        projconf['paths']['datalog_py'])

# Site metadata file
sitedata_file = os.path.join(base_path,
        projconf['files']['sitedata'])

# Get name and subdirectory for datalog data types
datasubdirs = {'rawdata_incoming':'',  
    'rawdata_backup': 'raw_bak/',
    'rawdata_standardized': 'raw_std/',
    'quality_assured': 'qa/'}

datadirs = list(datasubdirs.keys())

print('Each site has {0} data directories available: \n {1} \n'
        'Use "iodat.site_datadir(sitename, datadir=datadir_name)"'
        'to get proper path'.format(len(datadirs), ', '.join(datadirs)))

