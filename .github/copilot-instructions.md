# Gazebo Terrain Generator - AI Coding Instructions

## Overview
This project generates 3D Gazebo terrain models using real-world elevation data and satellite imagery. It's a Flask web application with a MapLibre GL frontend that downloads map tiles, processes open-source elevation data, and generates Gazebo SDF world files.

## Architecture Overview

### Core Workflow (3-stage pipeline)
1. **Tile Download Phase**: MapLibre GL frontend sends tile coordinates to Flask backend, which downloads satellite images using various map providers (Google, Bing, OpenStreetMap)
2. **Elevation Processing Phase**: Downloads elevation data from Open Topo Data API (SRTM 30m) and processes heightmaps with local caching
3. **Gazebo Generation Phase**: Combines satellite imagery + elevation data into Gazebo-compatible SDF files using template substitution

### Key Components
- **Flask Server** (`scripts/server.py`): REST API handling tile downloads and orchestrating generation pipeline
- **Utils Package** (`scripts/utils/`): Core processing modules for elevation data, terrain generation, and file operations
- **Web UI** (`scripts/UI/`): MapLibre GL-based interface for region selection and configuration with custom geocoding
- **Templates** (`templates/`): SDF template files with placeholder variables like `$MODELNAME$`, `$ORIGIN_LAT$`
- **Elevation Service** (`scripts/utils/elevation_service.py`): Open Topo Data API integration with caching

## Critical Development Patterns

### Environment Configuration
- **Configuration centralized** in `scripts/utils/param.py` via `globalParam` class
- **Output paths configurable** via `GAZEBO_MODEL_PATH` and `GAZEBO_WORLD_PATH` environment variables
- **No API keys required** - uses open-source services (MapLibre GL, Open Topo Data, Nominatim)
- **Default output structure**: `output/gazebo_terrain/` for models, `output/gazebo_terrain/worlds/` for world files

### File Processing Architecture  
- **Tile-based processing**: Uses mercantile library for XYZ tile coordinate calculations
- **Multiprocessing**: Column-wise image concatenation using `Pool` and `cpu_count()`
- **Thread-safe operations**: File operations use threading locks (`FileWriter` class with lock parameter)
- **Template substitution**: SDF files use `$VARIABLE$` placeholders replaced during generation

### Key API Endpoints
```
POST /download-tile     # Individual tile download
POST /start-download    # Initialize metadata  
POST /end-download      # Trigger terrain generation
GET /task-status        # Check background processing status
```

## Development Workflow

### Running the Application
```bash
# Setup virtual environment 
python3 -m venv terrain_generator
source terrain_generator/bin/activate  # Linux/Mac
# OR
terrain_generator\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start server (validates Mapbox API key first)
python scripts/server.py

# Access UI at http://localhost:8080
```

### File Structure Conventions
```
output/gazebo_terrain/
├── {model_name}/
│   ├── model.sdf              # Heightmap model definition
│   ├── model.config           # Gazebo model metadata
│   └── textures/
│       ├── {name}_height_map.tif    # 16-bit elevation data
│       └── {name}_aerial.png        # Stitched satellite texture
└── worlds/{model_name}.sdf    # World file referencing model
```

## Project-Specific Patterns

### Map Tile Coordinate System
- Uses **XYZ tile numbering** with zoom levels (higher zoom = more detail)
- **Boundary calculations**: Southwest/northeast corners define regions using `mercantile` library
- **Tile stitching**: Column-wise concatenation then row assembly for memory efficiency

### Elevation Data Integration  
- **Elevation source**: Open Topo Data API provides SRTM 30m elevation data with global coverage
- **Coordinate transformation**: Geographic bounds → coordinate grid → elevation queries → heightmap generation
- **Local caching**: MD5-based coordinate caching to reduce API calls and improve performance
- **Rate limiting**: Automatic delays between API requests to respect service limits

### Template System
- **SDF generation**: Uses simple string replacement (`$VARIABLE$` → actual values)
- **Key variables**: `$MODELNAME$`, `$ORIGIN_LAT$`, `$ORIGIN_LONG$`, `$ORIGIN_ELEVATION$`
- **Model references**: Generated models use `model://` URI scheme

### Error Handling Patterns
- **Graceful degradation**: Missing tiles handled without failing entire generation
- **Background processing**: Long-running terrain generation uses threading with status tracking
- **API validation**: Mapbox key validation on startup prevents runtime failures

## External Dependencies
- **Open Topo Data API**: For SRTM 30m elevation data with local caching and rate limiting
- **MapLibre GL**: Open-source mapping library with OpenStreetMap-based styles
- **Nominatim**: OpenStreetMap geocoding service with local landmark database fallback
- **Map providers**: Google, Bing, ESRI tiles (check ToC before commercial use)
- **Gazebo compatibility**: Generates SDF 1.6+ format with Bullet physics collision detection
- **Image processing**: OpenCV and PIL for tile stitching and format conversion

## Testing & Debugging
- **Sample worlds**: Use `sample_worlds/prayag/` to test Gazebo integration
- **Environment setup**: `export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:<path>`
- **Validation**: `gz sim prayag/prayag.sdf` for quick testing