#!/usr/bin/env python
""" Dash app for simulating investment portfolio w/ different assets and weights. At the moment only works with ETFs"""

import dash
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State, ALL
from portfolio import read_portfolio_from_pickle, Portfolio, pd

#   get default data

ptf = read_portfolio_from_pickle('portfolio.pkl')
w = ptf.summary['weight']
scaled = ptf.get_scaled_prices()

#   Create app
app = dash.Dash()


def slider(i: int, ptf: Portfolio):
    """
    Slider object constructor
    :param i: index of slider (corresponding to asset #i)
    :param ptf: Portfolio
    :return: slider w/ range [0-100], upper title= asset name, lower title= asset symbol
    """
    return html.Div([html.Label(ptf.summary['name'][i]),
                     dcc.Slider(id={'type': 'slider', 'index': i},
                                min=0, max=100, value=100, step=10,
                                marks={0: {'label': '0%'},
                                       100: {'label': '100%'}}),
                     html.Label(ptf.summary.index[i])],
                    style={'display': 'inline-block',
                           'margin-right': 50,
                           'margin-left': 50,
                           'margin-top': 20,
                           'margin-bottom': 20,
                           'width': 300,
                           'textAlign': 'center'})


#   create default figs
fig1 = px.line(scaled, title='Ticker revenue comparison')
fig1.update_layout(yaxis_tickformat='%')
fig2 = px.line(ptf.get_combined_worth(), title='Combined revenue')
fig2.update_layout(yaxis_tickformat='%', showlegend=False)
sector_split = ptf.get_sector_split()
currency_split = ptf.get_currency_split()
fig3 = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])
fig3.add_trace(go.Pie(labels=currency_split.index, values=currency_split['weight'],
                      name='Currency', title='Currency exposure'), row=1, col=1)
fig3.add_trace(go.Pie(labels=sector_split.index, values=sector_split.to_list(),
                      name='Sector', title='Sector exposure'), row=1, col=2)
div2 = html.Div([dcc.Graph(figure=fig2), dcc.Graph(figure=fig3)])

#   Configure HTML layout
app.layout = html.Div([
    html.Div([dcc.Input(id='ticker-name', type='text', placeholder='Insert ticker symbol'),
              html.Button('Add', id='add-button'), html.Button('Remove', id='remove-button')]),
    html.Div(id='all-assets',
             children=[dcc.Graph(id='all-ticker-graph', figure=fig1),
                       html.Div(id='sliders', children=[slider(i, ptf) for i in range(len(w.index))])]),
    html.Button('Update weights', id='update-button'),
    html.Div(id='combined-graph', children=div2),
    html.Div([html.Button('Save portfolio', id='save-button'), html.Div(id='save-confirmation')],
             style={'display': 'inline-block'}),
    # Data sharing within the app
    html.Div(id='portfolio-data', children=[
        html.Div(id='portfolio-finance', children=ptf.finance.to_json(), style={'display': 'none'}),
        html.Div(id='portfolio-fund', children=ptf.summary.to_json(), style={'display': 'none'}),
        html.Div(id='portfolio-period', children=ptf.period, style={'display': 'none'}),
        html.Div(id='last_trigger', children=None, style={'display': 'none'})])
])


#   App callbacks
@app.callback(Output('portfolio-data', 'children'),
              [Input('add-button', 'n_clicks'),
               Input('remove-button', 'n_clicks'),
               Input('update-button', 'n_clicks')],
              [State('portfolio-finance', 'children'),
               State('portfolio-fund', 'children'),
               State('portfolio-period', 'children'),
               State('ticker-name', 'value'),
               State({'type': 'slider', 'index': ALL}, 'value')])
def update_assets(_1, _2, _3, finance, fund, period, tick, *ws):
    """
    Update portfolio when adding an asset, removing an asset or updating the weights
    """
    finance = pd.read_json(finance); summary = pd.read_json(fund)
    ptf = Portfolio(finance=finance, summary=summary, period=period)
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    trigger = None
    if 'add' in changed_id:
        ptf.add(tick)
        trigger = 'add'
    elif 'remove' in changed_id:
        ptf.remove(tick)
        trigger = 'remove'
    elif 'update' in changed_id:
        ptf.update(weights=ws[0])
        trigger = 'update'
    div = [
        html.Div(id='portfolio-finance', children=ptf.finance.to_json(), style={'display': 'none'}),
        html.Div(id='portfolio-fund', children=ptf.summary.to_json(), style={'display': 'none'}),
        html.Div(id='portfolio-period', children=ptf.period, style={'display': 'none'}),
        html.Div(id='last_trigger', children=trigger, style={'display': 'none'})]
    return div


@app.callback(Output('all-assets', 'children'), [Input('last_trigger', 'children')],
              [State('portfolio-finance', 'children'),
               State('portfolio-fund', 'children'),
               State('portfolio-period', 'children'),
               State('all-assets', 'children')])
def update_multi_asset_objects(trigger, finance, fund, period, div):
    """
    Update sliders and asset revenue comparison graph when asset list changes
    """
    finance = pd.read_json(finance); summary = pd.read_json(fund)
    ptf = Portfolio(finance=finance, summary=summary, period=period)
    if trigger == 'add' or trigger == 'remove':
        scaled = ptf.get_scaled_prices()
        figure = px.line(scaled, title='Ticker revenue comparison')
        figure.update_layout(yaxis_tickformat='%')
        div = [dcc.Graph(id='all-ticker-graph', figure=figure),
               html.Div(id='sliders', children=[slider(i, ptf) for i in range(len(finance.columns))])]
    return div


@app.callback(Output('combined-graph', 'children'), [Input('last_trigger', 'children')],
              [State('portfolio-finance', 'children'),
               State('portfolio-fund', 'children'),
               State('portfolio-period', 'children'),
               State('combined-graph', 'children')])
def update_combined_figures(trigger, finance, fund, period, div):
    """
    Update combined worth graph and exposure pie charts
    """
    finance = pd.read_json(finance); summary = pd.read_json(fund)
    ptf = Portfolio(finance=finance, summary=summary, period=period)
    if trigger is not None:
        figure1 = px.line(ptf.get_combined_worth(), title='Combined revenue')
        figure1.update_layout(yaxis_tickformat='%', showlegend=False)
        sector_split = ptf.get_sector_split()
        currency_split = ptf.get_currency_split()
        figure2 = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])
        figure2.add_trace(go.Pie(labels=currency_split.index, values=currency_split['weight'],
                                 name='Currency', title='Currency exposure'), row=1, col=1)
        figure2.add_trace(go.Pie(labels=sector_split.index, values=sector_split.to_list(),
                                 name='Sector', title='Sector exposure'), row=1, col=2)
        div = html.Div([dcc.Graph(figure=figure1), dcc.Graph(figure=figure2)])
    return div


@app.callback(Output('ticker-name', 'value'), [Input('add-button', 'n_clicks'), Input('remove-button', 'n_clicks')])
def clear_input(_1, _2):
    """
    Clear input box when adding or removing an asset
    """
    return ''


@app.callback(Output('save-confirmation', 'children'), [Input('save-button', 'n_clicks')],
              [State('portfolio-finance', 'children'),
               State('portfolio-fund', 'children'),
               State('portfolio-period', 'children')], prevent_initial_call=True)
def save_content(_, finance, fund, period):
    """
    Save portfolio to default portfolio.pkl file
    """
    finance = pd.read_json(finance); summary = pd.read_json(fund)
    ptf = Portfolio(finance=finance, summary=summary, period=period)
    ptf.save_to_pickle('portfolio.pkl')
    return 'Portfolio successfully saved'


if __name__ == "__main__":
    app.run_server(debug=True)

__author__ = "Sharon Katz"
__email__ = 'sharonkats510@gmail.com'
__license__ = "MIT"
