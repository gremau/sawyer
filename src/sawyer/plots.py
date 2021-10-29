"""
Plot functions for checking data from a datalogger before or after qa processes
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sawyer.dtools as dtool
import sawyer.config as sy
from IPython.core.debugger import set_trace

class tcol:
    """
    Simple class for assigning terminal output colors
    """
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    UNDERLINE = '\033[4m'

if sy.conf.import_uplots:
    import userplots as u
    print(tcol.WARNING + "Importing user plots as submodule `u`: call " +
            tcol.ENDC + tcol.UNDERLINE + "plots.u.<functionname>" + tcol.ENDC +
            tcol.WARNING  + " .\n" + tcol.ENDC)


def meas_profile_tsfig(df, lname, var, ylabel, strexclude=None, ylimit=None):
    """
    Make a time series figure for sensors in a measurement profile
    """
    # Get measurement dictionary
    measdict = dtool.var_h_v_dict(df.columns, var,
            str_exclude=strexclude)
    nplots = len(measdict.keys())
    # Set up plot
    fig, ax = plt.subplots(nplots, figsize=(11.5, 8), sharex=True)
    if nplots==1: ax = [ax]
    fig.canvas.manager.set_window_title(lname + ' ' + var + ' timeseries') 
    # Loop through each profile and depth and plot
    for i, pnum in enumerate(sorted(measdict.keys())):
        for d in measdict[pnum]:
            colname = pnum + '_' + d
            ax[i].plot( df.index, df[colname], marker='.', lw=1.25, label=str(d)+'cm' )
        ax[i].legend(loc='upper left', bbox_to_anchor=(0, 1.05),
                ncol=4, fontsize=10)
        if ylimit is not None:
            ax[i].set_ylim(ylimit)
        ax[i].set_title('Profile ' + pnum)
        ax[i].set_ylabel(ylabel)
    return fig

def meas_profile_scatterfig(df, lname, var, ylabel, strexclude=None,
        ylimit=[-155,0]):
    """
    Make a scatterplot figure for sensors in a measurement profile
    """
    # Get measurement dictionary
    measdict = dtool.var_h_v_dict(df.columns, var,
            str_exclude=strexclude)
    nplots = len(measdict.keys())
    # Set up plot
    fig, ax = plt.subplots(1, nplots, figsize=(7, 5), sharey=True)
    if nplots==1: ax = [ax]
    fig.canvas.manager.set_window_title(lname + ' ' + var + ' profile') 
    # Loop through each profile and depth and plot againt depth
    for i, pnum in enumerate(sorted(measdict.keys())):
        for d in measdict[pnum]:
            depth = d.split('_')[0]
            colname = pnum + '_' + d
            ax[i].plot(df[colname],np.tile(-int(depth), [len(df), 1]),
                    marker='o', ls='None', label=str(depth)+'cm' )
        ax[i].set_title('Profile ' + pnum)
        ax[i].set_ylim(ylimit)
        ax[i].set_xlabel(ylabel)
        if i==0:
            ax[i].set_ylabel('Depth (cm)')
    return fig

def tsfig_add_filedates(fig, filedates):
    """
    Add vertical lines indicating a series of dates (usually referring to the
    date of file collection)
    """
    for a in fig.axes:
        ymin, ymax = a.get_ylim()
        a.vlines(filedates, ymin, ymax, linestyles='dotted',lw=0.5)

def qa_var_tsplot(ax, varname, df, df_qa, df_qa_masked):
    """
    Plot a variable showing what has been modified in the qa process
    """
    #varname_f = varname + '_flag'
    # Plot original data and overlay qa data
    ax.plot(df.index, df[varname], marker= '.', ls='none', color = '0.75',
            label='Raw file data')
    ax.plot(df_qa.index, df_qa[varname], '.k', label='QA file data')
    # If there is a shift between them circle it
    test_qa = df[varname] != df_qa[varname]
    ax.plot(df_qa.index[test_qa], df_qa[varname][test_qa], 'o', mfc='none',
            mec='xkcd:neon green', mew='0.3', alpha=.5, label='Shifted in QA')
    # Plot the removed data in red
    test_mask = df_qa_masked[varname] != df_qa[varname]
    ax.plot(df_qa.index[test_mask], df_qa[varname][test_mask], '.r',
            label='Masked values')
    ax.set_ylabel(varname)
    #ax.legend()

    return ax

def gf_var_tsplot(ax, varname, df_qa, df_gf):
    """
    Plot a variable showing what has been gapfilled
    """
    #varname_f = varname + '_f'
    # Plot gapfill data oand overlay qa data
    ax.plot(df_gf.index, df_gf[varname], marker= '.', ls='none',
            color = 'xkcd:neon green', label='Gapfilled')
    ax.plot(df_qa.index, df_qa[varname], marker='.', ls='none',
            color='k', label='Original')    
    ax.set_ylabel(varname)
    ax.legend()

    return ax

def qa_var_tsfig(df, df_qa, df_qamask, lname, var, ylabel, 
        get_vardict=False, strexclude=None, ylimit=None):
    """
    Make a figure that plots the results of the qa process. Either a list of
    variables to plot can be supplied, or a vardict can be requested, which 
    will plot one or more profiles of variables.
    """
    nfigs = 1
    # If requested convert var to a var_h_v dict (for measurement profiles)
    if get_vardict:
        figs = []
        # Get the variable h_v dict to set up the number of figs
        vardict = dtool.var_h_v_dict(df_qa.columns, var,
            str_exclude=strexclude)
        nfigs = len(vardict.keys())
        # For each "h" location (profile) make a figure with subplots for
        # each "v" location
        for p, prof in enumerate(sorted(vardict.keys())):
            nplots = len(vardict[prof])
            fig, ax = plt.subplots(nplots, figsize=(11.5, 8), sharex=True)
            if nplots==1: ax = [ax]
            fig.canvas.manager.set_window_title(lname + ' ' + prof + ' QA timeseries')
            for v, vert in enumerate(vardict[prof]):
                varname = prof + '_' + vert
                qa_var_tsplot(ax[v], varname, df, df_qa, df_qamask)
                ax[v].set_title(varname)
                ax[v].set_ylabel(ylabel)
            figs.append(fig)
        return figs
    # Otherwise just plot each supplied variable in a subplot
    else:
        nplots = len(var)
        # Set up plot
        fig, ax = plt.subplots(nplots, figsize=(11.5, 8), sharex=True)
        if nplots==1: ax = [ax]
        fig.canvas.manager.set_window_title(lname + ' QA timeseries') 
        # Loop through each profile and depth and plot
        for i, vname in enumerate(var):
            qa_var_tsplot(ax[i], vname, df, df_qa, df_qamask)
            ax[i].set_title(vname)
            ax[i].set_ylabel(ylabel)
        return fig

def gf_var_tsfig(df_qa, df_gf, lname, var, ylabel, 
        get_vardict=False, strexclude=None, ylimit=None):
    """
    Make a figure that plots the results of the gapfilling. Either a list of
    variables to plot can be supplied, or a vardict can be requested, which 
    will plot one or more profiles of variables.
    """
    nfigs = 1
    # If requested convert var to a var_h_v dict (for measurement profiles)
    if get_vardict:
        figs = []
        # Get the variable h_v dict to set up the number of figs
        vardict = dtool.var_h_v_dict(df_qa.columns, var,
            str_exclude=strexclude)
        nfigs = len(vardict.keys())
        # For each "h" location (profile) make a figure with subplots for
        # each "v" location
        for p, prof in enumerate(sorted(vardict.keys())):
            nplots = len(vardict[prof])
            fig, ax = plt.subplots(nplots, figsize=(11.5, 8), sharex=True)
            if nplots==1: ax = [ax]
            fig.canvas.manager.set_window_title(lname + ' ' + prof + ' GF timeseries')
            for v, vert in enumerate(vardict[prof]):
                varname = prof + '_' + vert
                gf_var_tsplot(ax[v], varname, df_qa, df_gf)
                ax[v].set_title(varname)
                ax[v].set_ylabel(ylabel)
            figs.append(fig)
        return figs
    # Otherwise just plot each supplied variable in a subplot
    else:
        nplots = len(var)
        # Set up plot
        fig, ax = plt.subplots(nplots, figsize=(11.5, 8), sharex=True)
        if nplots==1: ax = [ax]
        fig.canvas.manager.set_window_title(lname + ' GF timeseries') 
        # Loop through each profile and depth and plot
        for i, vname in enumerate(var):
            gf_var_tsplot(ax[i], vname, df_qa, df_gf)
            ax[i].set_title(vname)
            ax[i].set_ylabel(ylabel)
        return fig
