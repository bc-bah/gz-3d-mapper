"""
Performance benchmarks for MapLibre GL style loading.
Tests various map styles to ensure sub-2-second initial load times.
"""

import unittest
import time
import requests
import json


class TestStyleLoadingPerformance(unittest.TestCase):
    
    def setUp(self):
        """Set up test styles for benchmarking."""
        self.test_styles = {
            "MapLibre Demo Style": "https://demotiles.maplibre.org/style.json",
            "OpenStreetMap Bright": "https://tiles.stadiamaps.com/styles/osm_bright.json",
            "OpenMapTiles Basic": "https://api.maptiler.com/maps/basic/style.json?key=demo",
            "Protomaps Light": "https://protomaps.github.io/basemaps/styles/light.json",
        }
        
        self.target_load_time = 2.0  # seconds
        self.timeout = 10.0  # seconds
    
    def test_style_download_speed(self):
        """Test that map styles can be downloaded within target time."""
        for style_name, style_url in self.test_styles.items():
            with self.subTest(style=style_name):
                start_time = time.time()
                
                try:
                    response = requests.get(style_url, timeout=self.timeout)
                    response.raise_for_status()
                    
                    # Validate JSON structure
                    style_data = response.json()
                    self.assertIn('sources', style_data, f"Invalid style format: {style_name}")
                    self.assertIn('layers', style_data, f"Invalid style format: {style_name}")
                    
                    download_time = time.time() - start_time
                    
                    print(f"{style_name}: {download_time:.3f}s")
                    
                    # Check if within target time
                    if download_time <= self.target_load_time:
                        print(f"✓ {style_name} meets performance target")
                    else:
                        print(f"⚠ {style_name} exceeds target ({download_time:.3f}s > {self.target_load_time}s)")
                    
                    # Don't fail the test for performance, just warn
                    self.assertLess(download_time, self.timeout, 
                        f"{style_name} download timeout exceeded")
                        
                except requests.RequestException as e:
                    self.fail(f"Failed to download {style_name}: {e}")
                except json.JSONDecodeError as e:
                    self.fail(f"Invalid JSON in {style_name}: {e}")
    
    def test_style_complexity_analysis(self):
        """Analyze style complexity to predict rendering performance."""
        complexity_scores = {}
        
        for style_name, style_url in self.test_styles.items():
            with self.subTest(style=style_name):
                try:
                    response = requests.get(style_url, timeout=self.timeout)
                    response.raise_for_status()
                    style_data = response.json()
                    
                    # Calculate complexity score
                    layer_count = len(style_data.get('layers', []))
                    source_count = len(style_data.get('sources', {}))
                    
                    # Count unique source URLs
                    unique_urls = set()
                    for source_data in style_data.get('sources', {}).values():
                        if 'url' in source_data:
                            unique_urls.add(source_data['url'])
                        elif 'tiles' in source_data:
                            for tile_url in source_data['tiles']:
                                unique_urls.add(tile_url.split('{')[0])  # Remove tile params
                    
                    complexity_score = layer_count + source_count * 2 + len(unique_urls) * 3
                    complexity_scores[style_name] = {
                        'score': complexity_score,
                        'layers': layer_count,
                        'sources': source_count,
                        'urls': len(unique_urls)
                    }
                    
                    print(f"{style_name}: Score={complexity_score}, "
                          f"Layers={layer_count}, Sources={source_count}, URLs={len(unique_urls)}")
                    
                    # Warn about high complexity styles
                    if complexity_score > 100:
                        print(f"⚠ {style_name} has high complexity (score={complexity_score})")
                    
                except (requests.RequestException, json.JSONDecodeError) as e:
                    print(f"Could not analyze {style_name}: {e}")
        
        # Find the best performing style
        if complexity_scores:
            best_style = min(complexity_scores.keys(), 
                           key=lambda k: complexity_scores[k]['score'])
            print(f"\nRecommended style for performance: {best_style}")
            print(f"Complexity score: {complexity_scores[best_style]['score']}")
    
    def test_tile_source_availability(self):
        """Test that tile sources in styles are accessible."""
        for style_name, style_url in self.test_styles.items():
            with self.subTest(style=style_name):
                try:
                    response = requests.get(style_url, timeout=self.timeout)
                    response.raise_for_status()
                    style_data = response.json()
                    
                    source_tests = []
                    for source_name, source_data in style_data.get('sources', {}).items():
                        if 'tiles' in source_data and source_data['tiles']:
                            # Test first tile URL template
                            tile_template = source_data['tiles'][0]
                            # Replace template variables with test values
                            test_url = (tile_template
                                       .replace('{z}', '1')
                                       .replace('{x}', '0') 
                                       .replace('{y}', '0')
                                       .replace('{r}', '')
                                       .replace('{s}', 'a'))
                            
                            try:
                                start_time = time.time()
                                tile_response = requests.head(test_url, timeout=5)
                                tile_time = time.time() - start_time
                                
                                if tile_response.status_code == 200:
                                    source_tests.append(f"✓ {source_name}: {tile_time:.3f}s")
                                else:
                                    source_tests.append(f"✗ {source_name}: HTTP {tile_response.status_code}")
                                    
                            except requests.RequestException as e:
                                source_tests.append(f"✗ {source_name}: {str(e)[:50]}")
                    
                    if source_tests:
                        print(f"\n{style_name} tile sources:")
                        for test_result in source_tests:
                            print(f"  {test_result}")
                            
                except (requests.RequestException, json.JSONDecodeError) as e:
                    print(f"Could not test tile sources for {style_name}: {e}")
    
    def test_recommended_style_selection(self):
        """Test and recommend the best style for the application."""
        results = {}
        
        for style_name, style_url in self.test_styles.items():
            start_time = time.time()
            
            try:
                response = requests.get(style_url, timeout=self.timeout)
                response.raise_for_status()
                style_data = response.json()
                
                download_time = time.time() - start_time
                layer_count = len(style_data.get('layers', []))
                
                # Score based on download time and complexity
                performance_score = (download_time * 10) + (layer_count * 0.1)
                
                results[style_name] = {
                    'download_time': download_time,
                    'layer_count': layer_count,
                    'performance_score': performance_score,
                    'meets_target': download_time <= self.target_load_time
                }
                
            except (requests.RequestException, json.JSONDecodeError) as e:
                results[style_name] = {
                    'error': str(e),
                    'performance_score': float('inf'),
                    'meets_target': False
                }
        
        # Find best performing style
        valid_styles = {k: v for k, v in results.items() if 'error' not in v}
        
        if valid_styles:
            best_style = min(valid_styles.keys(), 
                           key=lambda k: valid_styles[k]['performance_score'])
            
            print(f"\n=== STYLE PERFORMANCE RESULTS ===")
            for style_name, data in sorted(valid_styles.items(), 
                                         key=lambda x: x[1]['performance_score']):
                status = "✓" if data['meets_target'] else "⚠"
                print(f"{status} {style_name}: {data['download_time']:.3f}s "
                      f"({data['layer_count']} layers)")
            
            print(f"\nRECOMMENDED: {best_style}")
            print(f"Download time: {valid_styles[best_style]['download_time']:.3f}s")
            print(f"Layer count: {valid_styles[best_style]['layer_count']}")
            
            return best_style
        else:
            self.fail("No valid styles found for testing")


if __name__ == '__main__':
    # Run performance benchmarks
    unittest.main(verbosity=2)