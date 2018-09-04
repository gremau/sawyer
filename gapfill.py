"""
Tools for gapfilling missing data. 

Gapfill functions that can be applied are called from the gapfunctions module.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from datalog import gapfunctions
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
        # without an external source)
        sourcelist = [gapconfs[k]['source'] for k in gapconfs.keys()
                if 'source' in gapconfs[k]]
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

    def get_source_df(self, colnum, gapconf, targetidx):
        """
        Get data from requested source.
        """
        sourcenames = gapconf['source']
        sourcecol = gapconf['source_cols'][colnum]
        source_df = pd.DataFrame(index=targetidx)
        # Multi-source fills send a >1 column dataframe to gffunc
        if len(sourcenames) > 1:
            # For multi-source fills, loop through the sources and join
            # to source_df. Currently this should only apply to midpoint
            # and THERE SHOULD PROBLY BE A CHECK FOR THAT
            # Get colname from second source_cols list (must be same size)
            sourcecol = [sourcecol]
            sourcecol.append(gapconf['source_cols_2'][colnum])
            for i, sname in enumerate(sourcenames):
                filldf = self.sources[sname].loc[:,sourcecol[i]]
                filldf.name = sname + '_' + filldf.name
                source_df = source_df.join(filldf)
        # Single source fills
        else:
            filldf = self.sources[sourcenames[0]].loc[:,sourcecol]
            source_df = source_df.join(filldf)
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
        return source_df.loc[idxrange, :]


def get_gffunction(gapconf):
    """
    Get the gapfilling function and arguments
    """
    args = (); kwargs = {}
    if 'gf_function' in gapconf:
        outfunc = getattr(gffunctions, gapconf['gf_function'])
        if 'gf_args' in gapconf:
            args = gapconf['gf_args']
        if 'gf_kwargs' in gapconf:
            kwargs = gapconf['gf_kwargs']
    else:
        outfunc = getattr(gffunctions, 'substitution')

    return [outfunc, args, kwargs]

def apply_gapfilling(df, gapconf, plot=False):
    """
    Apply gapfilling to a dataframe. The incoming dataframe (df) is copied
    and gaps are filled according to the function and parameters in gapconf.
    
    These changes are recorded in the logical array (df_isfilled)

    Args:
        df      : input dataframe
        gapconf : gapfill dictionary from the appropriate datalog configuration
    Returns:
        Three pandas dataframes with identical dimensions to the input df
        df_new  : dataframe with any gaps filled using methods in gapconf
        df_isfilled : logical dataframe indicating filling (True = filled)
    """
    # Make a copy to be a gapfilled dataframe and a boolean array
    df_new = df.copy()
    df_isfilled = pd.DataFrame(False, index=df.index, columns=df.columns)
    # Get gapfilling sources
    gfsource = GapfillSource(gapconf)
    # Loop through gapconf
    for k, conf in gapconf.items():
        getsource=False
        if k in (0, '0'):
            raise ValueError('Gapfill key cannot be zero (0)!')
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
        gffunc, gf_args, gf_kwargs = get_gffunction(conf)
        print('Fill gap {0}, using {1}.'.format(k, gffunc))

        if conf['gap_cols']=='all':
            # If "all" columns to be flagged select all
            colrange = df.columns
        elif gfsource.externalsource and 'source_cols' in conf:
            # If calling an external source...
            if len(conf['source_cols'])==len(conf['gap_cols']):
                getsource=True
                # leave gap_cols as is:
                colrange = conf['gap_cols']
            else:
                raise ValueError('gap_cols and source_cols must be same' +
                'length for external source gapfilling')
        else:
            # Or find dataframe columns matching those in gapconf
            test = [any(s in var for s in conf['gap_cols'])
                    for var in df.columns] 
            colrange = df.columns[test]
        # Now loop thorugh    
        for c, col in enumerate(colrange):
            print('Fill column {0}'.format(col))
            to_fill = df_new[col]
            source_df = None
            if getsource:
                # Source data must be sent to gffunc, and it must be adjusted
                # first by methods in the gfsource
                source_df = gfsource.get_source_df(c, conf, df.index)
            # Run the gapfilling function    
            df_new[col], gf_bool = gffunc(to_fill, source_df, fillidx,
                    *gf_args, **gf_kwargs)
            df_isfilled[col] = np.logical_or(gf_bool, df_isfilled[col])

        # Plot if requested
            if plot:
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(1,1)
                dpl.gf_var_tsplot(ax, col, df, df_new)
                plt.show()

    # Rewrite df_flag column names
    df_isfilled.columns = df_isfilled.columns + '_f'

    return df_new, df_isfilled

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

    # Get most recent raw_std data and merge logger and global flags
    df, filedate = dio.get_latest_df(lname, 'qa', optmatch='masked')
    # Get gapfilling configuration
    gapconf = dio.read_yaml_conf(lname, 'gapfill')
    # Fill gaps
    df_gf, df_isfilled = apply_gapfilling(df, gapconf, plot=plot)
    
    return df_gf, df_isfilled, filedate
