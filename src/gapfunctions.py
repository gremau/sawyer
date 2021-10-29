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
require_src = ['substitution','midpoint','linearfit','linearfit2']

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

    y_out = y_gaps.copy()

    yx = pd.concat([y_gaps, x_from], axis=1, join='inner')
    yx.columns = ['y', 'x']
    
    #commonidx = ~yx.isna().any(1)
    gapfillidx = np.logical_and(~np.isnan(yx.x), np.isnan(xy.y))

    y_out[gapfillidx] = yx[gapfillidx].x
        
    return y_out

def midpoint(y_gaps, fillidx, *args, **kwargs):
    """
    Calculate gapfilling values as the midpoint between two source time series.
    """
    
    source = args
    y_out = y_gaps.copy()

    # Simple join - index checking done in gapfill.py and
    # indices of x and y should be identical
    xxy = source[0].join(source[1]).join(y_gaps)
    xxy.columns = ['x1', 'x2', 'y']
    #commonidx = ~yx.isna().any(1)
    x1x2idx = np.logical_and(~np.isnan(xxy.x1), ~np.isnan(xxy.x2))
    ypredict = np.logical_and(x1x2idx, np.isnan(xxy.y))
    # Gapfill (constrained by fillidx)
    ypredict_fill = np.logical_and(ypredict, fillidx)
    # Fill with mean of x1 and x2
    y_out[ypredict_fill] = xxy.loc[ypredict_fill,['x1','x2']].mean(axis=1)
        
    return y_out, ypredict_fill


def linearfit(y_gaps, fillidx, *args, **kwargs):
    """
    Calculate linear regression between y_gaps and a source dataframe,
    predict the gapfilling values using the calculated coefficients.

    this does the regression a couple ways (could be pruned)
    """
    #set_trace()
    zero_intcpt = kwargs.get('zero_intcpt',False)
    # Should only be one source
    x_src = args[0].copy()
    y_out = y_gaps.copy()
    
    # Simple join for regression - index checking done in gapfill.py and
    # indices of x and y should be identical
    xy = x_src.join(y_gaps, lsuffix='x', rsuffix='y')
    xy.columns = ['x', 'y']
    
    # X and Y values present
    commonidx = ~xy.isna().any(1)
    # X present, Y missing (and can be predicted)
    ypredict = np.logical_and(~np.isnan(xy.x), np.isnan(xy.y))
    # Gapfill index (constrained by reindexed ypredict and fillidx)
    ypredict_reind = ypredict.reindex(y_gaps.index, fill_value=False)
    ypredict_fill = np.logical_and(ypredict_reind, fillidx)
    # Get locations in xy to calculate fitted y values
    xyfit_locs = ypredict_fill.index[ypredict_fill]
    
    if zero_intcpt:
        # This is the least-squares solution for y=a*x (intercept of zero)
        # https://medium.com/@andrew.chamberlain/f67044b7f39b
        # https://machinelearningmastery.com/solve-linear-regression-using-linear-algebra/
        coeff = (xy[commonidx].x.dot(xy[commonidx].y)/
                xy[commonidx].x.dot(xy[commonidx].x))
        # Can also use numpy linear alg solver - should be equivalent
        # https://stackoverflow.com/a/9994484
        x2 = xy[commonidx].x[:, np.newaxis]
        y2 = xy[commonidx].y
        coeff2, yint, _, _ = np.linalg.lstsq(x2, y2, rcond=None)
        # calculate predicted values
        y_out[ypredict_fill] = xy.loc[xyfit_locs].x * coeff
    else:
        coeff = np.polyfit(xy[commonidx].x, xy[commonidx].y, 1)
        y_out[ypredict_fill] = np.polyval(coeff, xy.loc[xyfit_locs].x)

    return y_out, ypredict_fill


def linearfit2(y_gaps, fillidx, *args, **kwargs):
    """
    Calculate linear regression between y_gaps and a source dataframe,
    predict the gapfilling values using the calculated coefficients.

    This is another method using scipy optimization
    """
    import scipy.optimize as sciop

    zero_intcpt = kwargs.get('zero_intcpt',False)
    # Should only be one source
    x_src = args[0].copy()
    y_out = y_gaps.copy()

    # Simple join for regression - index checking done in gapfill.py and
    # indices of x and y should be identical
    xy = x_src.join(y_gaps, lsuffix='x', rsuffix='y')
    xy.columns = ['x', 'y']
    
    commonidx = ~xy.isna().any(1)
    # X present, Y missing (and can be predicted)
    ypredict = np.logical_and(~np.isnan(xy.x), np.isnan(xy.y))
    # Gapfill (constrained by fillidx)
    ypredict_fill = np.logical_and(ypredict, fillidx)

    # Minimize slope m in this function (sum of squared errors)
    def sse_linfit_zero_intcpt(m, x, y):
        return sum( ( y - ( m * x ) ) ** 2 )
        
    # Use scipy optimization tool to find slope
    coeff = sciop.fmin(func=sse_linfit_zero_intcpt, x0=1.1,
            args=(xy[commonidx].x, xy[commonidx].y))

    y_out[ypredict_fill] = xy[ypredict_fill].x * coeff

    return y_out, ypredict_fill
