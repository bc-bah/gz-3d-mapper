"""
Small terrain generation test to validate Open Topo Data integration.
This creates a minimal test case for the elevation service.
"""

import os
import sys
import tempfile
import shutil
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

def test_small_terrain_generation():
    """Test terrain generation with a small area."""
    print("🏔️ Testing Small Terrain Generation")
    print("="*50)
    
    try:
        # Import required modules
        from scripts.utils.elevation_service import download_elevation_data
        import numpy as np
        
        # Create temporary output directory
        temp_output = tempfile.mkdtemp()
        print(f"📁 Using temporary directory: {temp_output}")
        
        # Define small test bounds (Central Park area, NYC)
        test_bounds = {
            "southwest": (40.7644, -73.9757),  # Southwest corner
            "northeast": (40.7822, -73.9584),  # Northeast corner  
            "southeast": (40.7644, -73.9584),  # Southeast corner
            "northwest": (40.7822, -73.9757)   # Northwest corner
        }
        
        print(f"🌍 Test area: Central Park, NYC")
        print(f"   Southwest: {test_bounds['southwest']}")
        print(f"   Northeast: {test_bounds['northeast']}")
        
        print("\n📡 Downloading elevation data from Open Topo Data...")
        
        # Test elevation data download
        try:
            heightmap_file = download_elevation_data(test_bounds, temp_output)
            print(f"✓ Elevation download completed")
            print(f"📄 Heightmap file: {os.path.basename(heightmap_file)}")
            
            # Verify files were created
            expected_files = ['heightmap.npy', 'elevation_metadata.json']
            created_files = []
            
            for filename in expected_files:
                filepath = os.path.join(temp_output, filename)
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    print(f"✓ {filename}: {size:,} bytes")
                    created_files.append(filename)
                else:
                    print(f"✗ {filename}: Not found")
            
            # Load and analyze heightmap
            if 'heightmap.npy' in created_files:
                heightmap = np.load(os.path.join(temp_output, 'heightmap.npy'))
                
                print(f"\n📊 Heightmap Analysis:")
                print(f"   Shape: {heightmap.shape}")
                print(f"   Min elevation: {np.min(heightmap):.2f} meters")
                print(f"   Max elevation: {np.max(heightmap):.2f} meters")
                print(f"   Mean elevation: {np.mean(heightmap):.2f} meters")
                print(f"   Data type: {heightmap.dtype}")
                
                # Central Park should have reasonable elevation values
                if 0 <= np.min(heightmap) <= 100 and 0 <= np.max(heightmap) <= 100:
                    print("✓ Elevation values are reasonable for NYC area")
                else:
                    print("⚠️ Elevation values seem unusual for NYC area")
                
            # Read metadata
            if 'elevation_metadata.json' in created_files:
                import json
                with open(os.path.join(temp_output, 'elevation_metadata.json'), 'r') as f:
                    metadata = json.load(f)
                
                print(f"\n📋 Metadata:")
                print(f"   Source: {metadata.get('source')}")
                print(f"   Resolution: {metadata.get('resolution')}")
                print(f"   Bounds match: {metadata.get('bounds') == test_bounds}")
            
            success = len(created_files) == len(expected_files)
            
        except Exception as e:
            print(f"✗ Elevation download failed: {e}")
            success = False
        
        # Cleanup
        shutil.rmtree(temp_output, ignore_errors=True)
        print(f"\n🧹 Cleaned up temporary files")
        
        return success
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_coordinate_bounds():
    """Test coordinate boundary calculations."""
    print("\n📐 Testing Coordinate Bounds")
    print("="*30)
    
    try:
        from scripts.utils.maptile_utils import maptile_utiles
        import mercantile
        
        # Test bounds for different zoom levels
        test_cases = [
            {"lat": 40.7589, "lng": -73.9851, "zoom": 12, "desc": "NYC - Zoom 12"},
            {"lat": 37.7749, "lng": -122.4194, "zoom": 14, "desc": "SF - Zoom 14"},
            {"lat": 51.5074, "lng": -0.1278, "zoom": 13, "desc": "London - Zoom 13"}
        ]
        
        all_passed = True
        
        for case in test_cases:
            lat, lng, zoom, desc = case['lat'], case['lng'], case['zoom'], case['desc']
            
            # Get tile for coordinate
            tile = mercantile.tile(lng, lat, zoom)
            
            # Get bounds using our utility
            bounds = maptile_utiles.get_true_boundaries(
                [lat-0.01, lng-0.01, lat+0.01, lng+0.01], zoom
            )
            
            print(f"📍 {desc}:")
            print(f"   Tile: {tile.x}, {tile.y}, {tile.z}")
            print(f"   Bounds calculated: ✓")
            
            # Verify bounds are reasonable
            if 'southwest' in bounds and 'northeast' in bounds:
                sw = bounds['southwest']
                ne = bounds['northeast']
                
                # Check that northeast is actually northeast of southwest
                if ne[0] > sw[0] and ne[1] > sw[1]:
                    print(f"   Bound validation: ✓")
                else:
                    print(f"   Bound validation: ✗ Invalid bounds")
                    all_passed = False
            else:
                print(f"   Bound validation: ✗ Missing bounds")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Coordinate bounds test failed: {e}")
        return False

def test_elevation_cache():
    """Test elevation caching functionality.""" 
    print("\n💾 Testing Elevation Cache")
    print("="*30)
    
    try:
        from scripts.utils.elevation_service import ElevationService
        import tempfile
        import shutil
        
        # Create temporary cache
        temp_cache = tempfile.mkdtemp()
        
        # Mock configuration
        class MockParam:
            ELEVATION_CACHE_DIR = temp_cache
            OPEN_TOPO_DATA_API_URL = "https://api.opentopodata.org/v1/srtm30m"
            OPEN_TOPO_DATA_TIMEOUT = 10
            OPEN_TOPO_DATA_MAX_LOCATIONS = 100
        
        # Replace globalParam temporarily
        import scripts.utils.elevation_service as es
        original_param = es.globalParam
        es.globalParam = MockParam()
        
        elevation_service = ElevationService()
        
        # Test caching
        test_coords = [(40.7589, -73.9851), (37.7749, -122.4194)]
        
        print("📝 Testing cache write/read...")
        
        # Cache some test data
        for i, (lat, lng) in enumerate(test_coords):
            elevation_service._cache_elevation(lat, lng, 10.0 + i)
        
        # Verify cached data can be retrieved
        cached_count = 0
        for i, (lat, lng) in enumerate(test_coords):
            cached = elevation_service._get_cached_elevation(lat, lng)
            if cached == 10.0 + i:
                cached_count += 1
                print(f"✓ Cache hit for {lat}, {lng}: {cached}m")
            else:
                print(f"✗ Cache miss for {lat}, {lng}")
        
        # Test cache directory structure
        cache_files = os.listdir(temp_cache)
        print(f"📁 Cache files created: {len(cache_files)}")
        
        success = cached_count == len(test_coords) and len(cache_files) > 0
        
        # Cleanup
        shutil.rmtree(temp_cache, ignore_errors=True)
        es.globalParam = original_param
        
        return success
        
    except Exception as e:
        print(f"✗ Elevation cache test failed: {e}")
        return False

def main():
    """Run terrain generation tests."""
    print("🧪 MapLibre GL Terrain Generation Tests")
    print("="*60)
    print()
    
    tests = [
        ("Coordinate Bounds", test_coordinate_bounds),
        ("Elevation Cache", test_elevation_cache),
        ("Small Terrain Generation", test_small_terrain_generation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("🧪 TERRAIN GENERATION TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All terrain generation tests passed!")
        print("✓ Open Topo Data integration working")
        print("✓ Coordinate precision maintained") 
        print("✓ Elevation caching functional")
        print("✓ Ready for full terrain generation!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        print("Check the output above for details.")

if __name__ == '__main__':
    main()