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
#########


# The dependency structure is as follows.
# The layout.py module initialises the dash object as a global variable app, and assigns the layout options to app.
# This module, and the global app variable, are imported into each of the callback specifier modules below in order to
# define the callback attributes of app. Finally, app, along with its layout attributes and callback attributes, is
# imported into dash_main.py.


from drab_specifier import *  # Import drab specifier callbacks
from timeseries_plot import *  # Import time-series plot callbacks
from scatter_plot import *  # Import scatter plot callbacks
from at_a_glance import * # Import at-a-glance callbacks


if __name__ == '__main__':
    app.run_server(debug=True)
