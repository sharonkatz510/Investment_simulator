import pandas as pd
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import column
from bokeh.palettes import Category20
from bokeh.models import HoverTool, ColumnDataSource, NumeralTickFormatter
#
"""Plotting tools for investment simulator"""


def plot_multi_asset_line(df):
    """
    :param df: (pandas DataFrame) with asset prices indexed by date
    :return: bokeh plot
    """
    pallet = Category20[df.shape[1]]
    p = figure(
        title='asset comparison', x_axis_label='Date', y_axis_label='price relative to start price',
        x_axis_type='datetime', plot_width=1200, sizing_mode="scale_width"
    )
    for i in range(df.shape[1]):
        cds = ColumnDataSource(df.iloc[:, i].to_frame().dropna())
        p.line(x='Date', y=df.columns[i], legend_label=df.columns[i],
               name=df.columns[i], color=pallet[i], source=cds)

    p.legend.location = 'top_left'
    p.legend.click_policy = 'hide'
    p.yaxis.formatter = NumeralTickFormatter(format='0 %')
    p.add_tools(HoverTool(
        tooltips=[
            ('date', '@Date{%F}'),
            ('worth', '$y{0,0%}'),
            ('name', '$name')
        ],

        formatters={
            'Date': 'datetime'  # use 'datetime' formatter for 'date' field
        },
        mode='mouse'
    ))
    return p


def plot_single_graph(series):  # TODO: finish
    """
    :param series: (pandnas Series)
    :return: bokeh plot
    """
    p = figure(
        title='Combined portfolio worth', y_axis_label='price relative to start', x_axis_label='Date',
        plot_width=1200, sizing_mode="scale_width", x_axis_type='datetime'
    )
    p.yaxis.formatter = NumeralTickFormatter(format='0 %')
    p.line(series.index, series.tolist())
    p.add_tools(HoverTool(
        tooltips=[
            ('date', '$x{%F}'),
            ('worth', '$y{0,0%}'),
        ],
        formatters={'$x': 'datetime'},
        mode='mouse'
    ))
    return p


__all__ = ['output_file', 'show', 'column',
           'plot_multi_asset_line', 'plot_single_graph']
