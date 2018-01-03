import pandas as pd

# Load data and branchlist for reference of function
df_main = pd.read_csv('../../Documents/BRAC/MF/MF Branch Data/Data/dabi_global.csv')
df_main = df_main[df_main.columns[1:]]
branchlist = pd.read_csv('../../Documents/BRAC/MF/MF Branch Data/Data/branchlist.csv')


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
