from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
import csv, os
from datetime import datetime
from tethys_sdk.services import get_spatial_dataset_engine
import urlparse

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    context = {}

    return render(request, 'grace/home.html', context)
    
    
@login_required
def home_graph(request, id):
    """
    Controller for home page to display a graph and map.
    """
    
    """
    SET UP THE MAP OPTIONS
    """   

    '''
    QUERY GEOSERVER TO GET THE LAYER CORRESPONDING TO ID
    THEN PARSE ONE OF THE URLS IN THE RESPONSE DICT TO GET
    THE BOUNDING BOX, THEN PARSE THE BOX TO GET LAT LONG TO
    PROPERLY CENTER THE MAP
    '''
    geoserver_engine = get_spatial_dataset_engine(name='default')
    response = geoserver_engine.get_layer(id, debug=False)
    kmlurl = response['result']['wms']['kml']
    parsedkml = urlparse.urlparse(kmlurl)
    bbox = urlparse.parse_qs(parsedkml.query)['bbox'][0]
    bboxitems = bbox.split(",")
    box_left = float(bboxitems[0])
    box_right = float(bboxitems[2])
    box_top = float(bboxitems[3])
    box_bottom = float(bboxitems[1])
    
    centerlat = (box_left+box_right)/2
    centerlong = (box_top+box_bottom)/2
    
    map_layers = []

    geoserver_layer = MVLayer(
        source='ImageWMS',
        options={'url': 'http://localhost:8181/geoserver/wms',
               'params': {'LAYERS': id},
               'serverType': 'geoserver'},
        legend_title=id,
        legend_extent=[box_left, box_bottom, box_right, box_top],
        legend_classes=[
            MVLegendClass('polygon', 'Boundary', fill='#999999'),
    ])

    map_layers.append(geoserver_layer)

    view_options = MVView(
        projection='EPSG:4326',
        center=[centerlat, centerlong],
        zoom=4,
        maxZoom=18,
        minZoom=2,
    )

    map_options = MapView(height='300px',
                          width='100%',
                          layers=map_layers,
                          legend=True,
                          view=view_options,
                          #basemap='MapQuest' 
                                  )       
    
    
    
    """
    SET UP THE GRAPH OPTIONS
    """
    project_directory = os.path.dirname(__file__)
    user_workspace = os.path.join(project_directory, 'workspaces', 'user_workspaces')

    if not os.path.exists(user_workspace):
        os.makedirs(user_workspace)

    csv_file = os.path.join(user_workspace, 'output/' + id + '/hydrograph.csv')   
   
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        csvlist = list(reader)
    
    volume_time_series = []
    formatter_string = "%m/%d/%Y"
    for item in csvlist:
        mydate = datetime.strptime(item[0], formatter_string)
        volume_time_series.append([mydate, float(item[1])])

    # Configure the time series Plot View
    grace_plot = TimeSeries(
        engine='highcharts',
        title=id + ' GRACE Data',
        y_axis_title='Volume',
        y_axis_units='cm',
        series=[
           {
               'name': 'Change in Volume',
               'color': '#0066ff',
               'data': volume_time_series,
           },
        ],
        width='100%',
        height='300px'
    )

    context = {'map_options': map_options,
               'grace_plot': grace_plot,
               'reg_id': id}

    return render(request, 'grace/home.html', context)