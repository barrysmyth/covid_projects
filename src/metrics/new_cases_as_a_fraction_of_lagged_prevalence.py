
def dailies_as_a_fraction_of_prevalence(
    df, daily_col, group_col, date_col, prevalence_period='14d', new_cases_lag=7
):
    
    prevalence = df.groupby(group_col).apply(
        lambda g: g.set_index(date_col)[daily_col].rolling(prevalence_period).sum()
    )