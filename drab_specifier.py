from dash.dependencies import Input, Output
from layout import *  # We import layout (and initialize app) from layout.py

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