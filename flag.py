"""
Functions for flagging and masking data. 

QA functions that can be applied are called from the qafunctions module.

"""

import pandas as pd
import numpy as np
from datetime import datetime
from datalog import qafunctions
import datalog.io as dio
from IPython.core.debugger import set_trace

def get_qafunction(flag):
    """
    Get the qa function and arguments
    """
    args = (); kwargs = {}
    if 'qa_function' in flag:
        outfunc = getattr(qafunctions, flag['qa_function'])
        if 'qa_args' in flag:
            args = flag['qa_args']
        if 'qa_kwargs' in flag:
            kwargs = flag['qa_kwargs']
    else:
        outfunc = getattr(qafunctions, 'mask_by_datetime')

    return [outfunc, args, kwargs]

def apply_qa_flags(df, flags):
    """
    Apply qa flags to a dataframe. There are two types of operations that can
    be performed on the input dataframe, depending on the QA flag:

    1. Transform data values based on qa flag input
    2. Mask data based on qa flag input
    
    These changes are logged in the flag array (df_flag) with a number
    corresponding to the qa flag in the site configuration files.

    Args:
        df      : input dataframe
        flags   : qa_flag dictionary from the site's datalog configuration dir
    Returns:
        Three pandas dataframes with identical dimensions to the input df
        df_new  : original data with any qa transformations applied
        df_mask : Mask dataframe containing boolean values (True = remove)
        df_flag : Flag dataframe with values corresponding to qa flags

    TODO - may want to add a flag for data already missing
    """
    # Make a copy to be a qa'd dataframe, aboolean array, and a flag dataframe
    df_new = df.copy()
    df_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    df_flag = pd.DataFrame(0, index=df.index, columns=df.columns)
    # Loop through qa flags
    for k, flag in flags.items():
        if k in (0, '0'):
            raise ValueError('QA flag key cannot be zero (0)!')
        st = flag['start']
        if st is None:
            st = df.index.min()
        en = flag['end']
        if en is None:
            en = datetime.now()
        qafunc, qa_args, qa_kwargs = get_qafunction(flag)
        print('Apply QA flag {0}, using {1}.'.format(k, qafunc))
        if flag['columns']=='all':
            # If "all" columns to be flagged select all
            colrange = df.columns
        else:
            # Or find dataframe columns matching those in qa_flags
            test = [any(s in var for s in flag['columns'])
                    for var in df.columns] 
            colrange = df.columns[test]
        # Get the index range to be flagged
        idxrange = np.logical_and(df.index >= st, df.index <= en)
        # Get the mask for flag k and set appropriate flag
        df_new, mask_k, rm = qafunc(df_new, idxrange, colrange,
                *qa_args, **qa_kwargs)
        # Add mask_k to df_flag and to df_mask if data are to be masked
        df_flag = df_flag.where(mask_k, other=k)
        if rm:
            df_mask = np.logical_or(df_mask, mask_k)

    # Rewrite df_flag column names
    df_flag.columns = df_flag.columns + '_flag'
    return df_new, df_mask, df_flag # df_new[df_mask]=np.nan will apply mask

def qa_dataframe(lname, df_corr=None, use_global=True):
    """
    Get qa dataframes with flags appended and values masked

    Args:
        lname (string): datalogger name
        df_corr (pandas dataframe): apply qa flags to this, usually corrected df
        use_global (bool): if set, use the global qa flags for the project
    Returns:
        df_qa       : QA'd dataframe
        df_qa_masked: QA'd dataframe with mask applied
        df_flag     : dataframe indicating which flags and where applied
    """
    # Load the dataframe or use a corrected dataframe if provided
    if df_corr is not None:
        # Use the corrected dataframe
        df = df_corr
        p = dio.get_datadir(lname, 'raw_std')
        _, colldates = dio.get_file_list(p, raw_std, parsedt=True)
    else:
        df, colldates = dio.get_latest_df(lname, 'raw_std')

    # Get logger (and global) qa flags and merge them
    flags = dio.read_yaml_conf(lname, 'qa_flags')
    gflags = {}
    if use_global:
        gflags = dio.read_yaml_conf('all', 'qa_flags')
    flags = {**flags, **gflags}
    
    # Apply qa flags
    df_qa, df_mask, df_flag = apply_qa_flags(df, flags)

    # Create the masked dataframe
    df_qa_masked = df_qa.copy()
    df_qa_masked[df_mask] = np.nan

    return df_qa, df_qa_masked, df_flag, max(colldates)
