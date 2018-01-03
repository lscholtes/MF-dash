# main server initialisation script

# Import the callback function scripts (layout script is called within these scripts,
# so does not need to be called again).

from drab_specifier import *  # Import drab specifier callbacks
from timeseries_plot import *  # Import time-series plot callbacks
from scatter_plot import *  # Import scatter plot callbacks
from at_a_glance import * # Import at-a-glance callbacks
from variable_selection import *  # Import callbacks for variable selection options

if __name__ == '__main__':
    app.run_server()
