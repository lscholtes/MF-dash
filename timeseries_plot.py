# Callbacks to update time-series graph
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
from scipy import stats

from layout import *
from filter_df import *

# Updates graph div width depending on whether scatter plot is present
@app.callback(Output('main_graph_div', 'style'),
              [Input('sec_variable', 'value')])
def update_graph_div(sec_variable):
    if not sec_variable:
        return {'width': '100%', 'float': 'left', 'display': 'inline-block'}
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
     Input('drab_tabs','value'),
     Input('division2', 'value'),
     Input('region2','value'),
     Input('area2','value'),
     Input('branch2','value')])
def update_graph(variable, timeframe, division, region, area, branch, mean_options, forecast_options,
                 drab_tabs, division2, region2, area2, branch2):
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
        # Linear prediction based on last 12 months. TODO - add option to predict based on other timeframes.
        t_copy = t  # Make a copy of the original t for later
        if len(y) > 12:
            y = y[-12:]
            t = t[-12:]
        delta_t = (t - pd.to_datetime(t[0])).days.values # Need to convert t to a number!
        delta_t = np.append(delta_t, delta_t[-1]+[31*(i+1) for i in range(6)])  # predict 6 months ahead...
        print delta_t

        # Fit linear model based on delta_t values
        gradient, intercept, r_value, p_value, std_err = stats.linregress(delta_t[:len(t)], y)
        print gradient, intercept, r_value, p_value, std_err

        # Make prediction based on delta_t values
        # y_star = [intercept + gradient * i for i in delta_t[len(t):]]
        y_star = [intercept + gradient * i for i in delta_t]
        print y_star

        # Concatenate past and future values of y
        # y = np.append(y, y_star)

        # Convert delta_t values to valid dateTimeIndex
        delta_t = pd.to_timedelta(delta_t, unit='D')
        print delta_t

        t = t[0] + delta_t
        print t

        # Add the fitted line to the plot

        traces.append(go.Scatter(
            x=t,
            y=y_star,
            text='Linear Forecast',
            name='Linear Forecast',
            mode='lines'
        ))

        t = t_copy  # Reset t to the original t copied earlier.

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