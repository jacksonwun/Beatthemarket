import dash
import dash_core_components as dcc
import dash_html_components as html

import colorlover as cl
import datetime as dt
import pandas as pd
from pandas_datareader.data import DataReader


colorscale = cl.scales['9']['qual']['Paired']

def dispatcher(request):
    '''
    Main function
    @param request: Request object
    '''

    app = _create_app()
    params = {
        'data': request.body,
        'method': request.method,
        'content_type': request.content_type
    }
    with app.server.test_request_context(request.path, **params):
        app.server.preprocess_request()
        try:
            response = app.server.full_dispatch_request()
        except Exception as e:
            response = app.server.make_response(app.server.handle_exception(e))
        return response.get_data()

def _create_app():
    ''' Creates dash application '''

    app = dash.Dash(__name__,) # external_stylesheets=external_stylesheets)
    app.layout =   html.Div(children=[
        html.Div([
            dcc.Checklist(
                id='grab_data',
                options=[
                    {'label': 'Start Grabing Data', 'value': 'active'},
                ],
                value=[''],
                labelStyle={'display': 'inline-block'}
            ),
        ]),

        html.Div([
            html.H1("Market News", style={'fontSize': 24}),
            html.Button("refresh", id='news_refresh'),
            html.Div(id='news_table', children=[]),
        ], style={'textAlign': 'center','fontSize': 14,},),

        html.Label('Warrant Selector', style={'fontSize': 24, 'textAlign': 'center'}),

        html.Div('StockNumber:'),

        html.Div([
            dcc.Input(id='stocknumber', value='00700', type='text', style={'height': '30px'}),
            dcc.RadioItems(
                id='shortcut_stocknumber',
                options=[
                    {'label': '00700', 'value': '00700'},
                    {'label': '00388', 'value': '00388'},
                    {'label': '03690', 'value': '03690'},
                    {'label': '01810', 'value': '01810'},
                    {'label': '00016', 'value': '00016'},
                    {'label': '09988', 'value': '09988'},
                    {'label': '02382', 'value': '02382'},
                ],
                value='00700',
                labelStyle={'display': 'inline-block'},
                style={'display':'inline-block'},
            ),
        ],), 

        html.Div('Warrant Type:'),

        dcc.RadioItems(
            id='risedrop',
            options=[
                {'label': 'Rise', 'value': 'rise'},
                {'label': 'Drop', 'value': 'drop'},
            ],
            value='rise',
            labelStyle={'display': 'inline-block'}
        ),

        dcc.Checklist(
            id='callput',
            options=[
                {'label': 'Call', 'value': '購'},
                {'label': 'Put', 'value': '沽'},
                {'label': 'Bull', 'value': '牛'},
                {'label': 'Bear', 'value': '熊'},
            ],
            value=['購', '', '', ''],
            labelStyle={'display': 'inline-block'}
        ),

        html.Div('Warrant Provider:'),

        dcc.Checklist(
            id='warrantprovider_checklist',
            options=[
                {'label': u'海通', 'value': '海通'},
                {'label': u'瑞銀', 'value': '瑞銀'},            
                {'label': u'中銀', 'value': '中銀'},            

                {'label': u'摩通', 'value': '摩通'},
                {'label': u'摩利', 'value': '摩利'},
                {'label': u'麥銀', 'value': '麥銀'},            
                {'label': u'法巴', 'value': '法巴'},
                {'label': u'法興', 'value': '法興'},

                {'label': u'瑞通', 'value': '瑞通'},
                {'label': u'匯豐', 'value': '匯豐'},
                {'label': u'瑞信', 'value': '瑞信'},
                {'label': u'高盛', 'value': '高盛'},

                {'label': u'國君', 'value': '國君'},
                {'label': u'東亞', 'value': '東亞'},
            ],
            value=['麥銀', '海通', '摩通', '法巴', '法興', '瑞通', '瑞銀', '匯豐', '中銀', '摩利', '',''],
            labelStyle={'display': 'inline-block'}
        ),

        dcc.Checklist(
            id='realtime_warrant_list',
            options=[
                {'label': 'Find Traded Positions', 'value': 'Traded Positions'},
                {'label': 'Exclude Implied volatility', 'value': 'Exclude Implied volatility'},
            ],
            value=['Exclude Implied volatility'],
            labelStyle={'display': 'inline-block'}
        ),

        html.Div('Last Price:'),

        html.Div([
            dcc.RangeSlider(
                id='last_price_slider',
                marks={0:'0', 0.05:'0.05', 0.1:'0.1', 0.25:'0.25', 0.5: '0.5', 1:'1', 1.5:'1.5'},
                #marks={i: '{}'.format(1.2 * i) for i in [0, 1, 1.5]},
                max=2,
                min=-0.05,
                value=[0.05, 0.25],
                dots=False,
                step=0.01,
                updatemode='drag',
                allowCross=False
            ),
        ], style={'width': '60%'}),

        html.Td(),
        html.Td(),
        html.P(),
        html.P(),

        html.Button('Warrant', id='Warrant'),
        html.Button('Realtime-Warrant', id='realtime_warrant'),
        html.Div([
            html.Div(id='time counter'),
            dcc.Interval(
                id='my-interval',
                interval=1*1000, # in milliseconds
                n_intervals=0
            )
        ]),

        html.Div(
            id='table',
            children=[
                # dash_table.DataTable(
                #     id='test_table',
                #     columns=[
                #         {"name": i, "id": i, "deletable": True} for i in df.columns
                #     ],
                #     data=df.to_dict('records'),
                #     editable=True,
                #     #filtering=True,
                #     filter_action='native',
                #     #sorting=True,
                #     sort_action="native",
                #     #sorting_type="multi",
                #     sort_mode="multi",
                #     row_selectable="multi",
                #     row_deletable=True,
                #     selected_rows=[],
                #     #pagination_mode="fe",
                #     page_action='native',
                #     #pagination_settings={
                #     #    "current_page": 0,
                #     #    "page_size": warrant_limit,
                #     #},
                #     page_current=0,
                #     page_size=warrant_limit,
                # ),
            ],
        ),

        html.Hr(),

        html.Div(
            'Non Realtime table'
        ),
        
        html.Div(
            id='out-table',
        ),

        html.Label('Slaughter Monitor', style={'fontSize': 24, 'textAlign': 'center'}),

        html.Div('Call:'),

        html.Div(
            id='slaughter_monitor',
            children=[
                # dcc_slaughter_monitor.stock(stocknumber='00700'),
                # dcc_slaughter_monitor.warrant(stocknumber='00700'),
            ],
        ),

        html.Div(
            children=[
                dcc.Input(id='add_slaughter_wrt', value='', type='text'),
                html.Button("Add", id='add_slaughter'),
                dcc.Input(id='del_slaughter_wrt', value='', type='text'),
                html.Button("Del", id='del_slaughter'),
                dcc.Input(id='show_slaughter_wrt', value='', type='text'),
                html.Button("show", id='show_slaughter'),
            ],
        ),

        html.P(),
        html.P(),
        html.P(),
        html.P(),
        html.P(),
        html.P(),
        html.P(),
        html.P(),        
        html.Hr(),
        
    ])


    @app.callback(
    dash.dependencies.Output('graphs','children'),
    [dash.dependencies.Input('stock-ticker-input', 'value')])

    def update_graph(tickers):
        graphs = []
        for i, ticker in enumerate(tickers):
            try:
                df = DataReader(ticker,'quandl',
                                dt.datetime(2017, 1, 1),
                                dt.datetime.now())
            except:
                graphs.append(html.H3(
                    'Data is not available for {}'.format(ticker),
                    style={'marginTop': 20, 'marginBottom': 20}
                ))
                continue

            candlestick = {
                'x': df.index,
                'open': df['Open'],
                'high': df['High'],
                'low': df['Low'],
                'close': df['Close'],
                'type': 'candlestick',
                'name': ticker,
                'legendgroup': ticker,
                'increasing': {'line': {'color': colorscale[0]}},
                'decreasing': {'line': {'color': colorscale[1]}}
            }
            bb_bands = bbands(df.Close)
            bollinger_traces = [{
                'x': df.index, 'y': y,
                'type': 'scatter', 'mode': 'lines',
                'line': {'width': 1, 'color': colorscale[(i*2) % len(colorscale)]},
                'hoverinfo': 'none',
                'legendgroup': ticker,
                'showlegend': True if i == 0 else False,
                'name': '{} - bollinger bands'.format(ticker)
            } for i, y in enumerate(bb_bands)]
            graphs.append(dcc.Graph(
                id=ticker,
                figure={
                    'data': [candlestick] + bollinger_traces,
                    'layout': {
                        'margin': {'b': 0, 'r': 10, 'l': 60, 't': 0},
                        'legend': {'x': 0}
                    }
                }
            ))

        return graphs

    return app

def bbands(price, window_size=10, num_of_std=5):
    rolling_mean = price.rolling(window=window_size).mean()
    rolling_std  = price.rolling(window=window_size).std()
    upper_band = rolling_mean + (rolling_std*num_of_std)
    lower_band = rolling_mean - (rolling_std*num_of_std)
    return rolling_mean, upper_band, lower_band


if __name__ == '__main__':
    app = _create_app()
    app.run_server()