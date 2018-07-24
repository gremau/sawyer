"""
Functions that can be called to qa a dataframe, either marking data for 
removal, or transforming values in some way (unit conversions, calibration 
corrections, etc.). These are generally called from the apply_qa_flags 
function in the flag module. Functions must return a  dataframe (often the 
same as the input), a boolean array mask indicating which dataframe values the
qa flag points to, and a boolean value indicating whether the flagged data 
should be masked (True = flag for removal).
"""

import pandas as pd
import numpy as np
import pdb

nancval = ['NAN', 'NaN', 'Nan', 'nan']

def scale_by_multiplier(df, idxrange, colrange, multiplier):
    """
    Scale all values in indicated row and column range by the multiplier
    """
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    mask.loc[idxrange, colrange] = True
    df[mask] = df[mask] * multiplier
    return [df, mask, False]

def mask_by_datetime(df, idxrange, colrange):
    """
    Mask all matching idxrange and colrange
    """
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    mask.loc[idxrange, colrange] = True
    return [df, mask, True]

def mask_by_comparison(df, idxrange, colrange, comparison, cval):
    """
    Mask values in matching idxrange and colrange AND colrange variables
    are above/below cval 
    """
    if cval in nancval:
        comparison = 'isnan'

    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    for c in colrange:
        if comparison=='above':
            idxrange_th = np.logical_and(idxrange, df[c] > cval)
        elif comparison=='below':
            idxrange_th = np.logical_and(idxrange, df[c] < cval)
        elif comparison=='equals':
            idxrange_th = np.logical_and(idxrange, df[c] == cval)
        elif comparison=='isnan':
            idxrange_th = np.logical_and(idxrange, np.isnan(df[c]))

        else:
            raise ValueError('Invalid comparison (above, below, equals)')
        mask.loc[idxrange_th, c] = True
    return [df, mask, True]

def mask_by_comparison_ind(df, idxrange, colrange, indvar,
        comparison, cval):
    """
    Mask values in matching idxrange and colrange AND where an independent
    variable (indvar) is above/below cval 
    """
    if cval in nancval:
        comparison = 'isnan'

    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    if comparison=='above':
        idxrange_thv = np.logical_and(idxrange, df[indvar] > cval)
    elif comparison=='below':
        idxrange_thv = np.logical_and(idxrange, df[indvar] < cval)
    elif comparison=='equals':
        idxrange_thv = np.logical_and(idxrange, df[indvar] == cval)
    elif comparison=='isnan':
        idxrange_thv = np.logical_and(idxrange, np.isnan(df[indvar]))
    else:
        raise ValueError('Invalid comparison (above, below, equals)')
    mask.loc[idxrange_thv, colrange] = True
    return [df, mask, True]

def mask_by_rolling_stat(df, idxrange, colrange, indvar, stat,
        window, comparison, thresh=0):
    """
    Mask values in matching idxrange and colrange AND where an independent
    variable (indvar) is above/below cval 

    Args:
        df (dataframe): a pandas dataframe containing datalogger data
        idxrange (boolean): rows of df to apply this function
        colrange (boolean): columns of df to apply this function
        indvar (string): variable name to apply moving statistic to
        stat (string): statistic to apply to indvar ('mean','median','stdv')
        window (int or string): moving window size (int or time, ie. '30min')
        comparison (string): comparison to make to calculated statistic
        thresh (float): threshold for comparison (compare to stat_ts +/- thresh)
    Returns:
        df: dataframe (unchanged)
        mask: dataframe listing data removals (1 for remove)
        bool: True for remove data
    """
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)    
    
    # Calculate the time series statistic
    if stat=='mean':
        stat_ts = df[indvar].rolling(window,
                center=True, min_periods=window-1).mean()
    elif stat=='median':
        stat_ts = df[indvar].rolling(window,
                center=True, min_periods=window-1).median()
    elif stat=='stdv':
        raise ValueError('This STDDEV filter is not working yet!!!')
        stat_ts = df[indvar].rolling(window,
                center=True, min_periods=window-1).std()
    else:
        raise ValueError('Invalid statistic (mean, median, stdv)')
    
    # Compare the data to stat_ts and flag
    if comparison=='above':
        idxrange_thv = np.logical_and(idxrange, df[indvar] > stat_ts + thresh)
    elif comparison=='below':
        idxrange_thv = np.logical_and(idxrange, df[indvar] < stat_ts - thresh)
    elif comparison=='equals':
        idxrange_thv = np.logical_and(idxrange, df[indvar] == stat_ts)
    else:
        raise ValueError('Invalid comparison (above, below, equals)')
    mask.loc[idxrange_thv, colrange] = True
    return [df, mask, True]
