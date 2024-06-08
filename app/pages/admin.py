"""
Admin page for system maintenance and monitoring.
"""
import pandas as pd
import datetime
import dash
import dash_bootstrap_components as dbc
from src.data_loading.main import AppDataManager
from src.utils import Logging, COLUMN
from src.app_components import (
    LeafletMapComponentManager,
    AdminComponentManager
)
from dash import dcc, dash_table
from src.plotting import CountIndicator

dash.register_page(
    __name__,
    path="/admin",
    title="tRacket Admin",
)

logger = Logging.get_console_logger(__name__)

### Data loading ###

data_manager = AppDataManager()
data_manager.load_and_format_locations()

### Layout ###
leaflet_manager = LeafletMapComponentManager(data_manager.locations)
admin_component_manager = AdminComponentManager()

def layout(**kwargs):
    map = leaflet_manager.get_map(style={"height": "50vh", "margin-bottom": "10px"})
    
    stats = []
    for device_id in data_manager.locations[COLUMN.DEVICEID]:
        device_stat = data_manager.load_and_format_location_stats(location_id=device_id)
        device_stat[COLUMN.DEVICEID] = device_id
        stats.append(device_stat)    
    stats = pd.concat(stats, axis=0, ignore_index=True)

    admin_df = pd.concat([stats, data_manager.locations], axis=1)
    admin_df = admin_df[[COLUMN.DEVICEID, COLUMN.LABEL, COLUMN.END, COLUMN.ACTIVE, COLUMN.COUNT, COLUMN.RADIUS]]
    admin_df = admin_df.sort_values(COLUMN.END, ascending=False)
    admin_df_plain = data_manager.data_formatter._enum_col_names_to_string(admin_df)
    
    limit = pd.Timestamp('now') + pd.Timedelta(-4, unit="H")
    limit += pd.Timedelta(-1, unit="H")

    table = dash_table.DataTable(
        data=admin_df_plain.to_dict('records'),
        sort_action='native',
        style_data_conditional=[
            {
                'if': {
                    'filter_query': f'{{end}} > {limit.isoformat()}',
                },
                'backgroundColor': '#2C7BB2',
                'color': 'white'
            },
        ]
        )

    plotter = CountIndicator(admin_df)
    location_count_fig = plotter.plot(title="Location Count")

    plotter = CountIndicator(admin_df[admin_df[COLUMN.ACTIVE] == True])
    active_count_fig = plotter.plot(title="Active Count")
    
    plotter = CountIndicator(admin_df[admin_df[COLUMN.END] > limit])
    sending_count_fig = plotter.plot(title="Sending Data")

    layout = dbc.Container(
        [
            admin_component_manager.get_navbar(),
            dbc.Row([dbc.Col([map])]),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=location_count_fig, config={"displayModeBar": False}, style={"height": "20vh"})),
                    dbc.Col(dcc.Graph(figure=active_count_fig, config={"displayModeBar": False}, style={"height": "20vh"})),
                    dbc.Col(dcc.Graph(figure=sending_count_fig, config={"displayModeBar": False}, style={"height": "20vh"})),
                ]
                ),
            dbc.Row([dbc.Col([table])])
        ]
    )
    
    return layout