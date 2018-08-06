"""
Functions that can be called to gapfill a dataframe. These are generally
called from the gapfill_series function in the gapfill module. Functions 
must return a dataframe (often the same as the input), and a boolean array mask
indicating which dataframe values are gapfilled.


TODO - put in warnings about small amounts of fill data (relative to gaps)
"""

import pandas as pd
import numpy as np
import pdb

nancval = ['NAN', 'NaN', 'Nan', 'nan']

def substitution(y_to, source, fillidx, conf):
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

def midpoint(y_gaps, source, fillidx):
    """
    Mask values in matching idxrange and colrange AND colrange variables
    are above/below cval 
    """
    y_out = y_gaps.copy()
    x_src = source.copy()
    # AUDIT - do  want an inner join (intersection)? Is this needed at all?
    # What if the source is shorter than y_gaps[fillidx]?
    yx = pd.concat([y_gaps, x_src], axis=1, join='inner')
    yx.columns = ['y', 'x1', 'x2']
    #commonidx = ~yx.isna().any(1)
    x1x2idx = np.logical_and(~np.isnan(yx.x1), ~np.isnan(yx.x2))
    ypredict = np.logical_and(x1x2idx, np.isnan(yx.y))
    # Gapfill (constrained by fillidx)
    ypredict_fill = np.logical_and(ypredict, fillidx)
    # Fill with mean of x1 and x2
    y_out[ypredict_fill] = yx[ypredict_fill].loc[:,['x1','x2']].mean(axis=1)
        
    return y_out, ypredict_fill


def linearfit(y_gaps, source, fillidx, zero_intcpt=False):
    """
    Mask all matching idxrange and colrange
    """
    y_out = y_gaps.copy()
    x_src = source.copy()
    #yfillidx = np.isnan(y_to)
    # AUDIT - do  want an inner join (intersection)? Is this needed at all?
    # What if the source is shorter than y_gaps[fillidx]?
    yx = pd.concat([y_gaps, x_src], axis=1, join='inner')
    yx.columns = ['y', 'x']
    
    # X and Y values present
    commonidx = ~yx.isna().any(1)
    # X present, Y missing (and can be predicted)
    ypredict = np.logical_and(~np.isnan(yx.x), np.isnan(yx.y))
    # Gapfill (constrained by fillidx)
    ypredict_fill = np.logical_and(ypredict, fillidx)
    
    if zero_intcpt:
        # This is the least-squares solution for y=a*x (intercept of zero)
        # https://medium.com/@andrew.chamberlain/f67044b7f39b
        # https://machinelearningmastery.com/solve-linear-regression-using-linear-algebra/
        coeff = (yx[commonidx].x.dot(yx[commonidx].y)/
                yx[commonidx].x.dot(yx[commonidx].x))
        # Can also use numpy linear alg solver - should be equivalent
        # https://stackoverflow.com/a/9994484
        x2 = yx[commonidx].x[:, np.newaxis]
        y2 = yx[commonidx].y
        coeff2, yint, _, _ = np.linalg.lstsq(x2, y2, rcond=None)
        y_out[ypredict_fill] = yx[ypredict_fill].x * coeff
    else:
        coeff = np.polyfit(yx[commonidx].x, yx[commonidx].y, 1)
        y_out[ypredict_fill] = np.polyval(coeff, yx[ypredict_fill].x)

    return y_out, ypredict_fill


def linearfit2(y_to, source, conf):
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
