"""
Unit tests for coordinate precision validation between MapLibre GL and mercantile library.
Ensures sub-pixel accuracy for tile edge alignment in the terrain generation pipeline.
"""

import unittest
import math
import mercantile
from scripts.utils.maptile_utils import maptile_utiles


class TestCoordinatePrecision(unittest.TestCase):
    
    def setUp(self):
        """Set up test cases with various coordinate scenarios."""
        self.test_coordinates = [
            # Format: (lng, lat, zoom, description)
            (-73.983652, 40.755024, 12, "New York City center"),
            (-122.4194, 37.7749, 14, "San Francisco high zoom"),
            (2.3522, 48.8566, 10, "Paris low zoom"), 
            (77.2090, 28.6139, 13, "New Delhi medium zoom"),
            (-87.6298, 41.8781, 15, "Chicago max detail"),
        ]
        
        self.precision_threshold = 1e-10  # Sub-pixel precision requirement
    
    def test_tile_coordinate_conversion_precision(self):
        """Test that tile coordinate conversions maintain precision."""
        for lng, lat, zoom, description in self.test_coordinates:
            with self.subTest(location=description, zoom=zoom):
                # Get tile coordinates using mercantile
                tile = mercantile.tile(lng, lat, zoom)
                
                # Convert back to geographic coordinates
                bounds = mercantile.bounds(tile)
                
                # Test that original coordinates fall within the tile bounds
                self.assertLessEqual(bounds.west, lng, 
                    f"Longitude precision error at {description}")
                self.assertLessEqual(lng, bounds.east,
                    f"Longitude precision error at {description}")
                self.assertLessEqual(bounds.south, lat,
                    f"Latitude precision error at {description}")
                self.assertLessEqual(lat, bounds.north,
                    f"Latitude precision error at {description}")
    
    def test_tile_boundary_calculation_accuracy(self):
        """Test tile boundary calculations match mercantile library."""
        for lng, lat, zoom, description in self.test_coordinates:
            with self.subTest(location=description, zoom=zoom):
                # Get tile coordinates
                tile = mercantile.tile(lng, lat, zoom)
                
                # Calculate bounds using our utility function
                our_bounds = maptile_utiles.get_tile_bounds(tile.x, tile.y, zoom)
                
                # Calculate bounds using mercantile
                mercantile_bounds = mercantile.bounds(tile)
                
                # Compare southwest corner
                self.assertAlmostEqual(
                    our_bounds["southwest"][0], mercantile_bounds.south,
                    places=10, msg=f"Southwest latitude mismatch at {description}")
                self.assertAlmostEqual(
                    our_bounds["southwest"][1], mercantile_bounds.west,
                    places=10, msg=f"Southwest longitude mismatch at {description}")
                
                # Compare northeast corner  
                self.assertAlmostEqual(
                    our_bounds["northeast"][0], mercantile_bounds.north,
                    places=10, msg=f"Northeast latitude mismatch at {description}")
                self.assertAlmostEqual(
                    our_bounds["northeast"][1], mercantile_bounds.east,
                    places=10, msg=f"Northeast longitude mismatch at {description}")
    
    def test_pixel_to_coordinate_precision(self):
        """Test pixel-to-coordinate conversion maintains required precision."""
        for lng, lat, zoom, description in self.test_coordinates:
            with self.subTest(location=description, zoom=zoom):
                # Get tile coordinates
                tile = mercantile.tile(lng, lat, zoom)
                bounds = mercantile.bounds(tile)
                
                # Calculate pixel size at this zoom level
                # At zoom level z, tile covers 360/2^z degrees longitude
                tile_size_degrees_lng = 360.0 / (2 ** zoom)
                pixel_size_lng = tile_size_degrees_lng / 256  # 256 pixels per tile
                
                # Similar for latitude (Web Mercator projection)
                tile_size_degrees_lat = abs(bounds.north - bounds.south)
                pixel_size_lat = tile_size_degrees_lat / 256
                
                # Test that pixel size is smaller than precision threshold
                self.assertLess(pixel_size_lng, 0.001,  # 0.001 degrees ~ 100m
                    f"Pixel longitude size too large at {description}")
                self.assertLess(pixel_size_lat, 0.001,
                    f"Pixel latitude size too large at {description}")
    
    def test_rectangular_bounds_precision(self):
        """Test rectangular selection bounds maintain precision."""
        # Simulate MapLibre GL rectangle drawing coordinates
        test_rectangles = [
            # Format: [(southwest_lng, southwest_lat), (northeast_lng, northeast_lat)]
            [(-74.0, 40.7), (-73.9, 40.8)],  # Manhattan area
            [(-122.5, 37.7), (-122.3, 37.8)],  # SF Bay area
            [(2.2, 48.8), (2.4, 48.9)],  # Paris area
        ]
        
        for rectangle in test_rectangles:
            southwest, northeast = rectangle
            sw_lng, sw_lat = southwest
            ne_lng, ne_lat = northeast
            
            with self.subTest(rectangle=rectangle):
                # Test that coordinates are within reasonable precision
                lng_diff = ne_lng - sw_lng
                lat_diff = ne_lat - sw_lat
                
                self.assertGreater(lng_diff, 0, "Invalid rectangle: negative longitude span")
                self.assertGreater(lat_diff, 0, "Invalid rectangle: negative latitude span")
                
                # Test precision of individual coordinates
                for coord in [sw_lng, sw_lat, ne_lng, ne_lat]:
                    # Check that coordinate has reasonable precision (not truncated)
                    coord_str = f"{coord:.10f}"
                    reconstructed = float(coord_str)
                    self.assertAlmostEqual(coord, reconstructed, places=10,
                        msg=f"Coordinate precision lost: {coord}")
    
    def test_bounds_to_tiles_conversion(self):
        """Test conversion from geographic bounds to tile coordinates."""
        # Test bounds that should convert to exact tile boundaries
        test_bounds = [
            {
                "southwest": (40.712776, -74.005974),  # NYC
                "northeast": (40.774789, -73.872070),
                "zoom": 12
            },
            {
                "southwest": (37.752, -122.447),  # SF
                "northeast": (37.785, -122.390), 
                "zoom": 14
            }
        ]
        
        for bounds_data in test_bounds:
            bounds = bounds_data
            zoom = bounds_data["zoom"]
            
            with self.subTest(bounds=bounds, zoom=zoom):
                # Get tile range for bounds
                sw_tile = mercantile.tile(bounds["southwest"][1], bounds["southwest"][0], zoom)
                ne_tile = mercantile.tile(bounds["northeast"][1], bounds["northeast"][0], zoom)
                
                # Verify tile range is reasonable
                tile_width = ne_tile.x - sw_tile.x + 1
                tile_height = sw_tile.y - ne_tile.y + 1  # Y increases downward
                
                self.assertGreater(tile_width, 0, "Invalid tile width")
                self.assertGreater(tile_height, 0, "Invalid tile height") 
                self.assertLess(tile_width, 100, "Tile range too wide (may cause performance issues)")
                self.assertLess(tile_height, 100, "Tile range too tall (may cause performance issues)")


class TestPerformanceBenchmarks(unittest.TestCase):
    """Test performance aspects of coordinate calculations."""
    
    def test_coordinate_conversion_speed(self):
        """Benchmark coordinate conversion performance."""
        import time
        
        test_coordinates = [(-73.983652 + i*0.001, 40.755024 + i*0.001) 
                           for i in range(1000)]
        zoom = 13
        
        start_time = time.time()
        
        for lng, lat in test_coordinates:
            tile = mercantile.tile(lng, lat, zoom)
            bounds = mercantile.bounds(tile)
        
        end_time = time.time()
        conversion_time = end_time - start_time
        
        # Should be able to convert 1000 coordinates in under 0.1 seconds
        self.assertLess(conversion_time, 0.1, 
            f"Coordinate conversion too slow: {conversion_time:.3f}s for 1000 conversions")
        
        print(f"Coordinate conversion benchmark: {conversion_time:.3f}s for 1000 conversions")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)