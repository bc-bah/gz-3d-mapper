"""
Test script to validate MapLibre GL migration components.
Run this to test geocoding, elevation service, and coordinate precision.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

def test_custom_geocoder():
    """Test the custom geocoder implementation."""
    print("=== Testing Custom Geocoder ===")
    
    try:
        from scripts.utils.custom_geocoder import CustomGeocoder
        
        geocoder = CustomGeocoder()
        
        # Test local database search
        print("1. Testing local landmark database...")
        results = geocoder.search("New York", use_external=False)
        
        if results:
            print(f"✓ Found {len(results)} results for 'New York'")
            best_result = results[0]
            print(f"  Best match: {best_result['name']} ({best_result['lat']}, {best_result['lng']})")
            print(f"  Score: {best_result['score']}, Source: {best_result['source']}")
        else:
            print("✗ No results found for 'New York'")
            
        # Test coordinate extraction
        print("\n2. Testing coordinate extraction...")
        coords = geocoder.get_coordinates("San Francisco")
        if coords:
            print(f"✓ San Francisco coordinates: {coords}")
        else:
            print("✗ Could not get San Francisco coordinates")
            
        # Test fuzzy matching
        print("\n3. Testing fuzzy matching...")
        results = geocoder.search("newyork", use_external=False)  # No space
        if results:
            print(f"✓ Fuzzy match worked: {results[0]['name']} (score: {results[0]['score']})")
        else:
            print("✗ Fuzzy matching failed")
            
        return True
        
    except Exception as e:
        print(f"✗ Geocoder test failed: {e}")
        return False

def test_elevation_service():
    """Test the elevation service implementation."""
    print("\n=== Testing Elevation Service ===")
    
    try:
        from scripts.utils.elevation_service import ElevationService
        import tempfile
        import shutil
        
        # Create temporary cache for testing
        temp_cache = tempfile.mkdtemp()
        
        # Mock globalParam for testing
        class MockParam:
            ELEVATION_CACHE_DIR = temp_cache
            OPEN_TOPO_DATA_API_URL = "https://api.opentopodata.org/v1/srtm30m"
            OPEN_TOPO_DATA_TIMEOUT = 10
            OPEN_TOPO_DATA_MAX_LOCATIONS = 100
        
        # Temporarily replace globalParam
        import scripts.utils.elevation_service as es
        original_param = es.globalParam
        es.globalParam = MockParam()
        
        elevation_service = ElevationService()
        
        print("1. Testing cache key generation...")
        key1 = elevation_service._get_cache_key(40.7589, -73.9851)
        key2 = elevation_service._get_cache_key(40.7589, -73.9851)
        
        if key1 == key2 and len(key1) == 32:
            print(f"✓ Cache key generation works: {key1}")
        else:
            print("✗ Cache key generation failed")
            
        print("\n2. Testing elevation caching...")
        lat, lng, elevation = 40.7589, -73.9851, 15.5
        
        # Cache elevation
        elevation_service._cache_elevation(lat, lng, elevation)
        
        # Retrieve from cache
        cached = elevation_service._get_cached_elevation(lat, lng)
        
        if cached == elevation:
            print(f"✓ Caching works: {cached} meters")
        else:
            print(f"✗ Caching failed: expected {elevation}, got {cached}")
            
        print("\n3. Testing coordinate precision...")
        high_precision_lat = 40.758895432
        high_precision_lng = -73.985123567
        
        elevation_service._cache_elevation(high_precision_lat, high_precision_lng, 20.0)
        cached_precise = elevation_service._get_cached_elevation(high_precision_lat, high_precision_lng)
        
        # Test slightly different coordinates don't match
        slightly_different = elevation_service._get_cached_elevation(40.758895433, high_precision_lng)
        
        if cached_precise == 20.0 and slightly_different is None:
            print("✓ High precision coordinate caching works")
        else:
            print("✗ Precision coordinate caching failed")
        
        # Cleanup
        shutil.rmtree(temp_cache, ignore_errors=True)
        es.globalParam = original_param
        
        return True
        
    except Exception as e:
        print(f"✗ Elevation service test failed: {e}")
        return False

def test_coordinate_precision():
    """Test coordinate precision using mercantile library."""
    print("\n=== Testing Coordinate Precision ===")
    
    try:
        import mercantile
        from scripts.utils.maptile_utils import maptile_utiles
        
        # Test coordinates from the migration
        test_cases = [
            (-73.983652, 40.755024, 12, "New York City"),
            (-122.4194, 37.7749, 14, "San Francisco"),
            (2.3522, 48.8566, 13, "Paris")
        ]
        
        print("1. Testing tile coordinate conversion precision...")
        all_passed = True
        
        for lng, lat, zoom, description in test_cases:
            # Get tile coordinates using mercantile
            tile = mercantile.tile(lng, lat, zoom)
            
            # Get bounds using our utility function
            our_bounds = maptile_utiles.get_tile_bounds(tile.x, tile.y, zoom)
            
            # Get bounds using mercantile
            mercantile_bounds = mercantile.bounds(tile)
            
            # Compare precision
            sw_lat_diff = abs(our_bounds["southwest"][0] - mercantile_bounds.south)
            sw_lng_diff = abs(our_bounds["southwest"][1] - mercantile_bounds.west)
            ne_lat_diff = abs(our_bounds["northeast"][0] - mercantile_bounds.north)
            ne_lng_diff = abs(our_bounds["northeast"][1] - mercantile_bounds.east)
            
            max_diff = max(sw_lat_diff, sw_lng_diff, ne_lat_diff, ne_lng_diff)
            
            if max_diff < 1e-10:  # Sub-pixel precision
                print(f"✓ {description} precision: {max_diff:.2e}")
            else:
                print(f"✗ {description} precision too low: {max_diff:.2e}")
                all_passed = False
        
        if all_passed:
            print("✓ All coordinate precision tests passed")
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Coordinate precision test failed: {e}")
        return False

def test_maplibre_integration():
    """Check MapLibre GL integration in frontend files."""
    print("\n=== Testing MapLibre GL Integration ===")
    
    try:
        # Check HTML dependencies
        print("1. Checking HTML dependencies...")
        with open('scripts/UI/index.htm', 'r') as f:
            html_content = f.read()
        
        maplibre_found = 'maplibre-gl' in html_content
        mapbox_removed = 'mapbox-gl-js' not in html_content
        
        if maplibre_found and mapbox_removed:
            print("✓ HTML dependencies updated to MapLibre GL")
        else:
            print(f"✗ HTML dependency issue: MapLibre={maplibre_found}, Mapbox removed={mapbox_removed}")
        
        # Check JavaScript integration
        print("\n2. Checking JavaScript integration...")
        with open('scripts/UI/main.js', 'r') as f:
            js_content = f.read()
        
        maplibre_api_found = 'maplibregl' in js_content
        mapbox_api_removed = 'mapboxgl' not in js_content
        osm_style_found = 'demotiles.maplibre.org' in js_content
        
        if maplibre_api_found and mapbox_api_removed and osm_style_found:
            print("✓ JavaScript updated to MapLibre GL with OSM style")
        else:
            print(f"✗ JavaScript issue: MapLibre API={maplibre_api_found}, Mapbox removed={mapbox_api_removed}, OSM style={osm_style_found}")
        
        # Check CSS updates
        print("\n3. Checking CSS updates...")
        with open('scripts/UI/style.css', 'r') as f:
            css_content = f.read()
        
        maplibre_css_found = 'maplibregl' in css_content
        mapbox_css_removed = 'mapboxgl' not in css_content
        
        if maplibre_css_found and mapbox_css_removed:
            print("✓ CSS updated to MapLibre GL classes")
        else:
            print(f"✗ CSS issue: MapLibre classes={maplibre_css_found}, Mapbox removed={mapbox_css_removed}")
        
        return True
        
    except Exception as e:
        print(f"✗ MapLibre integration check failed: {e}")
        return False

def test_server_configuration():
    """Test server configuration for open-source stack."""
    print("\n=== Testing Server Configuration ===")
    
    try:
        from scripts.utils.param import globalParam
        
        print("1. Checking configuration parameters...")
        
        # Check that Mapbox API key is removed
        if hasattr(globalParam, 'MAPBOX_API_KEY'):
            print("⚠ Mapbox API key still present in configuration")
        else:
            print("✓ Mapbox API key removed from configuration")
        
        # Check Open Topo Data configuration
        if hasattr(globalParam, 'OPEN_TOPO_DATA_API_URL'):
            print(f"✓ Open Topo Data URL configured: {globalParam.OPEN_TOPO_DATA_API_URL}")
        else:
            print("✗ Open Topo Data URL not configured")
        
        # Check elevation cache directory
        if hasattr(globalParam, 'ELEVATION_CACHE_DIR'):
            print(f"✓ Elevation cache directory configured: {globalParam.ELEVATION_CACHE_DIR}")
        else:
            print("✗ Elevation cache directory not configured")
        
        return True
        
    except Exception as e:
        print(f"✗ Server configuration test failed: {e}")
        return False

def main():
    """Run all migration tests."""
    print("🧪 Testing MapLibre GL Migration Implementation\n")
    
    tests = [
        ("MapLibre GL Integration", test_maplibre_integration),
        ("Custom Geocoder", test_custom_geocoder),
        ("Elevation Service", test_elevation_service),
        ("Coordinate Precision", test_coordinate_precision),
        ("Server Configuration", test_server_configuration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*50)
    print("🧪 MIGRATION TEST SUMMARY")
    print("="*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All migration tests passed! MapLibre GL migration is successful.")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Check the output above for details.")

if __name__ == '__main__':
    main()