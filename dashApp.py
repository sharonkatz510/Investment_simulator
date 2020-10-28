import dash
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
from investment_simulator import *
from plotly.subplots import make_subplots
import plotly.graph_objects as go

#

ptf = read_portfolio_from_pickle('indexes.pkl')
prices_scaled = ptf.finance.apply(lambda x: x/x[x.first_valid_index()], axis=0).fillna(method='ffill')
w = ptf.summary['weight']
w.index = prices_scaled.columns
combined = (prices_scaled * w.transpose()).sum(axis=1)  # combined portfolio worth
#
fig1 = px.line(prices_scaled)
fig2 = px.line(combined.to_frame(name='Combined value'))
cur_split = get_weighted_count(ptf.summary, column = 'currency')
market_split = get_weighted_count(ptf.summary, column = 'market')
fig3 = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])
fig3.add_trace(go.Pie(labels=cur_split.index, values=cur_split['weight'], name='Currency'),
               row=1, col=1)
fig3.add_trace(go.Pie(labels=market_split.index, values=market_split['weight'], name='Market'),
               row=1, col=2)

fig1.update_layout(yaxis_tickformat = '%')
fig2.update_layout(yaxis_tickformat = '%')

app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig1),
    dcc.Graph(figure=fig2),
    dcc.Graph(figure=fig3)
])

app.run_server(debug=False)