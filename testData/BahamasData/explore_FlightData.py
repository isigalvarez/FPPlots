# !usr/bin/env python3
# ===========================================================
# Created on 18/04/2019
# This script tries to plot the flight data on an interactive
# map using bokeh.
#
# (!!!) Not remotely finished!
# ===========================================================

from bokeh.plotting import figure, show, output_file, reset_output
from bokeh.tile_providers import STAMEN_TERRAIN

from bokeh.plotting import figure, save
from bokeh.models import ColumnDataSource, HoverTool, LogColorMapper
import geopandas as gpd
import pysal as ps

from bokeh.palettes import RdYlBu11 as palette
from bokeh.models import LogColorMapper

# Create the figure specifying mercator get latitude and longitude
p = figure(x_range=(-6000000, 3000000), y_range=(-100000, 4000000),
           x_axis_type="mercator", y_axis_type="mercator")
# Add the background map
p.add_tile(STAMEN_TERRAIN)
# Save the figure
save(p)
# Reset the output to keep things clean
reset_output()