import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

global app
app = dash.Dash()

# Preliminary data loading, extracting DRAB names, etc.
df_main = pd.read_csv('../../Documents/BRAC/MF/MF Branch Data/Data/dabi_global.csv')
df_main = df_main[df_main.columns[1:]]
branchlist = pd.read_csv('../../Documents/BRAC/MF/MF Branch Data/Data/branchlist.csv')
dates = pd.date_range('2012/01/01', freq='M', periods=12 * 5 + 9)


variable_names = df_main['variable'].unique()
variable_options = [{'label': variable_names[i], 'value': variable_names[i]} for i in range(len(variable_names))]
agg_level_names = branchlist.columns
agg_level_options = [{'label': agg_level_names[i], 'value': agg_level_names[i]} for i in range(len(agg_level_names))]
division_options = [{'label': k, 'value': k} for k in branchlist['Division'].unique()]
division_options.append({'label': 'Global', 'value': 'Global'})

# Custom CSS styling
app.css.append_css({'external_url': 'https://codepen.io/luke-scholtes/pen/xprjoK.css'})

colors = {
    'dark-grey': '#111111',
    'mid-grey': '#5b5b5b',
    'light-grey': '#dddddd',
    'white': '#ffffff',
    'schauss pink': '#ffa5b1',
    'english vermillion': '#cc444bb',
    'jelly bean': '#da5552',
    'tango pink': '#df7373',
    'jet': '#32292f',
    'independence': '#575366',
    'shadow blue': '#6e7dab',
    'gainsboro': '#d1e3dd',
    'BRAC pink': '#d10074',
    'light BRAC pink': '#ed0083'
}

# Dash layout
app.layout = html.Div(style={'font-family': 'Verdana, sans-serif'},
                      children=[
    # Upper Div
    html.Div([

        # Define Location
        html.Div([
            # Tabs
            html.Div([
                dcc.Tabs(
                    tabs=[
                        {'label': 'Single', 'value': 1},
                        {'label': 'Compare', 'value': 2}
                    ],
                    id='drab_tabs',
                    value=1
                )
            ]),
            # DRAB selection
            html.Div([
                # DRAB, text only
                html.Div([
                    html.Div(['Division'], style={'display': 'block', 'margin-top': 0}),
                    html.Div(['Region'], style={'display': 'block', 'margin-top': 20}),
                    html.Div(['Area'], style={'display': 'block', 'margin-top': 20}),
                    html.Div(['Branch'], style={'display': 'block', 'margin-top': 20})
                ],
                    style={'width': '15%', 'color': colors['white'], 'display': 'inline-block', 'vertical-align': 'middle'}),
                # Primary DRAB dropdown
                html.Div([
                    html.Div([
                        dcc.Dropdown(id='division',
                                     options=division_options,
                                     value='Global')],
                            style={'display': 'block', 'vertical-align': 'middle', 'margin-top': 3}),
                    html.Div([
                        dcc.Dropdown(id='region')],
                            style={'display': 'block', 'vertical-align': 'middle', 'margin-top': 3}),
                    html.Div([
                            dcc.Dropdown(id='area')],
                            style={'display': 'block', 'vertical-align': 'middle', 'margin-top': 3}),
                    html.Div([
                            dcc.Dropdown(id='branch')],
                            style={'display': 'block', 'vertical-align': 'middle', 'margin-top': 3})
                ],
                    id='primary_drab',
                    ),
                # Secondary DRAB dropdown
                html.Div([
                    html.Div([
                        dcc.Dropdown(id='division2',
                                     options=division_options,
                                     value='Global')],
                            style={'display': 'block', 'vertical-align': 'middle', 'margin-top': 3}),
                    html.Div([
                            dcc.Dropdown(id='region2')],
                            style={'display': 'block', 'vertical-align': 'middle', 'margin-top': 3}),
                    html.Div([
                            dcc.Dropdown(id='area2')],
                            style={'display': 'block', 'vertical-align': 'middle', 'margin-top': 3}),
                    html.Div([
                            dcc.Dropdown(id='branch2')],
                            style={'display': 'block', 'vertical-align': 'middle', 'margin-top': 3})
                ],
                    id='secondary_drab',
                    )
            ])
        ],
            style={'width': '35%', 'display': 'inline-block', 'margin-top': 10, 'margin-bottom': 10, 'margin-left': 10}),

        # Variable Selection
        html.Div([
            # Primary Variable
            html.Div([
                html.Div('Variable:', style={'color': colors['white']}),
                dcc.Dropdown(id='variable',
                             options=variable_options,
                             value=variable_options[0]['value']),
                dcc.Checklist(id='show_all_opts',
                              options=[{'label': 'Show all', 'value': 'show_all'}],
                              values=[],
                              style={'color': colors['white']})],
                style={'margin-bottom': 20}),
            # Secondary Variable
            html.Div([
                html.Div('Secondary Variable:', style={'color': colors['white']}),
                dcc.Dropdown(id='sec_variable',
                             options=variable_options,
                             value=None)])
        ], style={'width': '20%', 'vertical-align': 'center', 'display': 'inline-block', 'margin-left': 30,
                  'margin-bottom': 10, 'margin-top': 10}),

        # Primary location basic information
        html.Div(
            id='at_a_glance',
            style={'width': '40%', 'display': 'inline-block', 'vertical-align': 'bottom', 'float': 'right',
                   'backgroundColor': colors['BRAC pink'], 'color': colors['white'], 'margin-bottom': 10,
                   'margin-top': 10, 'margin-right': 10})

    ],
        style={'width': '100%', 'backgroundColor': colors['light BRAC pink']}),

    # Split div (aesthetic)
    # html.Hr(
    #          style={'height': 10, 'margin-bottom': 10, 'backgroundColor': colors['light-grey'],
    #                 'width': '100%', 'border': 'none'}),


    # Graphs
    html.Div([
        # Time-Series graph + options + timeframe
        html.Div([
            # Timeframe selector
            html.Div([
                dcc.RangeSlider(id='timeframe',
                                marks={i: dates[i] for i in range(len(dates)) if i % 12 == 0},
                                min=0,
                                max=len(dates),
                                value=[0, len(dates)]),
            ],
                style={'margin-bottom': 20, 'margin-left': 40, 'margin-right': 40}),
            # Graph + options
            html.Div([
                # Overlay options
                html.Div([
                    # Mean overlay options
                    html.Div([
                        html.Div(['Average:'], style={'font-weight': 'bold', 'color': colors['white']}),
                        dcc.Checklist(id='mean_options',
                                      options=[{'label': 'Global', 'value': 'glbm'},
                                               {'label': 'Division', 'value': 'divm'},
                                               {'label': 'Region', 'value': 'regm'},
                                               {'label': 'Area', 'value': 'arem'}],
                                      values=[],
                                      style={'display': 'block', 'color': colors['white']})
                    ],
                        id='mean_overlay_options',
                        style={'padding-bottom': 10, 'padding-left': 8, 'backgroundColor': colors['BRAC pink']}),
                    # Forecast options
                    html.Div([
                        html.Div(['Forecast:'], style={'font-weight': 'bold', 'color': colors['white']}),
                        dcc.Checklist(id='forecast_options',
                                      options=[  # {'label': 'Smoothing', 'value': 'smth'},
                                          {'label': 'Linear', 'value': 'linear_pred'},
                                          {'label': 'ARIMA', 'value': 'arima_pred'}],
                                      values=[],
                                      style={'color': colors['white']}),
                        html.P(['Forecast for'], style={'color': colors['white']}),
                        html.Div([
                            dcc.Dropdown(id='forecast_look_ahead',
                                         options=[{'label': i, 'value': i} for i in [3, 6, 9, 12]],
                                         value=3)],
                                 style={'width': '50%'}),
                        html.P(['months, based on past'], style={'color': colors['white']}),
                        html.Div([
                            dcc.Dropdown(id='forecast_look_back',
                                         options=[{'label': i, 'value': i} for i in [3, 6, 12, 24, 'all']],
                                         value=6)],
                                 style={'width': '50%'}),
                        html.P(['months.'], style={'color': colors['white']})
                    ],
                        style={'padding-bottom': 10, 'padding-left': 8, 'backgroundColor': colors['light BRAC pink']})
                ],
                    style={'width': '13%', 'display': 'inline-block', 'vertical-align': 'top',
                           'margin-top': 20}),

                # Main time series graph
                html.Div([
                    dcc.Graph(id='main_graph')
                ],
                    style={'width': '87%', 'display': 'inline-block'})

            ])
        ], id='main_graph_div'),
        # Scatter plot + options
        html.Div([
            # Scatter plot options
            dcc.Checklist(id='scatter_options',
                          options=[{'label': 'R-Squared (Scatter)', 'value': 'rsquare'},
                                   {'label': 'Quantile Trim', 'value': 'quant_trim'}],
                          values=['quant_trim']),
            # Scatter plot
            dcc.Graph(id='scatter_graph'),
            html.Div(id='lin_regn_coeffs', style={'margin-top': 10})
        ], id='scatter_graph_div')
    ],
        style={'width': '100%', 'margin-top': 10}),

    # Hidden divs for variable/data sharing between callback functions
    html.Div(id='scatter_calc', style={'display': 'none'}),  # Data loading/calculations for scatter plot
])