import os
import json
import time
import hashlib
import requests
import numpy as np
from multiprocessing import Pool, cpu_count
from .param import globalParam
from .maptile_utils import maptile_utiles


class ElevationService:
    """
    Open Topo Data API service to replace Mapbox DEM tiles.
    Uses coordinate-based elevation queries with local caching.
    """
    
    def __init__(self):
        self.cache_dir = globalParam.ELEVATION_CACHE_DIR
        self.api_url = globalParam.OPEN_TOPO_DATA_API_URL
        self.timeout = globalParam.OPEN_TOPO_DATA_TIMEOUT
        self.max_locations = globalParam.OPEN_TOPO_DATA_MAX_LOCATIONS
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure elevation cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, lat, lon):
        """Generate cache key for lat/lon coordinate."""
        coord_str = f"{lat:.6f},{lon:.6f}"
        return hashlib.md5(coord_str.encode()).hexdigest()
    
    def _get_cached_elevation(self, lat, lon):
        """Get cached elevation if available."""
        cache_key = self._get_cache_key(lat, lon)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data.get('elevation')
            except (json.JSONDecodeError, IOError):
                pass
        return None
    
    def _cache_elevation(self, lat, lon, elevation):
        """Cache elevation data for lat/lon coordinate."""
        cache_key = self._get_cache_key(lat, lon)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'lat': lat,
                    'lon': lon,
                    'elevation': elevation,
                    'timestamp': time.time()
                }, f)
        except IOError:
            pass  # Ignore cache write errors
    
    def get_elevation_batch(self, coordinates):
        """
        Get elevations for batch of coordinates using Open Topo Data API.
        
        Args:
            coordinates (list): List of (lat, lon) tuples
            
        Returns:
            dict: Dictionary mapping (lat, lon) to elevation in meters
        """
        results = {}
        uncached_coords = []
        
        # Check cache first
        for lat, lon in coordinates:
            cached_elev = self._get_cached_elevation(lat, lon)
            if cached_elev is not None:
                results[(lat, lon)] = cached_elev
            else:
                uncached_coords.append((lat, lon))
        
        # Fetch uncached coordinates from API
        if uncached_coords:
            # Split into batches to respect API limits
            for i in range(0, len(uncached_coords), self.max_locations):
                batch = uncached_coords[i:i + self.max_locations]
                batch_results = self._fetch_elevation_batch(batch)
                results.update(batch_results)
                
                # Add delay to respect API rate limits
                if i + self.max_locations < len(uncached_coords):
                    time.sleep(1)  # 1 second delay between batches
        
        return results
    
    def _fetch_elevation_batch(self, coordinates):
        """Fetch elevation data from Open Topo Data API."""
        results = {}
        
        # Format locations for API
        locations = "|".join([f"{lat},{lon}" for lat, lon in coordinates])
        
        try:
            response = requests.get(
                self.api_url,
                params={'locations': locations},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'OK':
                for i, result_data in enumerate(data.get('results', [])):
                    lat, lon = coordinates[i]
                    elevation = result_data.get('elevation')
                    
                    if elevation is not None:
                        results[(lat, lon)] = elevation
                        self._cache_elevation(lat, lon, elevation)
                    else:
                        # Use default elevation for invalid points
                        results[(lat, lon)] = 0.0
                        
        except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
            print(f"Error fetching elevation data: {e}")
            # Return default elevations for failed requests
            for lat, lon in coordinates:
                results[(lat, lon)] = 0.0
        
        return results
    
    def generate_heightmap_from_bounds(self, bounds, resolution=64):
        """
        Generate heightmap array from geographic bounds.
        
        Args:
            bounds (dict): Bounds with 'southwest', 'northeast', etc.
            resolution (int): Grid resolution for heightmap
            
        Returns:
            numpy.ndarray: 2D array of elevation values
        """
        # Extract coordinate bounds
        south = min(bounds["southwest"][0], bounds["southeast"][0])
        north = max(bounds["northwest"][0], bounds["northeast"][0])
        west = min(bounds["southwest"][1], bounds["northwest"][1])
        east = max(bounds["southeast"][1], bounds["northeast"][1])
        
        # Generate coordinate grid
        lats = np.linspace(south, north, resolution)
        lons = np.linspace(west, east, resolution)
        
        coordinates = []
        for lat in lats:
            for lon in lons:
                coordinates.append((lat, lon))
        
        # Get elevation data
        elevations = self.get_elevation_batch(coordinates)
        
        # Create heightmap array
        heightmap = np.zeros((resolution, resolution))
        idx = 0
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                heightmap[i, j] = elevations.get((lat, lon), 0.0)
                idx += 1
        
        return heightmap


def download_elevation_data(bounds, output_dir):
    """
    Main function to replace download_dem_data.
    Downloads elevation data using Open Topo Data API.
    
    Args:
        bounds (dict): Geographic bounds dictionary
        output_dir (str): Output directory for elevation data
    """
    elevation_service = ElevationService()
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate heightmap with higher resolution for terrain generation
    print("Downloading elevation data from Open Topo Data...")
    heightmap = elevation_service.generate_heightmap_from_bounds(bounds, resolution=128)
    
    # Save heightmap as numpy array for processing
    heightmap_file = os.path.join(output_dir, "heightmap.npy")
    np.save(heightmap_file, heightmap)
    
    # Create metadata file
    metadata = {
        'bounds': bounds,
        'resolution': 128,
        'source': 'Open Topo Data (SRTM 30m)',
        'timestamp': time.time()
    }
    
    metadata_file = os.path.join(output_dir, "elevation_metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Elevation data saved to {output_dir}")
    return heightmap_file