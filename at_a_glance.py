from layout import *
from dash.dependencies import Input, Output
from filter_df import *


# Callback to update At-a-glance information


@app.callback(Output('at_a_glance', 'children'),
              [Input('division', 'value'),
               Input('region', 'value'),
               Input('area', 'value'),
               Input('branch', 'value'),
               Input('drab_tabs', 'value'),
               Input('division2', 'value'),
               Input('region2', 'value'),
               Input('area2', 'value'),
               Input('branch2', 'value')])
def update_at_a_glance(division, region, area, branch, drab_tabs, division2, region2, area2, branch2):

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

    # If only one DRAB is selected
    if drab_tabs == 1:
        # Create the html Div to be returned
        return html.Div([
            html.Table(
                [html.Tr([
                    html.Th([html.P('At-a-Glance: ', style={'display': 'inline', 'font-weight': 'normal'}),
                             html.P(name,style={'display': 'inline'})]),
                    html.Th('Annual Change', style={'text-align': 'right'})
                ])] +
                [html.Tr([
                    html.Td('Current Borrowers'),
                    html.Td('{0:.3g}%'.format(pc_change[2]), style={'text-align': 'right'})
                ]),
                    html.Tr([
                        html.Td('Monthly Disbursement'),
                        html.Td('{0:.3g}%'.format(pc_change[3]), style={'text-align': 'right'})
                    ]),
                    html.Tr([
                        html.Td('Current OD/OS%'),
                        html.Td('{0:.3g}%'.format(pc_change[0]), style={'text-align': 'right'})
                    ]),
                    html.Tr([
                        html.Td('Total OD/OS% [Excl. NL2]'),
                        html.Td('{0:.3g}%'.format(pc_change[1]), style={'text-align': 'right'})
                    ])
                ],
                style={'width': '100%'})
        ], style={'margin-left': 15, 'margin-bottom': 15, 'margin-right': 15})
    # If two DRABs are selected, return % change of vars for both drabs
    else:
        # We first calculate the % changes for the second DRAB too

        y = filter_df(rel_vars, [division2, region2, area2, branch2], 'sum')
        name2 = y['name']
        y = y['data']

        # Calculate current OD/OS ratio
        current_od = y.loc[rel_vars[0]].values
        current_os = y.loc[rel_vars[1]].values
        current_odos = [i / j for i in current_od for j in current_os]

        # Calculate total OD/OS ratio
        od = y.loc[rel_vars[2]].values
        os = y.loc[rel_vars[3]].values
        odos = [i / j for i in od for j in os]

        # Values at present
        present2 = [current_odos[-1],  # Current ODOS
                    odos[-1],  # Total ODOS
                    y.loc[rel_vars[4]].values[-1],  # Current borrowers
                    y.loc[rel_vars[5]].values[-1]  # Monthly disbursement
                    ]

        # Percentage change in values over last 12 months
        pc_change2 = [100 * (current_odos[-1] - current_odos[-12]) / current_odos[-12],
                      100 * (odos[-1] - odos[-12]) / odos[-12],
                      100 * (y.loc[rel_vars[4]].values[-1] - y.loc[rel_vars[4]].values[-12]) /
                      y.loc[rel_vars[4]].values[-12],
                      100 * (y.loc[rel_vars[5]].values[-1] - y.loc[rel_vars[5]].values[-12]) /
                      y.loc[rel_vars[5]].values[-12]
                      ]

        return html.Div([
            html.Table(
                [html.Tr([
                    html.Th([html.P('Annual change in: ', style={'display': 'inline', 'font-weight': 'normal'})]),
                    html.Th(name, style={'text-align': 'right'}),
                    html.Th(name2, style={'text-align': 'right'})
                ])] +
                [html.Tr([
                    html.Td('Current Borrowers'),
                    html.Td('{0:.3g}%'.format(pc_change[2]), style={'text-align': 'right'}),
                    html.Td('{0:.3g}%'.format(pc_change2[2]), style={'text-align': 'right'})
                ]),
                    html.Tr([
                        html.Td('Monthly Disbursement'),
                        html.Td('{0:.3g}%'.format(pc_change[3]), style={'text-align': 'right'}),
                        html.Td('{0:.3g}%'.format(pc_change2[3]), style={'text-align': 'right'})
                    ]),
                    html.Tr([
                        html.Td('Current OD/OS%'),
                        html.Td('{0:.3g}%'.format(pc_change[0]), style={'text-align': 'right'}),
                        html.Td('{0:.3g}%'.format(pc_change2[0]), style={'text-align': 'right'})
                    ]),
                    html.Tr([
                        html.Td('Total OD/OS% [Excl. NL2]'),
                        html.Td('{0:.3g}%'.format(pc_change[1]), style={'text-align': 'right'}),
                        html.Td('{0:.3g}%'.format(pc_change2[1]), style={'text-align': 'right'})
                    ])
                ],
                style={'width': '100%'})
        ], style={'margin-left': 15, 'margin-bottom': 15, 'margin-right': 15})