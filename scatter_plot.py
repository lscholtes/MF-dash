# Callback to do scatter plot calculations
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
from scipy import stats
import json

from layout import *
from filter_df import *


@app.callback(Output('scatter_graph_div','style'),
              [Input('sec_variable','value')])
def update_scatter_div(sec_variable):
    if not sec_variable:
        return {'display': 'none'}
    else:
        return {'width': '100%', 'display': 'inline-block'}


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
            # noinspection PyTypeChecker
            x_99pc = np.percentile(x_np, 99.5)
            # noinspection PyTypeChecker
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