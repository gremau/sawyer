"""
A module of unit conversion functions that can be loaded to convert
"""
import pandas as pd

def co2_mol_to_C_mass_flux( df, n_seconds ) :
    """
    Convert molar CO2 flux to mass C flux ( umolCO2/m^2/s to gC/m^2 )
    and sum (integrate) for each period in the timeseries for each column
    in data frame

    Args:
        df: a pandas dataframe
        n_seconds: number of seconds to integrate in the conversion

    Returns:
        df_int: an converted, integrated dataframe

    TODO
        1. Could be good to diff the index (n seconds per meas), then integrate,
        thus removing the seconds argument.

    """
    # Initialize returned variables
    df_int = df.copy()
    export_cols = []
    # For each input column create a new header and convert values to mass flux
    for cname in df.columns :
        export_cname = cname + '_g_int'
        export_cols.append( export_cname )
        # Integrate based on number of seconds
        df_int[ export_cname ] = df_int[ cname ] * ( 12.011/1e+06 ) * n_seconds

    return df_int[ export_cols ]
