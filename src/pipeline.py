import pandas as pd

import numpy as np

def compute_per_100k(df, cols_like='new_'):
    """Compute per capita values for cols, add to df and return."""
    
    per_100k = 100000*df.filter(like=cols_like)\
        .div(df['population'], axis=0)\
        .rename(columns={col: col+'_per_100k' for col in df.filter(like=cols_like).columns})
    
    return pd.concat([df, per_100k], axis=1)


def compute_rel_num(df, cols_like='new_'):
    
    rels = df.groupby('country')\
        .apply(lambda g: g.set_index('date').filter(like=cols_like)/g.set_index('date').filter(like=cols_like).max())\
        .rename(columns={col: 'rel_'+col  for col in df.filter(like=cols_like).columns})
        
    return df.set_index(['country', 'date']).join(rels).reset_index()
    

def compute_cumsum(df, cols_like='_per_100k'):
    
    totals = df.groupby('country')\
        .apply(lambda g: g.set_index('date').filter(like=cols_like).cumsum())\
        .rename(columns={col: col.replace(cols_like, cols_like+'_cumsum') for col in df.filter(like=cols_like).columns})
    
    return df.set_index(['country', 'date']).join(totals).reset_index()

rolling_period = '7d'

def compute_rolling(df, cols_like='_per_100k'):
    rolling = df.groupby('country').apply(
        lambda g: g.set_index('date')\
            .filter(like=cols_like)\
            .rolling(rolling_period).mean()\
            .rename(columns={col: col+'_rolling' for col in g.filter(like=cols_like).columns})
    )
    
    return df.set_index(['country', 'date']).join(rolling).reset_index()



infectous_period = '14d'

def compute_prevalence(df, cases_col='new_cases_per_100k_rolling', infectous_period=infectous_period):
    
    prevalence_col = '{}_prevalence_{}'.format(cases_col, infectous_period)
    
    # The sum of the new cases during the infectous period.
    prevalence = df.groupby('country')\
        .apply(lambda g: g.set_index('date')[[cases_col]].rolling(infectous_period).sum())\
        .rename(columns={cases_col: prevalence_col})
    
    return df.set_index(['country', 'date']).join(prevalence).reset_index()




transmission_prevalence_lag = 7

def compute_transmission_ratio(
    df, cases_col='new_cases_per_100k_rolling', 
    prevalence_col='new_cases_per_100k_rolling_prevalence_14d', 
    prevalence_lag=transmission_prevalence_lag
):
    
    use_col = '{}_transmission_ratio_{}d'.format(cases_col, prevalence_lag)
    
    new_cases_per_lagged_prevalence = pd.DataFrame(
        df.groupby('country').apply(lambda g: g.set_index('date')[cases_col]/g.set_index('date')[prevalence_col].shift(prevalence_lag)),
        columns=[use_col])
        
    return df.set_index(['country', 'date']).join(new_cases_per_lagged_prevalence).reset_index()
    
    
    
def compute_totals_per_100k(df):
    totals = df.groupby('country')\
        .apply(lambda g: g.set_index('date').filter(like='_per_100k').cumsum())\
        .rename(columns={col: col.replace('new_', 'total_') 
                         for col in df.filter(like='new_').columns
                        })
    
    return df.set_index(['country', 'date']).join(totals).reset_index()

