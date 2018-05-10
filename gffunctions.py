"""
Functions that can be called to gapfill a dataframe. These are generally
called from the gapfill_series function in the gapfill module. Functions 
must return a dataframe (often the same as the input), and a boolean array mask
indicating which dataframe values are gapfilled.
"""

import pandas as pd
import numpy as np
import pdb

nancval = ['NAN', 'NaN', 'Nan', 'nan']

def substitution(x_from, y_to):
    """
    Mask values in matching idxrange and colrange AND colrange variables
    are above/below cval 
    """
    y_out = y_to.copy()

    yx = pd.concat([y_to, x_from], axis=1, join='inner')
    yx.columns = ['y', 'x']
    
    #commonidx = ~yx.isna().any(1)
    gapfillidx = np.logical_and(~np.isnan(yx.x), np.isnan(xy.y))

    y_out[gapfillidx] = yx[gapfillidx].x
        
    return y_out

def midpoint(x_from1, x_from2, y_to):
    """
    Mask values in matching idxrange and colrange AND colrange variables
    are above/below cval 
    """
    y_out = y_to.copy()

    yx = pd.concat([y_to, x_from1, x_from2], axis=1, join='inner')
    yx.columns = ['y', 'x1', 'x2']
    
    #commonidx = ~yx.isna().any(1)
    x1x2idx = np.logical_and(~np.isnan(yx.x1), ~np.isnan(yx.x2))
    gapfillidx = np.logical_and(x1x2idx, np.isnan(xy.y))

    y_out[gapfillidx] = yx[gapfillidx].loc[:,['x1','x2']].mean(axis=1)
        
    return y_out


def linearfit(x_from, y_to, zero_intcpt=False):
    """
    Mask all matching idxrange and colrange
    """
    y_out = y_to.copy()
    #yfillidx = np.isnan(y_to)

    yx = pd.concat([y_to, x_from], axis=1, join='inner')
    yx.columns = ['y', 'x']
    
    commonidx = ~yx.isna().any(1)
    gapfillidx = np.logical_and(~np.isnan(yx.x), np.isnan(xy.y))
    
    if zero_intcpt:
        # This is the least-squares solution for y=a*x (intercept of zero)
        coeff = (yx[commonidx].x.dot(xy[commonidx].y)/
                yx[commonidx].x.dot(xy[commonidx].x))
        y_out[gapfillidx] = yx[gapfillidx].x * coeff
    else:
        coeff = np.polyfit(yx[commonidx].x, xy[commonidx].y, 1)
        y_out[gapfillidx] = np.polyval(coeff, yx[gapfillidx].x)

    return y_out


def linearfit2(x_from, y_to):
    """
    Mask all matching idxrange and colrange
    """
    import scipy.optimize as sciop

    y_out = y_to.copy()

    yx = pd.concat([y_to, x_from], axis=1, join='inner')
    yx.columns = ['y', 'x']
    
    commonidx = ~yx.isna().any(1)
    gapfillidx = np.logical_and(~np.isnan(yx.x), np.isnan(xy.y))

    # Minimize slope m in this function (sum of squared errors)
    def sse_linfit_zero_intcpt(m, x, y):
        return sum( ( y - ( m * x ) ) ** 2 )
        
    # Use scipy optimization tool to find slope
    coeff = sciop.fmin(func=sse_linfit_zero_intcpt, x0=1.1,
            args=(yx[commonidx]. x,yx[commonidx].y))

    y_out[gapfillidx] = yx[gapfillidx].x * coeff

    return y_out
