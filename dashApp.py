import dash
import plotly.express as px
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output

from portfolio import read_portfolio_from_pickle, Portfolio

#   get data

ptf = read_portfolio_from_pickle('portfolio.pkl')
w = ptf.summary['weight']
scaled = ptf.get_scaled_prices()

#   Create app
app = dash.Dash()
#   create static figure - multi-line plot
fig1 = px.line(scaled, title='Ticker revenue comparison')
fig1.update_layout(yaxis_tickformat='%')


def slider(i):
    return html.Div([html.Label(ptf.summary['name'][i]),
                     daq.Slider(id='stkWeight{0}'.format(i),
                                min=0, max=100, value=100, step=10, size=200,
                                handleLabel={"showCurrentValue": True, 'label': '%'},
                                labelPosition='bottom',
                                marks={0: {'label': '0%'},
                                       100: {'label': '100%'}})],
                    style={'display': 'inline-block',
                           'margin-right': 50,
                           'margin-left': 50,
                           'margin-top': 50,
                           'margin-bottom': 50})


#   Configure HTML layout
app.layout = html.Div([
    html.Div([dcc.Input(id='ticker-name', type='text', placeholder='Insert ticker symbol'),
              html.Button('Add', id='add-button'), html.Button('Remove', id='remove-button')]),
    dcc.Graph(id='all-ticker-graph', figure=fig1),
    html.Div(id='sliders', children=[slider(i) for i in range(len(w.index))]),
    dcc.Graph(id='combined-graph'),
    dcc.Graph(id='pie-plots')
])


#   App callbacks
@app.callback(Output('all-ticker-graph', 'figure'),
              [Input('add-button', 'n_clicks'), Input('ticker-name', 'value')])
def update_portfolio(_, tick):
    ptf.add(tick)
    scaled = ptf.get_scaled_prices()
    figure = px.line(scaled, title='Ticker revenue comparison')
    figure.update_layout(yaxis_tickformat='%')
    return figure


@app.callback(Output('sliders', 'children'),
              [Input('add-button', 'n_clicks'), Input('ticker-name', 'value')])
def update_sliders(_, tick):
    ptf.add(tick)
    w = ptf.summary['weight']
    return [slider(i) for i in range(len(w.index))]


@app.callback(Output('combined-graph', 'figure'),
              [Input(component_id='stkWeight{}'.format(i), component_property='value') for i in range(len(w.index))])
def update_combined_figure(*ws):
    a = ptf.update(weights=list(ws))
    figure = px.line(a.get_combined_worth(), title='Combined revenue')
    figure.update_layout(yaxis_tickformat='%', showlegend=False)
    return figure


@app.callback(Output('pie-plots', 'figure'),
              [Input(component_id='stkWeight{}'.format(i), component_property='value') for i in range(len(w.index))])
def update_pie_charts(*ws):
    a = ptf.update(weights=list(ws))
    sector_split = a.get_sector_split()
    figure = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])
    figure.add_trace(go.Pie(labels=a.currencySplit.index, values=a.currencySplit['weight'],
                            name='Currency', title='Currency exposure'),
                     row=1, col=1)
    figure.add_trace(go.Pie(labels=sector_split.index, values=sector_split.to_list(),
                            name='Sector', title='Sector exposure'),
                     row=1, col=2)
    return figure


app.run_server(debug=False)
