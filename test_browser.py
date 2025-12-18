"""
Browser-based test guide for MapLibre GL migration functionality.
Use this guide to manually test the web interface.
"""

import webbrowser
import time

def print_test_guide():
    """Print comprehensive test guide for manual browser testing."""
    print("🌐 MapLibre GL Web Interface Test Guide")
    print("="*60)
    print()
    
    print("📋 PRE-TEST CHECKLIST:")
    print("• Server is running at http://localhost:8080")
    print("• Browser has developer tools available")
    print("• Network connection available for tile loading")
    print()
    
    print("🗺️ TEST 1: MAP LOADING")
    print("-" * 30)
    print("1. Open http://localhost:8080 in your browser")
    print("2. Check that the page loads without errors")
    print("3. Verify that a map appears (may take 2-10 seconds)")
    print("4. Expected: OpenStreetMap-based tiles should load")
    print("5. Map should be centered around New York City area")
    print()
    print("🔍 What to look for:")
    print("✓ No 'mapboxgl is not defined' errors in console")
    print("✓ Map tiles load and display correctly")
    print("✓ Map is interactive (pan, zoom works)")
    print("✓ Style loads without 404 errors")
    print()
    
    print("🔍 TEST 2: GEOCODING & SEARCH")
    print("-" * 30)
    print("1. Look for a search box or geocoder control")
    print("2. Try searching for 'San Francisco'")
    print("3. Try searching for 'London'")
    print("4. Try searching for 'JFK Airport'")
    print("5. Expected: Map should move to searched locations")
    print()
    print("🔍 What to look for:")
    print("✓ Search results appear for major cities")
    print("✓ Map centers on selected location")
    print("✓ No geocoder errors in console")
    print("✓ Fallback to local database works if network fails")
    print()
    
    print("📐 TEST 3: RECTANGLE SELECTION")
    print("-" * 30)
    print("1. Look for drawing tools or rectangle selection")
    print("2. Try to draw a rectangle on the map")
    print("3. Draw a small rectangle (approx 1-2 km area)")
    print("4. Expected: Rectangle should appear with precise boundaries")
    print("5. Check that coordinates are displayed accurately")
    print()
    print("🔍 What to look for:")
    print("✓ Drawing tools are available")
    print("✓ Rectangle can be drawn smoothly")
    print("✓ Coordinate precision maintained (6+ decimal places)")
    print("✓ No 'MapboxDraw is not defined' errors")
    print()
    
    print("🏔️ TEST 4: TERRAIN GENERATION")
    print("-" * 30)
    print("1. After drawing a rectangle, look for 'Generate Terrain' button")
    print("2. Click to start terrain generation")
    print("3. Expected: Process should start without errors")
    print("4. Monitor server terminal for elevation data download")
    print("5. Wait for completion message")
    print()
    print("🔍 What to look for:")
    print("✓ No Mapbox API errors")
    print("✓ Open Topo Data API requests succeed")
    print("✓ Elevation data caching works")
    print("✓ Terrain files generated in output directory")
    print()
    
    print("🛠️ DEBUGGING TOOLS")
    print("-" * 30)
    print("Browser Developer Tools (F12):")
    print("• Console tab: Check for JavaScript errors")
    print("• Network tab: Monitor tile and API requests")
    print("• Sources tab: Verify MapLibre GL scripts load")
    print()
    print("Server Terminal:")
    print("• Watch for HTTP requests and responses")
    print("• Monitor elevation API calls")
    print("• Check for any Python errors")
    print()
    
    print("❌ COMMON ISSUES TO WATCH FOR:")
    print("-" * 30)
    print("• 'mapboxgl is not defined' → MapboxGL remnants in code")
    print("• 'MapboxDraw is not defined' → Draw plugin not migrated")
    print("• 'Invalid style URL' → Style endpoint not accessible")
    print("• '401 Unauthorized' → API key issues (should not happen)")
    print("• Tiles not loading → Network or CDN issues")
    print("• Slow map loading → Style complexity or network")
    print()
    
    print("✅ SUCCESS CRITERIA:")
    print("-" * 30)
    print("🗺️ Map loads with OpenStreetMap tiles in <10 seconds")
    print("🔍 Geocoding finds major cities and landmarks")
    print("📐 Rectangle selection maintains coordinate precision")
    print("🏔️ Terrain generation uses Open Topo Data successfully")
    print("🚫 No Mapbox-related errors in console or server")
    print()
    
    print("📊 PERFORMANCE BENCHMARKS:")
    print("-" * 30)
    print("• Initial map load: <10 seconds")
    print("• Geocoding response: <3 seconds")
    print("• Rectangle drawing: Smooth, no lag")
    print("• Elevation data: <30 seconds for small areas")

def run_browser_tests():
    """Attempt to run browser-based tests."""
    print("\n🚀 Attempting to open browser tests...")
    
    try:
        # Open browser to the application
        webbrowser.open('http://localhost:8080')
        print("✓ Browser opened to http://localhost:8080")
        
        print("\n⏱️ Waiting 5 seconds for page load...")
        time.sleep(5)
        
        print("📝 Please follow the test guide above to verify:")
        print("  1. Map loading with MapLibre GL")
        print("  2. Geocoding functionality")
        print("  3. Rectangle selection precision")
        print("  4. Terrain generation with Open Topo Data")
        
        print("\n🔍 While testing, check browser console for any errors:")
        print("  Press F12 → Console tab → Look for red error messages")
        
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print("Please manually open http://localhost:8080")

def test_api_endpoints():
    """Test the Flask API endpoints."""
    print("\n🔧 Testing API Endpoints...")
    
    try:
        import requests
        base_url = "http://localhost:8080"
        
        print("1. Testing task status endpoint...")
        response = requests.get(f"{base_url}/task-status", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Task status API working: {data}")
        else:
            print(f"✗ Task status API failed: {response.status_code}")
        
        print("\n2. Testing static file serving...")
        response = requests.get(f"{base_url}/main.js", timeout=5)
        
        if response.status_code == 200:
            print("✓ Static file serving working")
            
            # Check for MapLibre GL in JavaScript
            if 'maplibregl' in response.text:
                print("✓ MapLibre GL found in JavaScript")
            else:
                print("⚠️ MapLibre GL not found in JavaScript")
                
            if 'mapboxgl' in response.text:
                print("⚠️ MapboxGL remnants found in JavaScript")
            else:
                print("✓ MapboxGL successfully removed from JavaScript")
        else:
            print(f"✗ Static file serving failed: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ API endpoint test failed: {e}")
        print("Make sure the server is running at http://localhost:8080")

def main():
    """Main test function."""
    print_test_guide()
    test_api_endpoints()
    
    # Ask user if they want to open browser
    print("\n" + "="*60)
    response = input("🌐 Open browser for testing? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        run_browser_tests()
    else:
        print("Manual testing: Please open http://localhost:8080 in your browser")
        print("Follow the test guide above to validate the migration.")

if __name__ == '__main__':
    main()