"""
Custom geocoding service with landmark database fallback.
Provides location search without external API dependencies for high-frequency queries.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class LandmarkDatabase:
    """Local landmark database for offline geocoding."""
    
    def __init__(self):
        self.landmarks = self._load_landmarks()
    
    def _load_landmarks(self) -> List[Dict]:
        """Load landmark database from JSON file."""
        landmarks_file = Path(__file__).parent / 'landmarks.json'
        
        # Create default landmarks if file doesn't exist
        if not landmarks_file.exists():
            self._create_default_landmarks(landmarks_file)
        
        try:
            with open(landmarks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return self._get_default_landmarks()
    
    def _create_default_landmarks(self, file_path: Path):
        """Create default landmarks database."""
        landmarks = self._get_default_landmarks()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(landmarks, f, indent=2, ensure_ascii=False)
        except IOError:
            pass  # Continue with in-memory landmarks
    
    def _get_default_landmarks(self) -> List[Dict]:
        """Get default landmark database."""
        return [
            # Major world cities
            {"name": "New York", "lat": 40.7128, "lng": -74.0060, "type": "city", "country": "US"},
            {"name": "Los Angeles", "lat": 34.0522, "lng": -118.2437, "type": "city", "country": "US"},
            {"name": "London", "lat": 51.5074, "lng": -0.1278, "type": "city", "country": "GB"},
            {"name": "Paris", "lat": 48.8566, "lng": 2.3522, "type": "city", "country": "FR"},
            {"name": "Tokyo", "lat": 35.6762, "lng": 139.6503, "type": "city", "country": "JP"},
            {"name": "Sydney", "lat": -33.8688, "lng": 151.2093, "type": "city", "country": "AU"},
            {"name": "San Francisco", "lat": 37.7749, "lng": -122.4194, "type": "city", "country": "US"},
            {"name": "Chicago", "lat": 41.8781, "lng": -87.6298, "type": "city", "country": "US"},
            {"name": "Berlin", "lat": 52.5200, "lng": 13.4050, "type": "city", "country": "DE"},
            {"name": "Moscow", "lat": 55.7558, "lng": 37.6176, "type": "city", "country": "RU"},
            
            # Major airports
            {"name": "JFK Airport", "lat": 40.6413, "lng": -73.7781, "type": "airport", "country": "US"},
            {"name": "LAX Airport", "lat": 33.9425, "lng": -118.4081, "type": "airport", "country": "US"},
            {"name": "Heathrow Airport", "lat": 51.4700, "lng": -0.4543, "type": "airport", "country": "GB"},
            {"name": "Charles de Gaulle Airport", "lat": 49.0097, "lng": 2.5479, "type": "airport", "country": "FR"},
            {"name": "Haneda Airport", "lat": 35.5494, "lng": 139.7798, "type": "airport", "country": "JP"},
            
            # Landmarks and geographical features
            {"name": "Grand Canyon", "lat": 36.0544, "lng": -112.1401, "type": "landmark", "country": "US"},
            {"name": "Mount Everest", "lat": 27.9881, "lng": 86.9250, "type": "landmark", "country": "NP"},
            {"name": "Eiffel Tower", "lat": 48.8584, "lng": 2.2945, "type": "landmark", "country": "FR"},
            {"name": "Statue of Liberty", "lat": 40.6892, "lng": -74.0445, "type": "landmark", "country": "US"},
            {"name": "Golden Gate Bridge", "lat": 37.8199, "lng": -122.4783, "type": "landmark", "country": "US"},
            {"name": "Niagara Falls", "lat": 43.0962, "lng": -79.0377, "type": "landmark", "country": "CA"},
            
            # Universities and institutions
            {"name": "Harvard University", "lat": 42.3736, "lng": -71.1097, "type": "university", "country": "US"},
            {"name": "MIT", "lat": 42.3601, "lng": -71.0942, "type": "university", "country": "US"},
            {"name": "Stanford University", "lat": 37.4275, "lng": -122.1697, "type": "university", "country": "US"},
            {"name": "Oxford University", "lat": 51.7548, "lng": -1.2544, "type": "university", "country": "GB"},
            
            # Natural features for terrain testing
            {"name": "Yosemite Valley", "lat": 37.7459, "lng": -119.5936, "type": "landmark", "country": "US"},
            {"name": "Death Valley", "lat": 36.5323, "lng": -116.9325, "type": "landmark", "country": "US"},
            {"name": "Mount Fuji", "lat": 35.3606, "lng": 138.7274, "type": "landmark", "country": "JP"},
            {"name": "Alps", "lat": 46.5197, "lng": 9.0122, "type": "landmark", "country": "CH"},
            {"name": "Himalayas", "lat": 28.0000, "lng": 84.0000, "type": "landmark", "country": "NP"},
            {"name": "Rocky Mountains", "lat": 39.7392, "lng": -104.9903, "type": "landmark", "country": "US"},
            
            # Coastal areas for terrain variety
            {"name": "Malibu Beach", "lat": 34.0259, "lng": -118.7798, "type": "landmark", "country": "US"},
            {"name": "Bondi Beach", "lat": -33.8915, "lng": 151.2767, "type": "landmark", "country": "AU"},
            {"name": "Copacabana Beach", "lat": -22.9711, "lng": -43.1822, "type": "landmark", "country": "BR"},
        ]
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search landmarks by name.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            
        Returns:
            List[Dict]: Matching landmarks with score
        """
        query_lower = query.lower().strip()
        results = []
        
        for landmark in self.landmarks:
            score = self._calculate_match_score(query_lower, landmark)
            if score > 0:
                result = landmark.copy()
                result['score'] = score
                results.append(result)
        
        # Sort by score (descending) and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def _calculate_match_score(self, query: str, landmark: Dict) -> float:
        """
        Calculate match score between query and landmark.
        
        Args:
            query (str): Search query (lowercase)
            landmark (Dict): Landmark data
            
        Returns:
            float: Match score (0 = no match, 1 = perfect match)
        """
        name_lower = landmark['name'].lower()
        
        # Exact match
        if query == name_lower:
            return 1.0
        
        # Starts with query
        if name_lower.startswith(query):
            return 0.9
        
        # Contains query
        if query in name_lower:
            return 0.7
        
        # Word boundary matches (better for multi-word names)
        words = name_lower.split()
        for word in words:
            if word.startswith(query):
                return 0.8
            if query in word:
                return 0.6
        
        # Fuzzy matching for typos (simple version)
        if len(query) >= 3:
            # Check if query is similar to any word in the name
            for word in words:
                if self._similar_strings(query, word):
                    return 0.5
        
        return 0.0
    
    def _similar_strings(self, s1: str, s2: str, threshold: float = 0.7) -> bool:
        """
        Check if two strings are similar using simple edit distance.
        
        Args:
            s1, s2 (str): Strings to compare
            threshold (float): Similarity threshold (0-1)
            
        Returns:
            bool: True if strings are similar
        """
        if abs(len(s1) - len(s2)) > 2:
            return False
        
        # Simple edit distance calculation
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return len(s1) <= 2
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                cost = 0 if c1 == c2 else 1
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + cost
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        edit_distance = previous_row[-1]
        similarity = 1 - (edit_distance / max(len(s1), len(s2)))
        return similarity >= threshold


class CustomGeocoder:
    """
    Custom geocoding service with external API fallback.
    """
    
    def __init__(self):
        self.landmark_db = LandmarkDatabase()
        self.cache = {}
    
    def search(self, query: str, use_external: bool = True) -> List[Dict]:
        """
        Search for locations using local database and optional external APIs.
        
        Args:
            query (str): Location search query
            use_external (bool): Whether to use external APIs as fallback
            
        Returns:
            List[Dict]: Search results with lat, lng, name, and source
        """
        # Check cache first
        cache_key = query.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        results = []
        
        # Search local landmark database
        local_results = self.landmark_db.search(query, limit=5)
        for landmark in local_results:
            results.append({
                'name': landmark['name'],
                'lat': landmark['lat'],
                'lng': landmark['lng'],
                'type': landmark.get('type', 'landmark'),
                'country': landmark.get('country', ''),
                'source': 'local_database',
                'score': landmark['score']
            })
        
        # If we have good local matches, use them
        if results and results[0]['score'] >= 0.8:
            self.cache[cache_key] = results
            return results
        
        # Fallback to external APIs if enabled and no good local matches
        if use_external and (not results or results[0]['score'] < 0.5):
            external_results = self._search_external(query)
            
            # Merge results, prioritizing high-score local matches
            if external_results:
                # Add external results
                for ext_result in external_results:
                    results.append(ext_result)
                
                # Re-sort by relevance
                results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Cache results
        self.cache[cache_key] = results[:10]  # Keep top 10 results
        return results[:10]
    
    def _search_external(self, query: str) -> List[Dict]:
        """
        Search external geocoding APIs as fallback.
        Uses Nominatim (OpenStreetMap) API with rate limiting.
        
        Args:
            query (str): Search query
            
        Returns:
            List[Dict]: External search results
        """
        import requests
        import urllib3
        import time
        
        # Disable SSL warnings for this session
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        results = []
        
        try:
            # Nominatim API (free but rate-limited)
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': query,
                'format': 'json',
                'limit': 5,
                'accept-language': 'en'
            }
            
            headers = {
                'User-Agent': 'Gazebo-Terrain-Generator/1.0'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            for item in data:
                result = {
                    'name': item.get('display_name', query),
                    'lat': float(item['lat']),
                    'lng': float(item['lon']),
                    'type': item.get('type', 'place'),
                    'country': item.get('address', {}).get('country', ''),
                    'source': 'nominatim',
                    'score': 0.6  # External results get medium score
                }
                results.append(result)
            
            # Add small delay to respect rate limits
            time.sleep(0.1)
            
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"External geocoding failed: {e}")
        
        return results
    
    def get_coordinates(self, query: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a location query.
        
        Args:
            query (str): Location search query
            
        Returns:
            Optional[Tuple[float, float]]: (lat, lng) or None if not found
        """
        results = self.search(query, use_external=True)
        
        if results:
            return (results[0]['lat'], results[0]['lng'])
        return None
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Simple reverse geocoding using landmark database.
        
        Args:
            lat, lng (float): Coordinates
            
        Returns:
            Optional[str]: Nearest landmark name or None
        """
        min_distance = float('inf')
        nearest_landmark = None
        
        for landmark in self.landmark_db.landmarks:
            # Simple distance calculation (not considering Earth curvature)
            distance = ((lat - landmark['lat']) ** 2 + (lng - landmark['lng']) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_landmark = landmark
        
        # Return nearest landmark if within reasonable distance
        if nearest_landmark and min_distance < 1.0:  # ~100km threshold
            return nearest_landmark['name']
        
        return None


# Global geocoder instance
custom_geocoder = CustomGeocoder()