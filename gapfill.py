"""
Functions for flagging and masking data. 

QA functions that can be applied are called from the qafunctions module.

"""

import pandas as pd
import numpy as np
from datetime import datetime
from datalog import gffunctions
import datalog.plots as dpl
import datalog.io as dio
import pdb

class GapfillSource:
    """
    Class to make gapfilling data accessible
    """

    def __init__(self, gapconfs):
        sourcelist = [gapconfs[k]['source'] for k in gapconfs.keys()]
        sourcelist = [item for sublist in sourcelist for item in sublist]
        self.sourcelist = set(sourcelist)
        self.sources = {}
        for s in self.sourcelist:
            if s in dio.loggers:
                self.sources[s], _ = dio.get_latest_df(s,
                        'qa', optmatch='masked')
            else:
                print

    def get_source_df(self, colnum, gapconf, targetidx):
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
    if 'gf_function' in gapconf:
        outfunc = getattr(gffunctions, gapconf['gf_function'])
        if 'gf_args' in gapconf:
            outargs = gapconf['gf_args']
        else:
            outargs = ''
    else:
        outfunc = getattr(gffunctions, 'substitution')
        outargs = ''
    return [outfunc, outargs]

def apply_gapfilling(df, gapconf, plot=False):
    """
    Apply gapfilling to a dataframe. There are two types of operations that can
    be performed on the input dataframe, depending on the gapfilling
    configuratioin:

    1. Transform data values based on qa flag input
    2. Mask data based on qa flag input
    
    These changes are logged in the flag array (df_flag) with a number
    corresponding to the qa flag in the site configuration files.

    Args:
        df      : input dataframe
        gapconf   : qa_flag dictionary from the site's datalog configuration dir
    Returns:
        Three pandas dataframes with identical dimensions to the input df
        df_new  : original data with any qa transformations applied
        df_mask : Mask dataframe containing boolean values (True = remove)
        df_flag : Flag dataframe with values corresponding to qa flags

    TODO - may want to add a flag for data already missing
    """
    # Make a copy to be a gapfilled dataframe, a boolean array,
    # and a flag dataframe
    df_new = df.copy()
    df_isfilled = pd.DataFrame(False, index=df.index, columns=df.columns)
    # Get gapfilling sources
    gfsource = GapfillSource(gapconf)
    # Loop through gapconf
    for k, conf in gapconf.items():
        if k in (0, '0'):
            raise ValueError('Gapfill key cannot be zero (0)!')
        
        st = conf['start_fill']
        if st is None:
            st = df.index.min()
        en = conf['end_fill']
        if en is None:
            en = datetime.now()
        # Get the gapfilling function and arguments
        gffunc, gfargs = get_gffunction(conf)
        print('Fill gap {0}, using {1}.'.format(k, gffunc))

        if conf['gap_cols']=='all':
            # If "all" columns to be flagged select all
            colrange = df.columns
        else:
            # Or find dataframe columns matching those in gapconf
            test = [any(s in var for s in conf['gap_cols'])
                    for var in df.columns] 
            colrange = df.columns[test]
        # Get the index range to be filled
        fillidx = np.logical_and(df.index >= st, df.index <= en)
        # Note: conf['to_cols'] and conf['from_cols'] must be the same length
        # might want to put in a check on this
        for c, col in enumerate(conf['gap_cols']):
            print('Fill column {0}'.format(col))
            to_fill = df_new[col]
            # Source data must be sent to gffunc, and it must be adjusted first
            # by methods in the gfsource
            source_df = gfsource.get_source_df(c, conf, df.index)
            df_new[col], gf_bool = gffunc(to_fill, source_df, fillidx, *gfargs)
            df_isfilled[col] = np.logical_or(gf_bool, df_isfilled[col])

        # Plot if requested
        if plot:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1,1)
            dpl.gf_var_tsplot(ax, conf['gap_cols'], df, df_new)
            plt.show()

    # Rewrite df_flag column names
    df_isfilled.columns = df_isfilled.columns + '_f'
    return df_new, df_isfilled # df_new[df_mask]=np.nan will apply mask

def fill_dataframe(df, gapconf, plot=False):
    """
    Get qa dataframes with gapconf appended and values masked

    Args:
        df: input dataframe
        gapconf: gapfill dictionary from the site's datalog configuration dir
    Returns:
        df_gf       : QA'd dataframe with gapconf appended
        df_gf_masked: QA'd dataframe with gapconf appended and mask applied
    """
    df_gf, df_isfilled = apply_gapfilling(df, gapconf, plot=plot)
    #df_qa_fl = pd.concat([df_qa, df_flag], axis=1)
    #df_qa_masked = df_qa.copy()
    #df_qa_masked[df_mask] = np.nan
    return df_gf, df_isfilled 
