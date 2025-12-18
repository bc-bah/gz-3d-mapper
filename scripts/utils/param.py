import os
from pathlib import Path

class globalParam:

    TEMP_PATH                   =  str(Path(__file__).resolve().parents[2] / 'temp')
    OUTPUT_BASE_PATH            = str(Path(__file__).resolve().parents[2] / 'output')

    GAZEBO_MODEL_PATH           = os.path.abspath(os.path.expanduser(os.getenv('GAZEBO_MODEL_PATH', os.path.join(OUTPUT_BASE_PATH,'gazebo_terrain'))))  
    GAZEBO_WORLD_PATH           = os.path.abspath(os.path.expanduser(os.getenv('GAZEBO_WORLD_PATH', os.path.join(OUTPUT_BASE_PATH,'gazebo_terrain/worlds',))))  
    DEM_RESOLUTION              = 13


    DEM_PATH                    = os.path.join(OUTPUT_BASE_PATH, 'dem')
    HELIPAD_MODEL         = "https://fuel.gazebosim.org/1.0/saiaravind19/models/helipad" 
    # Set the global config
    TEMPORARY_SATELLITE_IMAGE    = os.path.join(TEMP_PATH,'gazebo_terrian')
    TEMPLATE_DIR_PATH            = str(Path(__file__).resolve().parents[2] / 'templates')
    
    # Open Topo Data API Configuration (replaces Mapbox DEM)
    OPEN_TOPO_DATA_API_URL       = "https://api.opentopodata.org/v1/srtm30m"
    OPEN_TOPO_DATA_TIMEOUT       = 10
    OPEN_TOPO_DATA_MAX_LOCATIONS = 100  # API limit per request
    ELEVATION_CACHE_DIR          = os.path.join(OUTPUT_BASE_PATH, 'elevation_cache')  
