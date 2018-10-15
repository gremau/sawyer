"""
Tools for gapfilling missing data. 

Gapfill functions that can be applied are called from the gapfunctions module.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from datalog import gapfunctions as gfuncs
import datalog.plots as dpl
import datalog.io as dio
from IPython.core.debugger import set_trace

class GapfillSource:
    """
    Class to make gapfilling data accessible
    """

    def __init__(self, gapconfs):
        """
        Initialize GapfillSource object.
        """
        # Get a list of all sources in the gapfill.yaml file (exclude items
        # without external sources like interp and fillna)
        sourcelist = [gapconfs[k]['sources'].keys() for k in gapconfs.keys()
                if 'sources' in gapconfs[k]]
        sourcelist = [item for sublist in sourcelist for item in sublist]
        self.sourcelist = set(sourcelist)
        
        if not self.sourcelist:
            print('Gapfilling configuration contains no external sources...')
        else:
            # Load dataframes for all external sources into a dictionary
            self.sources = {}
            self.externalsource = True
            for s in self.sourcelist:
                if s in dio.loggers: # Check if datalogger is in this project
                    self.sources[s], _ = dio.get_latest_df(s, 'qa',
                            optmatch='masked')
                else: # Eventually check for other sources...
                    raise ValueError('Source not configured for gapfilling!')

    def get_source_list(self, colnum, gapconf, targetidx):
        """
        Get data from requested source.
        """
        sources = gapconf['sources']
        source_list = []
        source_df = pd.DataFrame(index=targetidx)
        # Multi-source fills send a >1 list of dataframes to gffunc
        if len(sources) > 1:
            # For each source 
            for i, sname in enumerate(sources.keys()):
                sourcecols = sources[sname]
                filldf = self.sources[sname].loc[:,sourcecols[colnum]]
                filldf.name = sname + '_' + filldf.name
                source_list.append(source_df.join(filldf))
        # Single source fills send a one dataframe list to gffunc
        else:
            sname = list(sources.keys())[0]
            sourcecol = sources[sname][colnum]
            filldf = self.sources[sname].loc[:,sourcecol]
            source_list.append(source_df.join(filldf))
        # The source data can be trimmed, which could be useful for linear
        # fits.
        if 'start_fit' in gapconf and 'end_fit' in gapconf:
            stf = gapconf['start_fit']
            if stf is None:
                stf = source_df.index.min()
            enf = gapconf['end_fit']
            if enf is None:
                enf = datetime.now()
            # Get the index range to be trimmed
            idxrange = np.logical_and(source_df.index >= stf,
                    source_df.index <= enf)
            for i, f in enumerate(source_list):
                source_list[i] = source_list[i].loc[idxrange,:]

        return source_list


def get_gffunction(gapconf):
    """
    Get the gapfilling function and arguments
    """
    args = (); kwargs = {}
    if 'gf_function' in gapconf:
        outfunc = getattr(gfuncs, gapconf['gf_function'])
        if 'gf_kwargs' in gapconf and gapconf['gf_kwargs'] is not None:
            kwargs = gapconf['gf_kwargs']
    else:
        outfunc = getattr(gffunctions, 'substitution')

    return [outfunc, kwargs]

def validate_gf_conf(gapconf, gapcolumns):
    # Make a gapconf to validate
    vgapconf = gapconf.copy()
    for c, conf in vgapconf.items():
        conf['filltype'] = 'self'
        # Validate conf key (non-zero)
        assert c not in (0, '0')
        # Check for required keys
        required_keys = ('gf_function', 'gap_cols', 'start_fill', 'end_fill')
        assert all (k in conf for k in required_keys)
        # First - copy gapfilling df column names into conf if requested
        if conf['gap_cols']=='all':
            conf['gap_cols'] = gapcolumns
        # Check if gap_cols could be expanded
        expand_gfcols = not all([c in gapcolumns for c in conf['gap_cols']])
        # External source(s) required to gapfill?
        # Are they present and same length?
        if conf['gf_function'] in gfuncs.require_src:
            assert ('sources' in conf.keys() and len(conf['sources']) > 0)
            sources_columns = [conf['sources'][k]
                    for k in conf['sources'].keys()]
            sourcelen = len(sources_columns[0])
            assert all(len(l) == sourcelen for l in sources_columns)
            # A bunch of stuff to expand or fill in columns for gapfilling
            # For one source fills (same source/column fills all gap_cols)
            if sourcelen==1 and len(conf['gap_cols'])==1 and not expand_gfcols:
                conf['filltype'] = 'one2one'
            elif sourcelen==1 and len(conf['gap_cols'])==1 and expand_gfcols:
                conf['filltype'] = 'one2many'
                test = [any(s in var for s in conf['gap_cols'])
                        for var in gapcolumns] 
                conf['gap_cols'] = gapcolumns[test]
            elif sourcelen==1 and len(conf['gap_cols'])>1 and not expand_gfcols:
                conf['filltype'] = 'one2many'
            elif sourcelen==1 and len(conf['gap_cols'])>1 and expand_gfcols:
                conf['filltype'] = 'one2many'
                test = [any(s in var for s in conf['gap_cols'])
                        for var in gapcolumns]
                conf['gap_cols'] = gapcolumns[test]
            # For many-source fills, gap_cols must be same length
            elif (sourcelen > 1 and sourcelen==len(conf['gap_cols']) and 
                    not expand_gfcols):
                conf['filltype'] = 'many2many'
            elif (sourcelen > 1 and sourcelen!=len(conf['gap_cols']) and 
                    not expand_gfcols):
                raise ValueError('The number of source and gapfill columns in '
                    'the configuration file do not match')
            elif (sourcelen > 1 and sourcelen==len(conf['gap_cols']) and 
                    expand_gfcols):
                raise ValueError('Some of the gapfill columns are incorrect in '
                    'the configuration file.')
            else:
                raise ValueError('Unspecified error')
        # If no sources required, just expand gap_cols if needed
        else:
            test = [any(s in var for s in conf['gap_cols'])
                    for var in gapcolumns]
            conf['gap_cols'] = gapcolumns[test]
        # Copy modified configuration into vgaconf
        vgapconf[c] = conf
    return vgapconf

def apply_gapfilling(df_in, gapconf, plot=False):
    """
    Apply gapfilling to a dataframe. The incoming dataframe (df) is copied
    and gaps are filled according to the function and parameters in gapconf.
    
    These changes are recorded in the logical array (df_isfilled)

    Args:
        df      : input dataframe (a qa_masked dataframe for a logger)
        gapconf : dict from the logger's gapfill.yaml in datalog_config
        plot    : if True, make diagnostic plots for gapfilled column in df 
    Returns:
        Three pandas dataframes with identical dimensions to the input df
        df_new  : dataframe with any gaps filled using methods in gapconf
        df_isfilled : logical dataframe indicating filling (True = filled)
    """
    # Make a copy to be a gapfilled dataframe and a boolean array
    df = df_in.copy()
    df_isfilled = pd.DataFrame(False, index=df.index, columns=df.columns)
    # Get gapfilling sources object
    gfsource = GapfillSource(gapconf)
    # Loop through gapconf
    for k, conf in gapconf.items():        
        # Get the start and end fill dates
        st = conf['start_fill']
        if st is None:
            st = df.index.min()
        en = conf['end_fill']
        if en is None:
            en = datetime.now()
        # Get the index range to be filled
        fillidx = np.logical_and(df.index >= st, df.index <= en)

        # Get the gapfilling function and arguments
        gffunc, gf_kwargs = get_gffunction(conf)
        print('Fill gap {0}, using {1}.'.format(k, gffunc))

        # Now loop through    
        for c, col in enumerate(conf['gap_cols']):
            print('Fill column {0}'.format(col))
            gf_sources = []
            to_fill = df[col]
            # Source data must be sent to gffunc, and it must be adjusted
            # by methods in the gfsource depending on filltype
            if conf['filltype'] == 'one2one' or conf['filltype'] == 'one2many':
                gf_sources = gfsource.get_source_list(0, conf, to_fill.index)
            elif conf['filltype'] == 'many2many':
                gf_sources = gfsource.get_source_list(c, conf, to_fill.index)
            
            # Run the gapfilling function
            df[col], gf_bool = gffunc(to_fill, fillidx, *gf_sources,
                    **gf_kwargs)
            df_isfilled[col] = np.logical_or(gf_bool, df_isfilled[col])

        # Plot if requested
            if plot:
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(1,1)
                dpl.gf_var_tsplot(ax, col, df_in, df)
                plt.show()

    # Rewrite df_flag column names
    df_isfilled.columns = df_isfilled.columns + '_f'

    return df, df_isfilled

def fill_logger(lname, plot=False):
    """
    Get a gapfilled dataframe for the given logger and a boolean dataframe
    indicating what data is filled.

    Args:
        lname (string): datalogger name
        plot (bool): if set, make a plot of the gapfilling
    Returns:
        df_gf       : gapfilled dataframe
        df_isfilled : boolean dataframe indicating what values are filled
        filedate     : datetime object indicating last date of data collection
    """

    # Get most recent qa masked data file for logger
    df, filedate = dio.get_latest_df(lname, 'qa', optmatch='masked')
    # Get gapfilling configuration
    gapconf = dio.read_yaml_conf(lname, 'gapfill')
    # Validate gapconf
    gapconfv = validate_gf_conf(gapconf, df.columns)

    # Fill gaps
    df_gf, df_isfilled = apply_gapfilling(df, gapconfv, plot=plot)
    
    return df_gf, df_isfilled, filedate
