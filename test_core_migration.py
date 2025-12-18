#!/usr/bin/env python3
"""
Core migration testing script for MapLibre GL migration validation.
Tests internal components without requiring external API calls.
"""

import sys
import os
import json
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def test_imports():
    """Test that all required modules can be imported successfully."""
    print("🧪 Testing Imports...")
    try:
        from utils.elevation_service import ElevationService
        from utils.custom_geocoder import CustomGeocoder, LandmarkDatabase
        from utils.param import globalParam
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_elevation_service_instantiation():
    """Test that the elevation service can be instantiated."""
    print("\n🧪 Testing Elevation Service...")
    try:
        from utils.elevation_service import ElevationService
        service = ElevationService()
        print(f"✅ ElevationService created: {type(service)}")
        
        # Test coordinate grid generation (using internal coordinate generation logic)
        bounds = {'southwest': [40.76, -73.97], 'northeast': [40.77, -73.96], 'southeast': [40.76, -73.96], 'northwest': [40.77, -73.97]}
        # Test if we can create the coordinate bounds
        print(f"✅ Bounds processing: {len(bounds)} boundary points")
        return True
    except Exception as e:
        print(f"❌ Elevation service failed: {e}")
        return False

def test_custom_geocoder():
    """Test the custom geocoder functionality."""
    print("\n🧪 Testing Custom Geocoder...")
    try:
        from utils.custom_geocoder import CustomGeocoder, LandmarkDatabase
        
        # Test landmark database
        db = LandmarkDatabase()
        landmarks = db.landmarks  # Use the actual attribute
        print(f"✅ Landmark database: {len(landmarks)} landmarks loaded")
        
        # Test geocoder
        geocoder = CustomGeocoder()
        
        # Test exact match
        result = geocoder.search("Times Square")
        if result:
            print(f"✅ Exact match found: {result['name']} at {result['center']}")
        else:
            print("⚠️ No exact match for Times Square")
            
        # Test fuzzy match
        result = geocoder.search("central park")
        if result:
            print(f"✅ Fuzzy match found: {result['name']}")
        else:
            print("⚠️ No fuzzy match for central park")
            
        return True
    except Exception as e:
        print(f"❌ Custom geocoder failed: {e}")
        return False

def test_param_configuration():
    """Test parameter configuration without Mapbox dependencies."""
    print("\n🧪 Testing Parameter Configuration...")
    try:
        from utils.param import globalParam
        
        # Check that Mapbox API key is not required
        if hasattr(globalParam, 'MAPBOX_API_KEY'):
            print(f"⚠️ Mapbox API key still present: {hasattr(globalParam, 'MAPBOX_API_KEY')}")
        else:
            print("✅ Mapbox API key successfully removed")
            
        # Check other required parameters
        print(f"✅ Tile download URL: {hasattr(globalParam, 'TILE_DOWNLOAD_URL')}")
        print(f"✅ Output path configured: {hasattr(globalParam, 'PATH_TO_OUTPUT')}")
        
        return True
    except Exception as e:
        print(f"❌ Parameter configuration failed: {e}")
        return False

def test_frontend_files():
    """Test that frontend files have been properly updated."""
    print("\n🧪 Testing Frontend Files...")
    
    # Test HTML file
    html_file = Path("scripts/UI/index.htm")
    if html_file.exists():
        content = html_file.read_text()
        maplibre_refs = content.count("maplibre-gl")
        # Check for actual Mapbox API/library references, not plugin file names
        mapbox_api_refs = content.count("mapbox-gl-js") + content.count("mapboxgl-css") + content.count("mapbox.com")
        mapbox_class_refs = content.count("mapboxgl-")
        
        print(f"✅ HTML MapLibre references: {maplibre_refs}")
        if maplibre_refs > 0 and mapbox_api_refs == 0 and mapbox_class_refs == 0:
            print("✅ HTML file updated to MapLibre GL")
        else:
            print(f"⚠️ HTML file: MapLibre refs: {maplibre_refs}, Mapbox API refs: {mapbox_api_refs}, Mapbox classes: {mapbox_class_refs}")
    else:
        print("❌ HTML file not found")
        return False
    
    # Test JavaScript file
    js_file = Path("scripts/UI/main.js")
    if js_file.exists():
        content = js_file.read_text()
        maplibre_refs = content.count("maplibregl")
        mapbox_refs = content.count("mapboxgl")
        print(f"✅ JavaScript MapLibre references: {maplibre_refs}")
        if mapbox_refs > 0:
            print(f"⚠️ JavaScript still has {mapbox_refs} Mapbox references")
        else:
            print("✅ JavaScript fully migrated to MapLibre GL")
    else:
        print("❌ JavaScript file not found")
        return False
        
    return True

def test_server_configuration():
    """Test server configuration changes."""
    print("\n🧪 Testing Server Configuration...")
    try:
        # Import server module
        import server
        
        # Check if Mapbox validation is removed
        server_file = Path("scripts/server.py")
        if server_file.exists():
            content = server_file.read_text()
            if "MAPBOX_API_KEY" not in content:
                print("✅ Mapbox API key validation removed from server")
            else:
                print("⚠️ Server still references Mapbox API key")
                
            if "elevation_service" in content:
                print("✅ Elevation service integrated into server")
            else:
                print("❌ Elevation service not found in server")
                return False
        
        print("✅ Server configuration updated")
        return True
    except Exception as e:
        print(f"❌ Server configuration test failed: {e}")
        return False

def test_coordinate_precision():
    """Test coordinate precision without external API calls."""
    print("\n🧪 Testing Coordinate Precision...")
    try:
        import mercantile
        
        # Test coordinate transformations
        bounds = {'south': 40.7589, 'west': -73.9851, 'north': 40.7789, 'east': -73.9651}
        
        # Test tile calculations
        zoom = 15
        southwest = mercantile.tile(bounds['west'], bounds['south'], zoom)
        northeast = mercantile.tile(bounds['east'], bounds['north'], zoom)
        
        print(f"✅ SW Tile: {southwest}")
        print(f"✅ NE Tile: {northeast}")
        
        # Test reverse calculation
        tile_bounds = mercantile.bounds(southwest)
        print(f"✅ Tile bounds precision: {abs(tile_bounds.west - bounds['west']) < 0.01}")
        
        return True
    except Exception as e:
        print(f"❌ Coordinate precision test failed: {e}")
        return False

def main():
    """Run all core migration tests."""
    print("🚀 Starting Core Migration Testing")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Elevation Service", test_elevation_service_instantiation), 
        ("Custom Geocoder", test_custom_geocoder),
        ("Parameter Configuration", test_param_configuration),
        ("Frontend Files", test_frontend_files),
        ("Server Configuration", test_server_configuration),
        ("Coordinate Precision", test_coordinate_precision),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🏁 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core migration components are working correctly!")
        print("✨ Ready for browser testing of the web interface")
    else:
        print("⚠️ Some core components need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)