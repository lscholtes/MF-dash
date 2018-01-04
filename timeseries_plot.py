# Callbacks to update time-series graph
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
from scipy import stats

from layout import *
from filter_df import *

import rpy2.robjects.packages as rpackages
import rpy2.robjects as robjects
from rpy2.robjects.vectors import StrVector

# Preload/install packages for ARIMA forecasting
base = rpackages.importr('base')
utils = rpackages.importr('utils')
package_names = ('stats', 'forecast')
names_to_install = [x for x in package_names if not rpackages.isinstalled(x)]
utils.chooseCRANmirror(ind=1) # select the first mirror in the list
if len(names_to_install) > 0:
    utils.install_packages(StrVector(names_to_install))
stats_r = rpackages.importr('stats')
forecast = rpackages.importr('forecast')


# Define function to make linear predictions. Here, y is an array of response variables, and t is an array of
# DateTimeIndex objects corresponding to the entries in y.
def linear_prediction(y, t, forecast_look_back, forecast_look_ahead, name):
    if not forecast_look_back == 'all':
        if len(y) > forecast_look_back:
            y = y[-forecast_look_back:]
            t = t[-forecast_look_back:]
    delta_t = (t - pd.to_datetime(t[0])).days.values  # Work in 'number of days since first relevant date'
    delta_t = np.append(delta_t, delta_t[-1] + [31 * (i + 1) for i in range(forecast_look_ahead)])

    # Fit linear model based on delta_t values
    gradient, intercept, r_value, p_value, std_err = stats.linregress(delta_t[:len(t)], y)
    # Make prediction based on delta_t values
    y_star = [intercept + gradient * i for i in delta_t]
    # Convert delta_t values to valid dateTimeIndex
    delta_t = pd.to_timedelta(delta_t, unit='D')
    t = t[0] + delta_t

    return go.Scatter(x=t,
                      y=y_star,
                      text='Trend ({})'.format(name),
                      name='Trend ({})'.format(name),
                      mode='lines')


# Define function for ARIMA prediction. Prediction is based on the 'auto.arima' and 'forecast' functions from the
# 'forecast' package in R. Interaction with R is through rpy2.
# This function takes an array y of response variables, and an array t of DateTimeIndex objects. It returns a go.Scatter
# object corresponding to the ARIMA prediction.
def arima_prediction(y, t, forecast_look_ahead, name, ci_color):

    # Get the necessary DateTimeIndex values for the forecast...
    delta_t = np.append(0, [31 * (i + 1) for i in range(forecast_look_ahead)])  # Day gaps between forecast dates
    delta_t = pd.to_timedelta(delta_t, unit='D')  # Convert to DateTime timedelta object
    t_future = t[-1] + delta_t  # Get future dates by adding delta_t to last observed date in t

    # Import functions required for ARIMA model from R
    auto_arima = robjects.r('auto.arima')  # auto.arima function from forecast package
    as_ts = robjects.r('ts')  # time-series class from stats package
    forecast_fn = robjects.r('forecast')  # forecast function from forecast package

    y_r = robjects.FloatVector(y)  # Define y_r as a float vector copy of y in the R environment
    y_r = as_ts(y_r, frequency=12)  # Convert y_r to a time-series object
    arima_model = auto_arima(y_r)  # Fit ARIMA model
    fc = forecast_fn(arima_model, h=forecast_look_ahead)  # Forecast based on fitted ARIMA model

    mean = np.array(fc.rx2('mean'))  # The mean of the ARIMA forecast
    upper_80 = [x[0] for x in np.array(fc.rx2('upper'))]  # Upper bound of 80% confidence interval
    lower_80 = [x[0] for x in np.array(fc.rx2('lower'))]  # Lower bound of 80% confidence interval

    traces = [go.Scatter(y=np.append(y[-1],mean),
                         x=t_future,
                         name='Forecast ({})'.format(name),
                         text='Forecast ({})'.format(name),
                         mode='lines+markers'
                         ),
              go.Scatter(y=np.append(y[-1], upper_80),
                         x=t_future,
                         mode='lines',
                         name='Upper',
                         text='Lower ({})'.format(name),
                         showlegend=False,
                         line=dict(
                             color=ci_color,
                             )
                         ),
              go.Scatter(y=np.append(y[-1], lower_80),
                         x=t_future,
                         mode='lines',
                         name='Lower',
                         text='Lower ({})'.format(name),
                         showlegend=False,
                         line=dict(
                             color=ci_color,
                            )
                         )
              ]

    return traces


# Updates graph div width depending on whether scatter plot is present
@app.callback(Output('main_graph_div', 'style'),
              [Input('sec_variable', 'value')])
def update_graph_div(sec_variable):
    if not sec_variable:
        return {'width': '100%', 'display': 'inline-block'}
    else:
        return {'display': 'none'}


# Hide mean overlay options when second DRAB is active
@app.callback(Output('mean_overlay_options', 'style'),
              [Input('drab_tabs', 'value')])
def hide_mean_overlay(value):
    if value == 1:
        return {'padding-bottom': 10, 'padding-left': 8, 'backgroundColor': colors['BRAC pink']}
    else:
        return {'display': 'none'}

# Updates the actual graph
@app.callback(
    Output(component_id='main_graph', component_property='figure'),
    [Input('variable', 'value'),
     Input('timeframe', 'value'),
     Input('division', 'value'),
     Input('region', 'value'),
     Input('area', 'value'),
     Input('branch', 'value'),
     Input('mean_options', 'values'),
     Input('forecast_options', 'values'),
     Input('drab_tabs', 'value'),
     Input('division2', 'value'),
     Input('region2', 'value'),
     Input('area2', 'value'),
     Input('branch2', 'value'),
     Input('forecast_look_ahead', 'value'),
     Input('forecast_look_back', 'value')])
def update_graph(variable, timeframe, division, region, area, branch, mean_options, forecast_options,
                 drab_tabs, division2, region2, area2, branch2, forecast_look_ahead, forecast_look_back):
    # Check that we don't have an erroneous division->region->area->branch specification,
    # e.g. division = x1, region = none, area = none, branch = x2

    t = dates

    # Aggregate data at the relevant level
    df = filter_df([variable], drab=[division, region, area, branch], agg_type='mean')
    y = df['data'].values[0]
    name = df['name']

    t = t[timeframe[0]:timeframe[1]]
    y = y[timeframe[0]:timeframe[1]]

    traces = [go.Scatter(
        x=t,
        y=y,
        text=name,
        name=name,
        mode='lines+markers')]

    # Forecasting options:

    if 'linear_pred' in forecast_options:
        traces.append(linear_prediction(y, t, forecast_look_back, forecast_look_ahead, name))

    if 'arima_pred' in forecast_options:
        mean, upper_80, lower_80 = arima_prediction(y, t, forecast_look_ahead, name, 'rgba(255, 127, 14, 0.5)')
        traces.append(mean)
        traces.append(upper_80)
        traces.append(lower_80)

    # Compare to another DRAB?
    if drab_tabs == 2:
        df = filter_df([variable], drab=[division2, region2, area2, branch2], agg_type='mean')
        y = df['data'].values[0]
        name = df['name']

        y = y[timeframe[0]:timeframe[1]]

        traces.append(go.Scatter(
            x=t,
            y=y,
            text=name,
            name=name,
            mode='lines+markers'
        ))

        # Add linear prediction?
        if 'linear_pred' in forecast_options:
            traces.append(linear_prediction(y, t, forecast_look_back, forecast_look_ahead, name))

        # Add ARIMA prediction?
        if 'arima_pred' in forecast_options:
            mean, upper_80, lower_80 = arima_prediction(y, t, forecast_look_ahead, name, 'rgba(255, 127, 14, 0.5)')
            traces.append(mean)
            traces.append(upper_80)
            traces.append(lower_80)

    # Global/Divisional/Regional/Area mean option:
    if np.any([i in mean_options for i in ['glbm', 'divm', 'regm', 'arem']]):

        df = df_main[df_main['variable'].isin([variable])]

        # Global mean
        if 'glbm' in mean_options and division != 'Global':
            y = df.mean()[1:]
            traces.append(go.Scatter(
                x=t,
                y=y[timeframe[0]:timeframe[1]],
                text='Global',
                name='Global',
                mode='lines+markers'))

        # Divisional mean
        if 'divm' in mean_options and region and division:
            y = filter_df([variable], [division, None, None, None], 'mean')['data']
            y = y.values[0]
            traces.append(go.Scatter(
                x=t,
                y=y[timeframe[0]:timeframe[1]],
                text=division,
                name=division,
                mode='lines+markers'))

        # Regional mean
        if 'regm' in mean_options and area and region and division:
            y = filter_df([variable], [division, region, None, None], 'mean')['data']
            y = y.values[0]
            traces.append(go.Scatter(
                x=t,
                y=y[timeframe[0]:timeframe[1]],
                text=region,
                name=region,
                mode='lines+markers'))

        # Area mean
        if 'arem' in mean_options and branch and area and region and division:
            y = filter_df([variable], [division, region, area, None], 'mean')['data']
            y = y.values[0]
            traces.append(go.Scatter(
                x=t,
                y=y[timeframe[0]:timeframe[1]],
                text=area,
                name=area,
                mode='lines+markers'))

    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={'title': 'Month'},
            yaxis={'title': variable},
            margin={'l': 60, 'b': 60, 't': 20, 'r': 20},
            hovermode='closest')
    }