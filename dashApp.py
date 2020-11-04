import dash
import plotly.express as px
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

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
    """
    :param i: index of slider for identification
    :return: Slider object with label
    """
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
    html.Div(id='all-assets', children=[dcc.Graph(id='all-ticker-graph', figure=fig1),
                                        html.Div(id='sliders', children=[slider(i) for i in range(len(w.index))])]),
    html.Div(id='combined-graph'),
])


#   App callbacks

@app.callback(Output('all-assets', 'children'), [Input('add-button', 'n_clicks'), Input('remove-button', 'n_clicks')],
              [State('ticker-name', 'value')])
def update_assets(_1, _2, tick):
    """
    Update assets when adding or removing an asset
    :param _1: add-button n_clicks as unused input
    :param _2: remove-button n_clicks as unused input
    :param tick: ticker-name in input box
    :return: update all-assets figure and sliders
    """
    global ptf, scaled
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'add-button' in changed_id:
        scaled = ptf.add(tick).get_scaled_prices()
    elif 'remove-button' in changed_id:
        scaled = ptf.remove(tick).get_scaled_prices()
    figure = px.line(scaled, title='Ticker revenue comparison')
    figure.update_layout(yaxis_tickformat='%')
    div = [dcc.Graph(id='all-ticker-graph', figure=figure),
           html.Div(id='sliders', children=[slider(i) for i in range(len(ptf.finance.columns))])]
    return div


@app.callback(Output('ticker-name', 'value'), [Input('add-button', 'n_clicks'), Input('remove-button', 'n_clicks')])
def clear_input(_1, _2):
    return ''


@app.callback(Output('combined-graph', 'children'),
              [Input(component_id='stkWeight{}'.format(i), component_property='value') for i in range(len(w.index))])
def update_combined_figures(*ws):
    """
    Update portfolio exposure and revenue according to sliders
    :param ws: list of slider values
    :return: combined revenue figure, currency exposure pie chart, sector exposure pie chart
    """
    a = ptf.update(weights=list(ws))
    figure1 = px.line(a.get_combined_worth(), title='Combined revenue')
    figure1.update_layout(yaxis_tickformat='%', showlegend=False)
    sector_split = a.get_sector_split()
    figure2 = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])
    figure2.add_trace(go.Pie(labels=a.currencySplit.index, values=a.currencySplit['weight'],
                             name='Currency', title='Currency exposure'), row=1, col=1)
    figure2.add_trace(go.Pie(labels=sector_split.index, values=sector_split.to_list(),
                             name='Sector', title='Sector exposure'), row=1, col=2)
    div = html.Div([dcc.Graph(figure=figure1), dcc.Graph(figure=figure2)])
    return div


app.run_server(debug=False)
