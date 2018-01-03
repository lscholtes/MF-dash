from layout import *
from dash.dependencies import Input, Output

# Here, we list those variables that we consider 'important', and should be primarily shown in variable selection:
important_vars = ['Amount Disbursed (Month) Tk.', 'Current Borrowers', 'Current OD/OS ratio (Monthly)',
                  'General Savings (Month) Tk.', ]
important_vars = [{'label': i, 'value': i} for i in important_vars]


@app.callback(Output('variable','value'),[Input('show_all_opts','values')])
def update_primary_variable_options(show_all_opts):
    if 'show_all' in show_all_opts:
        return variable_options[0]['value']
    else:
        return important_vars[0]['value']


@app.callback(Output('variable','options'),[Input('show_all_opts','values')])
def update_primary_variable_options(show_all_opts):
    if 'show_all' in show_all_opts:
        return variable_options
    else:
        return important_vars
