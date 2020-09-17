from matplotlib.pylab import plt
from matplotlib.ticker import FuncFormatter
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
from matplotlib import pyplot, lines
from matplotlib.patches import Patch
import matplotlib



import pandas as pd
import numpy as np

import datetime 


# Simplify a number of ease of labeling.
def simplify_number(n):
    
    if n < 1:
        label = '<1'
    elif n > 999999:
        label = '{:,}M'.format(int(n/1000000))
    else:
        label = '{:,}k'.format(int(n/1000)) if n>999 else '{:,}'.format(int(n))

    return label


def simplify_date(date): return date.strftime("%b %d")


# A directional arrow following bt a simplified number.
def directional_arrow(n):
    
    return '↑' if n>0 else '↓'


# A standard marker for peaks and other points
def mark_point(ax, x, y, color='r', markersize=6):
    ax.plot(x, y, marker='o', color=color, markersize=markersize)
    ax.plot(x, y, marker='o', markersize=1, c='k')
    

def plot_label(ax, x, y, label, va='bottom', ha='left', xoffset=datetime.timedelta(days=2), yoffset=.025, **kwargs):
        
    # Create some spacing around the label
    if ha=='right': xoffset = -xoffset
    if va == 'top': yoffset = -yoffset
        
    ax.text(x+xoffset, y+yoffset, label, va=va, ha=ha, color='dimgrey', **kwargs)
    

def plot_lockdown_model(ax, data, features, growth_type='cases', mobility_col='google_mobility_level_rolling_mean_rel', h = 0.4):
    
    # Some setup
    origin_date, end_date = datetime.date(2020, 1, 1), datetime.datetime.today()
    
    # Add the origin date to the features to avoid passing it as additional param
    features = features.append(pd.Series({'origin_date': origin_date}))
    
    growth_col = 'new_{}_rolling_mean'.format(growth_type)
    
    # Init axis
    ax = setup_axis(ax, origin_date, end_date, h)
    
    # Plot the main curves
    plot_growth_curve(ax, data[growth_col])
    plot_mobility_curve(ax, data[mobility_col], h)
    
    # Annotations and highlights.
    highlight_mobility_features(ax, features, growth_type, h)
    highlight_growth_features(ax, features, growth_type)
        
    # Add the title
    plot_title(ax, features)
    
    
def setup_axis(ax, origin_date, end_date, h):
    
    # x-axis date locators and formatters
    locator = mdates.AutoDateLocator(maxticks=7)
    formatter = mdates.ConciseDateFormatter(locator)
    
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    month_fmt = mdates.DateFormatter('%b')
    def m_fmt(x, pos=None): return month_fmt(x)[:3]

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(FuncFormatter(m_fmt))
        
    ax.tick_params(axis = 'x', which = 'major', width=1, length=5)

    ax.set_xlim(origin_date, end_date)
    ax.set_ylim(-h, 1+h)
    
    # Remove the axes spines and the y ticks
    [s.set_visible(False) for s in ax.spines.values()]
    [t.set_visible(False) for t in ax.get_yticklines()]
    [t.set_visible(False) for t in ax.get_yticklabels()]

    ax.spines['bottom'].set_visible(True)


    
    return ax



def plot_growth_curve(ax, growth_data, fill_colour='whitesmoke'):
    
    # Start at the first non-zero
    data = growth_data.loc[growth_data[growth_data>0].index[0]:].ffill()
    
    # The relative growth values
    rel_data = (data/data.max())
    
    # Plot the growth line and fill the area beneath its curve.
    ax.plot(rel_data.index, rel_data, lw=1.5, c='k')
    ax.fill_between(rel_data.index, 0, rel_data, color=fill_colour, alpha=.25)
    


def plot_mobility_curve(ax, mobility_data, h):
    
    mobility_data = mobility_data.ffill()
    
    # The colours mapped to rel mobility values
    transition_colours = ['white', 'skyblue', 'yellow', 'red']
    cmap = mcolors.LinearSegmentedColormap.from_list("", transition_colours)
    colours = [cmap(v) for v in (1-mobility_data).values]

    # Plot the bars
    ax.bar(mobility_data.index, [h]*len(mobility_data.index), bottom=-h, width=2, color=colours)
    
    # Plot the trace
    ax.plot(mobility_data.index, (mobility_data*h)-h, lw=1, c='k')
    
    
    
def highlight_mobility_features(ax, features, growth_type, h, **kwargs):
    
    lockdown_min_mobility_level = h*(features['lockdown_min_mobility_level']-1)
    rel_lockdown_entry = features['lockdown_entry_value_'+growth_type]/features['overall_peak_value_'+growth_type]
    rel_lockdown_exit = features['lockdown_exit_value_'+growth_type]/features['overall_peak_value_'+growth_type]

    
    # Start and end of lockdown
    ax.axvline(features['lockdown_start_date'], c='k', ls=':', lw=.5)
    ax.axvline(features['rebound_start_date'], c='k', ls=':', lw=.5)
    
    # Mark the crossing points with the growth curve; make sure to normalise the values correctly relative to overall peak.
    mark_point(ax, features['lockdown_start_date'], rel_lockdown_entry)
    mark_point(ax, features['rebound_start_date'], rel_lockdown_exit)

    # Mark the mobility min and add guideline
    mark_point(ax, features['lockdown_min_mobility_date'], lockdown_min_mobility_level)
    ax.plot([features['lockdown_min_mobility_date']]*2, [lockdown_min_mobility_level, ax.get_ylim()[0]], c='k', ls=':', lw=.5)
    
    # Label the crossing points and the min
    plot_label(ax, features['lockdown_start_date'], ax.get_ylim()[1], 'Start: {} {}/d @ {}'.format(
        simplify_number(features['lockdown_entry_value_'+growth_type]), growth_type[0], simplify_date(features['lockdown_start_date'])
    ), va='top', ha='right')
    
    plot_label(ax, features['rebound_start_date'], ax.get_ylim()[1], 'End: {} {}/d @ {}'.format(
        simplify_number(features['lockdown_exit_value_'+growth_type]), growth_type[0], simplify_date(features['rebound_start_date'])
    ), va='top', ha='left')
    
    # If the mobility level is high then plot the label above the min point.
    ypos = lockdown_min_mobility_level if features['lockdown_min_mobility_level']<.35 else ax.get_ylim()[0]
    plot_label(ax, features['lockdown_min_mobility_date'], ypos, '{}% @ {}'.format(
        simplify_number(100*features['lockdown_min_mobility_level']),
        simplify_date(features['lockdown_min_mobility_date'])
    ), va='bottom', ha='left')

    
    # Mark and label mobility levels during/after lockdown
    ax.plot([features['origin_date'], features['lockdown_start_date']], [h*(features['lockdown_mean_mobility_level']-1)]*2, c='k', ls=':', lw=0.5)
    ax.plot([features['lockdown_start_date'], features['rebound_start_date']], [h*(features['lockdown_mean_mobility_level']-1)]*2, c='k', ls='--', lw=1)

    ax.plot([features['origin_date'], features['rebound_start_date']], [h*(features['rebound_mean_mobility_level']-1)]*2, c='k', ls=':', lw=0.5)
    ax.plot([features['rebound_start_date'], features['overall_end_date']], [h*(features['rebound_mean_mobility_level']-1)]*2, c='k', ls='--', lw=1)

    plot_label(ax, features['origin_date'], h*(features['lockdown_mean_mobility_level']-1), 'During: {}% (x{}d)'.format(
        simplify_number(100*features['lockdown_mean_mobility_level']), simplify_number(features['lockdown_duration_days'])
    ), va='top')
    
    plot_label(ax, features['origin_date'], h*(features['rebound_mean_mobility_level']-1), 'After: {}% (x{}d)'.format(
        simplify_number(100*features['rebound_mean_mobility_level']), simplify_number(features['rebound_duration_days'])
    ))
    
    # Mark and label current mobility level and trend (relative to rebound)
    mark_point(ax, features['overall_end_date'], h*(features['current_mobility_level']-1), color='k', markersize=3)
    plot_label(ax, features['overall_end_date'], h*(features['current_mobility_level']-1), '{}%'.format(simplify_number(100*features['current_mobility_level'])), va='center')



    

def highlight_growth_features(ax, features, growth_type):
    
    # Mark and label the overall peak; it's a relative peak of 1 by definition.
    mark_point(ax, features['overall_peak_date_'+growth_type], 1)
    
    # Adjust the alignment if the peak is too close to right margin.
    ha = 'center' if features['overall_peak_date_'+growth_type]<(features['overall_end_date']-datetime.timedelta(days=7)) else 'right'
    plot_label(ax, features['overall_peak_date_'+growth_type], 1, '{} {}/d\n{}% @ {}'.format(
        simplify_number(features['overall_peak_value_'+growth_type]), growth_type[0],
        100, simplify_date(features['overall_peak_date_'+growth_type]) 
    ), ha=ha)
    ax.axvline(features['overall_peak_date_'+growth_type], c='k', ls=':', lw=.5)


    
    # If there is a separate lockdown peak then mark and label this.
    if features['overall_peak_date_'+growth_type] != features['lockdown_peak_date_'+growth_type]:
        mark_point(ax, features['lockdown_peak_date_'+growth_type], features['lockdown_peak_value_'+growth_type]/features['overall_peak_value_'+growth_type])
        ax.plot([features['lockdown_peak_date_'+growth_type]]*2, [ax.get_ylim()[0], features['lockdown_peak_value_'+growth_type]/features['overall_peak_value_'+growth_type]], c='k', ls=':', lw=.5)

        # if there is sufficient space between the lockdown and overall peaks then label the former.
        if abs((features['overall_peak_date_'+growth_type]-features['lockdown_peak_date_'+growth_type]).days)>10:
            plot_label(ax, features['lockdown_peak_date_'+growth_type], features['lockdown_peak_value_'+growth_type]/features['overall_peak_value_'+growth_type], '{} {}/d\n{}% @ {}'.format(
                simplify_number(features['lockdown_peak_value_'+growth_type]), growth_type[0],
                simplify_number(100*features['lockdown_peak_value_'+growth_type]/features['overall_peak_value_'+growth_type]), simplify_date(features['lockdown_peak_date_'+growth_type])
            ), ha='center')

    
    # Mark and label growth means during/after
    ax.plot([features['origin_date'], features['lockdown_start_date']], [features['lockdown_mean_value_'+growth_type]/features['overall_peak_value_'+growth_type]]*2, c='k', ls=':', lw=0.5)
    ax.plot([features['lockdown_start_date'], features['rebound_start_date']], [features['lockdown_mean_value_'+growth_type]/features['overall_peak_value_'+growth_type]]*2, c='k', ls='--', lw=1)

    ax.plot([features['origin_date']+datetime.timedelta(days=30), features['rebound_start_date']], [features['rebound_mean_value_'+'cases']/features['overall_peak_value_'+growth_type]]*2, c='k', ls=':', lw=0.5)
    ax.plot([features['rebound_start_date'], features['overall_end_date']], [features['rebound_mean_value_'+'cases']/features['overall_peak_value_'+growth_type]]*2, c='k', ls='--', lw=1)

    plot_label(ax, features['origin_date'], features['lockdown_mean_value_'+growth_type]/features['overall_peak_value_'+growth_type], 'During:\n{} ({}%)\n{}/day'.format(
        simplify_number(features['lockdown_mean_value_'+growth_type]), simplify_number(100*features['lockdown_mean_value_'+growth_type]/features['overall_peak_value_'+growth_type]), growth_type
    ), rotation=90)


    plot_label(ax, features['origin_date']+datetime.timedelta(days=30), features['rebound_mean_value_'+growth_type]/features['overall_peak_value_'+growth_type], 'After:\n{} ({}%)\n{}/day'.format(
        simplify_number(features['rebound_mean_value_'+growth_type]), simplify_number(100*features['rebound_mean_value_'+growth_type]/features['overall_peak_value_'+growth_type]), growth_type
    ), rotation=90)
    
    # Mark and label current mobility level and trend (relative to rebound)
    mark_point(ax, features['overall_end_date'], features['current_value_'+growth_type]/features['overall_peak_value_'+growth_type], color='k', markersize=3)
    plot_label(ax, features['overall_end_date'], features['current_value_'+growth_type]/features['overall_peak_value_'+growth_type], '{}%'.format(
        simplify_number(100*features['current_value_'+growth_type]/features['overall_peak_value_'+growth_type])
    ), va='center')


def plot_title(ax, features):
    
    title = '{} (p. ~{})\n{} cases/M, {} deaths/M, {:.2f} CFR'.format(
        features['location'].upper(), 
        simplify_number(features['population']),
        simplify_number(1000000*features['total_cases']/features['population']),
        simplify_number(1000000*features['total_deaths']/features['population']),
        features['cfr']
    )
    
    ax.set_title(title, loc='left')
    
    ax.text(features['origin_date']-datetime.timedelta(days=7), .5, 'Confirmed Cases', rotation=90, style='oblique')
    ax.plot([features['origin_date']]*2, [.02, 1.5], c='k', lw=.5)

    ax.text(features['origin_date']-datetime.timedelta(days=7), -.3, 'Mobility', rotation=90, style='oblique')
    ax.plot([features['origin_date']]*2, [-.5, -.02], c='k', lw=.5)

    ax.axhline(0, c='k', lw=.5)







