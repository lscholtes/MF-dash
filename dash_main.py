#########
# TODO:
# - Add some sort of div/reg/area/branch ranking indicator for performance comparison of each variable
# - Add basic summary information for each div/reg/area/branch e.g. current OD/OS, total members, etc.
# - Add the possibility to compare arbitrary div/reg/area/branches (DRAB) in a single time-series plot? -> Drag-n-drop
# kinda thing.
# -> Perhaps we could add another row of DRAB selectors, which is in a html div that is hidden unless 'activated' by
# a callback which changes the div style settings when we click an 'add' button? -> This would give us a way to select
# a further DRAB!
# - Add a 'selector' tool to find branches that fulfill some criterion, e.g. all branches with current OD/OS in the top
# 95% percentile.
#

from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
from scipy import stats
import json

from layout import *  # We import layout (and initialize app) from layout.py

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


# Callbacks to show/hide secondary DRAB selector


@app.callback(
    Output('primary_drab', 'style'),
    [Input('drab_tabs', 'value')])
def adjust_primary_drab(value):
    if value == 1: # Only primary drab selector -> width = 85%
        return {'display': 'inline-block', 'width': '85%', 'vertical-align': 'middle'}
    else: # Both drab selectors -> width: 42.5%
        return {'display': 'inline-block', 'width': '42.5%', 'vertical-align': 'middle'}


@app.callback(
    Output('secondary_drab', 'style'),
    [Input('drab_tabs', 'value')])
def show_secondary_drab(value):
    if value == 1: # Hide secondary drab selector
        return {'display': 'none'}
    else: # Show secondary drab selector
        return {'display': 'inline-block', 'width': '42.5%', 'vertical-align': 'middle'}


# Callbacks to update location specifier dropdowns:


@app.callback(
    Output('region', 'options'),
    [Input('division', 'value')])
def update_region(input_value):
    foo = branchlist[branchlist['Division'].isin([input_value])]
    return [{'label': x, 'value': x} for x in foo['Region'].unique()]


@app.callback(
    Output('area', 'options'),
    [Input('region', 'value'),
     Input('division', 'value')])
def update_area(region, division):
    foo = branchlist[branchlist['Division'].isin([division])]
    foo = foo[foo['Region'].isin([region])]
    return [{'label': x, 'value': x} for x in foo['Area'].unique()]


@app.callback(
    Output('branch', 'options'),
    [Input('area', 'value'),
     Input('region', 'value'),
     Input('division', 'value')])
def update_branch(area, region, division):
    foo = branchlist[branchlist['Division'].isin([division])]
    foo = foo[foo['Region'].isin([region])]
    foo = foo[foo['Area'].isin([area])]
    return [{'label': x, 'value': x} for x in foo['Branch'].unique()]


# Function that filters df based on list of variable names, aggregates df based on a DRAB list (either as sum or mean)
# We want the last value of division->region->area->branch that is non-empty AND is compatible with
# previous entries!!! -> If we do not check the second condition then updating the graph may fail.

def filter_df(var_names, drab, agg_type, return_all=False): # agg_type = 'sum' or 'mean', var_names and drab are lists
    # drab MUST have length = 4, missing entries are filled by None.
    # return_all is a boolean. If true, filter_df returns the aggregated variable values for ALL locations within the
    # target DRAB hierarchy.

    division, region, area, branch = drab

    # First, filter the dataframe, so that only the relevant variables are being considered
    y = df_main[df_main['variable'].isin(var_names)]
    y = pd.merge(branchlist, y, on='branch_code')

    name = 'foo'

    if division == 'Global':
        if agg_type == 'mean':
            y = y.groupby('variable').mean()
        else:
            y = y.groupby('variable').sum()
        y = y[y.columns[1:]]
        name = division

    else:
        # Filter at division level.
        # The following condition checks whether the value of region is valid, given the value of division.
        # If it is not, then we aggregate by division.
        if not region or not pd.Series(region).isin(
                branchlist[branchlist['Division'].isin([division])]['Region']).bool():
            if agg_type == 'mean':
                y = y.groupby(['Division', 'variable']).mean()
            else:
                y = y.groupby(['Division', 'variable']).sum()
            y = y[y.columns[1:]]  # Delete the first column, since this is the mean of branch_code
            if not return_all:
                y = y.loc[[(division, i) for i in var_names]]
                y = y.loc[division] # This deletes the first redundant entry of the multiIndex
            name = division

        # Filter at region level.
        # Check whether value of area is valid, given value of region. If not, aggregate by region.
        elif not area or not pd.Series(area).isin(branchlist[branchlist['Region'].isin([region])]['Area']).bool():
            y = y.loc[y['Division'].isin([division])]
            if agg_type == 'mean':
                y = y.groupby(['Region', 'variable']).mean()
            else:
                y = y.groupby(['Region', 'variable']).sum()
            y = y[y.columns[1:]]
            if not return_all:
                y = y.loc[[(region, i) for i in var_names]]
                y = y.loc[region]
            name = region

        # Filter at area level.
        elif not branch or not pd.Series(branch).isin(branchlist[branchlist['Area'].isin([area])]['Branch']).bool():
            y = y.loc[y['Division'].isin([division])]
            y = y.loc[y['Region'].isin([region])]
            if agg_type == 'mean':
                y = y.groupby(['Area', 'variable']).mean()
            else:
                y = y.groupby(['Area', 'variable']).sum()
            y = y[y.columns[1:]]
            if not return_all:
                y = y.loc[[(area, i) for i in var_names]]
                y = y.loc[area]
            name = area

        # Filter at branch level.
        elif branch:
            y = y.loc[y['Division'].isin([division])]
            y = y.loc[y['Region'].isin([region])]
            y = y.loc[y['Area'].isin([area])]
            if agg_type == 'mean':
                y = y.groupby(['Branch', 'variable']).mean()
            else:
                y = y.groupby(['Branch', 'variable']).sum()
            y = y[y.columns[1:]]
            if not return_all:
                y = y.loc[[(branch, i) for i in var_names]]
                y = y.loc[branch]
            name = branch

    return {'name': name, 'data': y}


# Callback to update At-a-glance information


@app.callback(Output('at_a_glance', 'children'),
              [Input('division', 'value'),
               Input('region', 'value'),
               Input('area', 'value'),
               Input('branch', 'value')])
def update_at_a_glance(division, region, area, branch):

    # Stats to be calculated:
    # - Current borrowers
    # - Disbursement
    # - Current OD/OS
    # - OD/OS
    # - % change over last 12 months for all above stats

    # TODO: Add a column to the table giving the ranking for each variable, e.g. south west has 4th best OD/OS ratio
    # of all divisions!

    # List of variables we require for at-a-glance info
    rel_vars = ['Current OD Tk.', 'Total Current OS Tk.',
                'Total OD [Excl.NL2] Tk.', 'Total OS [Excl.NL2] Tk.',
                'Current Borrowers', 'Amount Disbursed (Month) Tk.']

    # Filter + aggregate data
    y = filter_df(rel_vars, [division, region, area, branch], 'sum')
    name = y['name']
    y = y['data']

    # Calculate current OD/OS ratio
    current_od = y.loc[rel_vars[0]].values
    current_os = y.loc[rel_vars[1]].values
    current_odos = [i/j for i in current_od for j in current_os]

    # Calculate total OD/OS ratio
    od = y.loc[rel_vars[2]].values
    os = y.loc[rel_vars[3]].values
    odos = [i/j for i in od for j in os]

    # Values at present
    present = [current_odos[-1],  # Current ODOS
               odos[-1],  # Total ODOS
               y.loc[rel_vars[4]].values[-1],  # Current borrowers
               y.loc[rel_vars[5]].values[-1]  # Monthly disbursement
    ]

    # Percentage change in values over last 12 months
    pc_change = [100 * (current_odos[-1] - current_odos[-12]) / current_odos[-12],
                 100 * (odos[-1]-odos[-12]) / odos[-12],
                 100 * (y.loc[rel_vars[4]].values[-1] - y.loc[rel_vars[4]].values[-12]) /
                 y.loc[rel_vars[4]].values[-12],
                 100 * (y.loc[rel_vars[5]].values[-1] - y.loc[rel_vars[5]].values[-12]) /
                 y.loc[rel_vars[5]].values[-12]
                 ]

    # Create the html Div to be returned
    return html.Div([
        html.Table(
            [html.Tr([
                html.Th([html.P('At-a-Glance: ',style={'display': 'inline', 'font-weight': 'normal'}),
                         html.P(name,style={'display':'inline'})]),
                html.Th('Present Value', style={'text-align': 'right'}),
                html.Th('Annual Change', style={'text-align': 'right'})
            ])] +
            [html.Tr([
                html.Td('Current Borrowers'),
                html.Td('{:,.0f}'.format(present[2]), style={'text-align': 'right'}),
                html.Td('{0:.3g}%'.format(pc_change[2]), style={'text-align': 'right'})
            ]),
                html.Tr([
                    html.Td('Monthly Disbursement'),
                    html.Td('{:,.0f} Tk.'.format(present[3]), style={'text-align': 'right'}),
                    html.Td('{0:.3g}%'.format(pc_change[3]), style={'text-align': 'right'})
                ]),
                html.Tr([
                    html.Td('Current OD/OS%'),
                    html.Td('{0:.3g}'.format(present[0]), style={'text-align': 'right'}),
                    html.Td('{0:.3g}%'.format(pc_change[0]), style={'text-align': 'right'})
                ]),
                html.Tr([
                    html.Td('Total OD/OS% [Excl. NL2]'),
                    html.Td('{0:.3g}'.format(present[1]), style={'text-align': 'right'}),
                    html.Td('{0:.3g}%'.format(pc_change[1]), style={'text-align': 'right'})
                ])
            ],
            style={'width': '100%'})
    ], style={'margin-left': 15, 'margin-bottom': 15, 'margin-right': 15})


# Callback to update time-series graph


# Updates graph div width depending on whether scatter plot is present
@app.callback(Output('main_graph_div', 'style'),
              [Input('sec_variable', 'value')])
def update_graph_div(sec_variable):
    if not sec_variable:
        return {'width': '100%', 'float': 'left', 'display': 'inline-block'}
    else:
        return {'width': '60%', 'float': 'left', 'display': 'inline-block'}


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


# Callback to do scatter plot calculations


@app.callback(Output('scatter_graph_div','style'),
              [Input('sec_variable','value')])
def update_scatter_div(sec_variable):
    if not sec_variable:
        return {'display': 'none'}
    else:
        return {'width': '40%', 'float': 'right', 'display': 'inline-block'}



@app.callback(
    Output(component_id='scatter_calc', component_property='children'),
    [Input('variable', 'value'),
     Input('sec_variable', 'value'),
     Input('division', 'value'),
     Input('region', 'value'),
     Input('area', 'value'),
     Input('branch', 'value'),
     Input('scatter_options', 'values')])
def update_scatter_calc(variable, sec_variable, division, region, area, branch, scatter_options):
    # Ensure that we have the value of sec_variable is not None
    if sec_variable:
        # Extract all data corresponding to 'variable' and 'sec_variable'

        df = df_main[df_main['variable'].isin([variable, sec_variable])]
        df = pd.merge(branchlist, df, on='branch_code')

        # We should make it clear that zero-entries correspond to mising values (this is generally the case...)
        df = df.replace({0: np.nan})

        # Now, filter out those branches that are not relevant to whatever DRAB is specified.
        if division=='Global':
            pass
        elif not region or not pd.Series(region).isin(
            branchlist[branchlist['Division'].isin([division])]['Region']).bool():
            df = df[df['Division'].isin([division])]
        elif not area or not pd.Series(area).isin(branchlist[branchlist['Region'].isin([region])]['Area']).bool():
            df = df[df['Division'].isin([division])]
            df = df[df['Region'].isin([region])]
        elif not branch or not pd.Series(branch).isin(branchlist[branchlist['Area'].isin([area])]['Branch']).bool():
            df = df[df['Division'].isin([division])]
            df = df[df['Region'].isin([region])]
            df = df[df['Area'].isin([area])]
        elif branch:
            df = df[df['Division'].isin([division])]
            df = df[df['Region'].isin([region])]
            df = df[df['Area'].isin([area])]
            df = df[df['Branch'].isin([branch])]

        x = df[df['variable'].isin([variable])]
        y = df[df['variable'].isin([sec_variable])]

        x = x.sort_values(by=['branch_code'])
        y = y.sort_values(by=['branch_code'])

        print x

        x = x[x.columns[7:]].values.tolist()
        y = y[y.columns[7:]].values.tolist()

        # Flatten the lists
        x = [item for sublist in x for item in sublist]
        y = [item for sublist in y for item in sublist]

        # We remove any (x,y) pairs containing at least one nan value
        x_copy = x
        x = [x[i] for i in range(len(x)) if (not np.isnan(x[i])) and (not np.isnan(y[i]))]
        y = [y[i] for i in range(len(y)) if (not np.isnan(x_copy[i])) and (not np.isnan(y[i]))]

        # Should we also remove outliers/extreme values? -> This would make the figure more informative/discernable.
        # -> Remove any (x,y) pairs where either x or y lies in the 99.5% percentile of their respective distributions.
        # -> TODO: Look into better ways of deciding whether values are outliers or not... e.g. Cook's distance?

        if 'quant_trim' in scatter_options:
            x_np = np.array(x)
            y_np = np.array(y)
            x_99pc = np.percentile(x_np, 99.5)
            y_99pc = np.percentile(y_np, 99.5)

            x_copy = x
            x = [x[i] for i in range(len(x)) if x[i] < x_99pc and y[i] < y_99pc]
            y = [y[i] for i in range(len(y)) if x_copy[i] < x_99pc and y[i] < y_99pc]

        traces = [go.Scattergl(x=x, y=y, mode='markers', marker=dict(size=5, opacity=.2))]

        output = {}

        if 'rsquare' in scatter_options:
            gradient, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            print 'gradient = {}'.format(gradient)
            x_min, x_max = [min(x), max(x)]
            traces.append(go.Scattergl(
                x=[x_min, x_max],
                y=[intercept + x_min * gradient, intercept + x_max * gradient],
                mode='lines',
                name='Linear Regression'))
            output['reg_coeffs'] = {'gradient': gradient, 'intercept': intercept, 'r_value': r_value,
                                    'p_value': p_value, 'std_err': std_err}

        output['data'] = traces
        output['layout'] = go.Layout(
            xaxis={'title': variable},
            yaxis={'title': sec_variable},
            margin={'l': 60, 'b': 60, 't': 20, 'r': 20},
            hovermode='closest',
            showlegend=False)

        return json.dumps(output)  # HTML div can only store string objects, so convert dictionary to JSON format


# Callback to update scatter plot


@app.callback(
    Output(component_id='scatter_graph', component_property='figure'),
    [Input('scatter_calc', 'children')])
def update_scatter_graph(scatter_calc):
    if not scatter_calc:  # Avoids errors on server start-up
        return {}
    scatter_calc = json.loads(scatter_calc) # Convert input from JSON back to dictionary
    return {'data': scatter_calc['data'], 'layout': scatter_calc['layout']}


# Callback to update regression coefficients


@app.callback(
    Output(component_id='lin_regn_coeffs', component_property='children'),
    [Input('scatter_calc', 'children')])
def update_reg_coeffs(scatter_calc):
    if not scatter_calc:  # Avoids errors on server start-up
        return []
    scatter_calc = json.loads(scatter_calc)
    if scatter_calc['reg_coeffs']:
        rc = scatter_calc['reg_coeffs']
        return [html.Div('Correlation = {0:.2g}'.format(rc['r_value'])),
                html.Div('Intercept = {0:.2g}'.format(rc['intercept'])),
                html.Div('Gradient = {0:.2g} (p = {1:.2g})'.format(rc['gradient'], rc['p_value']))]

if __name__ == '__main__':
    app.run_server(debug=True)
