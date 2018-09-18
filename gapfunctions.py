"""
Functions that can be called to gapfill a dataframe. These are generally
called from the apply_gapfilling function in the gapfill module. Functions 
must return a dataframe (often the same as the input), and a boolean array mask
indicating which dataframe values are gapfilled.

In many cases we are accessing interpolation methods in scipy.interpolate,
especially in univariate cases (filling gaps indepenedent of any other
timeseries). For more information see here:

https://docs.scipy.org/doc/scipy/reference/interpolate.html

and here:
    
https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html

TODO - put in warnings about small amounts of fill data (relative to gaps)
"""

import pandas as pd
import numpy as np
from IPython.core.debugger import set_trace

nancval = ['NAN', 'NaN', 'Nan', 'nan']

def fillna(y_gaps, fillidx, *args, **kwargs):
    """
    Wrapper for pandas.DataFrame.fillna

    All arguments should go into gf_kwargs in gapfill.yaml

    See documentation at:
    
    https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.fillna.html
    """
    source, fillidx = args[0], args[1]
    y_new = y_gaps.copy()
    #return y_gaps.fillna(*args, **kwargs)
    y_new[fillidx] = y_gaps[fillidx].fillna(*args, **kwargs)
    y_predict_fill = np.logical_and(fillidx, np.isnan(y_new))
    return y_new, y_predict_fill

def interpolate(y_gaps, fillidx, *args, **kwargs):
    """
    Wrapper for pandas.DataFrame.interpolate

    All arguments should go into gf_kwargs in gapfill.yaml

    See documentation at:
    
    https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.interpolate.html
    """
    source, fillidx = args[0], args[1]

    y_new = y_gaps.copy()
    #return y_gaps.interpolate(*args, **kwargs)
    y_new[fillidx] = y_gaps[fillidx].interpolate(**kwargs)
    y_predict_fill = np.logical_and(fillidx, np.isnan(y_new))
    return y_new, y_predict_fill

def scipy_interp1d(y_gaps, fillidx, *args, **kwargs):
    """
    Wrapper for scipy.interpolate.interp1d

    All arguments should go into gf_kwargs in gapfill.yaml

    See documentation at:
    
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp1d.html#scipy.interpolate.interp1d

    IN PROGRESS
    """
    import scipy.interpolate.interp1d as i1d

    source, fillidx = args[0], args[1]

    y_new = y_gaps.copy()
    #return y_gaps.interpolate(*args, **kwargs)
    y_new[fillidx] = y_gaps[fillidx].interpolate(**kwargs)
    y_predict_fill = np.logical_and(fillidx, np.isnan(y_new))
    return y_new, y_predict_fill


def substitution(y_gaps, fillidx, *args, **kwargs):
    """
    Substitute values in source dataframe into gaps in y_gaps 
    (no transformation).

    IN PROGRESS
    """
    source, fillidx = args[0], args[1]

    y_out = y_gaps.copy()

    yx = pd.concat([y_gaps, x_from], axis=1, join='inner')
    yx.columns = ['y', 'x']
    
    #commonidx = ~yx.isna().any(1)
    gapfillidx = np.logical_and(~np.isnan(yx.x), np.isnan(xy.y))

    y_out[gapfillidx] = yx[gapfillidx].x
        
    return y_out

def midpoint(y_gaps, fillidx, *args, **kwargs):
    """
    Calculate gapfilling values as the midpoint between two columns in the
    source dataframe.

    IN PROGRESS
    """
    source, fillidx = args[0], args[1]
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


def linearfit(y_gaps, fillidx, *args, **kwargs):
    """
    Calculate linear regression between y_gaps and a source dataframe,
    predict the gapfilling values using the calculated coefficients.

    this does the regression a couple ways (could be pruned)
    """
    zero_intcpt = kwargs.get('zero_intcpt',False)
    set_trace()
    source, fillidx = args[0], args[1]
    y_out = y_gaps.copy()
    x_src = source.copy()
    #yfillidx = np.isnan(y_gaps)
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


def linearfit2(y_gaps, fillidx, *args, **kwargs):
    """
    Calculate linear regression between y_gaps and a source dataframe,
    predict the gapfilling values using the calculated coefficients.

    This is another method using scipy optimization
    """
    import scipy.optimize as sciop

    source, fillidx = args[0], args[1]

    y_out = y_gaps.copy()

    yx = pd.concat([y_gaps, x_from], axis=1, join='inner')
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
