"""
Unit tests for the new Open Topo Data elevation service.
Tests API integration, caching, and coordinate precision.
"""

import unittest
import tempfile
import shutil
import os
import json
from unittest.mock import patch, Mock
import numpy as np

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.elevation_service import ElevationService, download_elevation_data


class TestElevationService(unittest.TestCase):
    
    def setUp(self):
        """Set up test with temporary cache directory."""
        self.temp_cache_dir = tempfile.mkdtemp()
        
        # Mock globalParam for testing
        with patch('scripts.utils.elevation_service.globalParam') as mock_param:
            mock_param.ELEVATION_CACHE_DIR = self.temp_cache_dir
            mock_param.OPEN_TOPO_DATA_API_URL = "https://api.opentopodata.org/v1/srtm30m"
            mock_param.OPEN_TOPO_DATA_TIMEOUT = 10
            mock_param.OPEN_TOPO_DATA_MAX_LOCATIONS = 100
            
            self.elevation_service = ElevationService()
    
    def tearDown(self):
        """Clean up temporary cache directory."""
        shutil.rmtree(self.temp_cache_dir, ignore_errors=True)
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        lat, lon = 40.7589, -73.9851  # NYC coordinates
        
        key1 = self.elevation_service._get_cache_key(lat, lon)
        key2 = self.elevation_service._get_cache_key(lat, lon)
        
        self.assertEqual(key1, key2, "Cache keys should be consistent")
        self.assertIsInstance(key1, str, "Cache key should be string")
        self.assertEqual(len(key1), 32, "Cache key should be MD5 hash length")
    
    def test_elevation_caching(self):
        """Test elevation data caching functionality."""
        lat, lon = 40.7589, -73.9851
        elevation = 15.5
        
        # Test caching
        self.elevation_service._cache_elevation(lat, lon, elevation)
        
        # Test retrieval
        cached_elevation = self.elevation_service._get_cached_elevation(lat, lon)
        
        self.assertEqual(cached_elevation, elevation, "Cached elevation should match")
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        lat, lon = 51.5074, -0.1278  # London coordinates (not cached)
        
        cached_elevation = self.elevation_service._get_cached_elevation(lat, lon)
        
        self.assertIsNone(cached_elevation, "Cache miss should return None")
    
    @patch('requests.get')
    def test_api_integration(self, mock_get):
        """Test Open Topo Data API integration."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'OK',
            'results': [
                {'elevation': 105.2},
                {'elevation': 98.7}
            ]
        }
        mock_get.return_value = mock_response
        
        coordinates = [(40.7589, -73.9851), (40.7505, -73.9934)]
        
        results = self.elevation_service.get_elevation_batch(coordinates)
        
        self.assertEqual(len(results), 2, "Should return elevation for both coordinates")
        self.assertEqual(results[(40.7589, -73.9851)], 105.2)
        self.assertEqual(results[(40.7505, -73.9934)], 98.7)
        
        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('locations', call_args[1]['params'])
    
    @patch('requests.get')
    def test_api_error_handling(self, mock_get):
        """Test API error handling."""
        # Mock API error
        mock_get.side_effect = Exception("Network error")
        
        coordinates = [(40.7589, -73.9851)]
        
        results = self.elevation_service.get_elevation_batch(coordinates)
        
        # Should return default elevation on error
        self.assertEqual(results[(40.7589, -73.9851)], 0.0)
    
    @patch('requests.get')
    def test_batch_size_limiting(self, mock_get):
        """Test that large coordinate batches are split properly."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'OK',
            'results': [{'elevation': 100.0} for _ in range(100)]
        }
        mock_get.return_value = mock_response
        
        # Create large coordinate list (more than max_locations)
        coordinates = [(40.0 + i*0.001, -74.0 + i*0.001) for i in range(150)]
        
        results = self.elevation_service.get_elevation_batch(coordinates)
        
        # Should make multiple API calls
        self.assertGreater(mock_get.call_count, 1, "Should split into multiple API calls")
        self.assertEqual(len(results), 150, "Should return all elevations")
    
    @patch('requests.get')
    def test_heightmap_generation(self, mock_get):
        """Test heightmap generation from bounds."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'OK',
            'results': [{'elevation': 50.0 + i} for i in range(4096)]  # 64x64 grid
        }
        mock_get.return_value = mock_response
        
        bounds = {
            "southwest": (40.7, -74.0),
            "northeast": (40.8, -73.9),
            "southeast": (40.7, -73.9),
            "northwest": (40.8, -74.0)
        }
        
        heightmap = self.elevation_service.generate_heightmap_from_bounds(bounds, resolution=64)
        
        self.assertEqual(heightmap.shape, (64, 64), "Heightmap should have correct dimensions")
        self.assertIsInstance(heightmap, np.ndarray, "Heightmap should be numpy array")
        self.assertGreater(heightmap.min(), 0, "Should have elevation data")
    
    def test_coordinate_precision(self):
        """Test that coordinate precision is maintained."""
        lat, lon = 40.758895432, -73.985123567  # High precision coordinates
        
        # Cache and retrieve
        self.elevation_service._cache_elevation(lat, lon, 15.5)
        cached_elevation = self.elevation_service._get_cached_elevation(lat, lon)
        
        self.assertIsNotNone(cached_elevation, "High precision coordinates should be cached")
        
        # Test slightly different coordinates don't match
        lat_different = 40.758895433  # 1 unit in last decimal place
        cached_elevation_different = self.elevation_service._get_cached_elevation(lat_different, lon)
        
        self.assertIsNone(cached_elevation_different, "Similar coordinates should not match cache")


class TestElevationIntegration(unittest.TestCase):
    """Integration tests for the elevation service."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_output_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_output_dir, ignore_errors=True)
    
    @patch('scripts.utils.elevation_service.ElevationService')
    def test_download_elevation_data_integration(self, mock_service_class):
        """Test the main download_elevation_data function."""
        # Mock elevation service
        mock_service = Mock()
        mock_heightmap = np.random.rand(128, 128) * 1000  # Random elevations
        mock_service.generate_heightmap_from_bounds.return_value = mock_heightmap
        mock_service_class.return_value = mock_service
        
        bounds = {
            "southwest": (40.7, -74.0),
            "northeast": (40.8, -73.9),
            "southeast": (40.7, -73.9),
            "northwest": (40.8, -74.0)
        }
        
        # Call function
        result_file = download_elevation_data(bounds, self.temp_output_dir)
        
        # Verify outputs
        self.assertTrue(os.path.exists(result_file), "Heightmap file should be created")
        self.assertTrue(result_file.endswith('heightmap.npy'), "Should return .npy file path")
        
        # Check metadata file
        metadata_file = os.path.join(self.temp_output_dir, "elevation_metadata.json")
        self.assertTrue(os.path.exists(metadata_file), "Metadata file should be created")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            self.assertEqual(metadata['bounds'], bounds)
            self.assertEqual(metadata['source'], 'Open Topo Data (SRTM 30m)')
    
    def test_file_structure_creation(self):
        """Test that proper file structure is created."""
        bounds = {
            "southwest": (40.7, -74.0),
            "northeast": (40.8, -73.9),
            "southeast": (40.7, -73.9),
            "northwest": (40.8, -74.0)
        }
        
        with patch('scripts.utils.elevation_service.ElevationService'):
            download_elevation_data(bounds, self.temp_output_dir)
        
        # Check directory structure
        self.assertTrue(os.path.isdir(self.temp_output_dir), "Output directory should exist")
        
        expected_files = ['heightmap.npy', 'elevation_metadata.json']
        for expected_file in expected_files:
            file_path = os.path.join(self.temp_output_dir, expected_file)
            self.assertTrue(os.path.exists(file_path), f"{expected_file} should be created")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)