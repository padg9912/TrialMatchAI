"""
Geographic Matching Module
Handles location-based filtering and distance calculations for clinical trials
"""

import re
import math
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
import requests
import json

@dataclass
class Location:
    """Represents a geographic location"""
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    country: str
    zip_code: Optional[str] = None

@dataclass
class TrialLocation:
    """Represents a clinical trial location"""
    facility_name: str
    location: Location
    contact_info: Optional[Dict] = None
    site_status: str = "active"  # active, recruiting, closed

class GeographicMatcher:
    """
    Handles geographic matching and distance calculations for clinical trials
    """
    
    def __init__(self):
        # Default maximum distances (in miles)
        self.max_distances = {
            'local': 25,      # Local area
            'regional': 100,  # Regional area
            'national': 500,  # National travel
            'international': float('inf')  # International
        }
        
        # Common city/state mappings for US
        self.us_cities = {
            'new york': {'state': 'NY', 'lat': 40.7128, 'lon': -74.0060},
            'los angeles': {'state': 'CA', 'lat': 34.0522, 'lon': -118.2437},
            'chicago': {'state': 'IL', 'lat': 41.8781, 'lon': -87.6298},
            'houston': {'state': 'TX', 'lat': 29.7604, 'lon': -95.3698},
            'phoenix': {'state': 'AZ', 'lat': 33.4484, 'lon': -112.0740},
            'philadelphia': {'state': 'PA', 'lat': 39.9526, 'lon': -75.1652},
            'san antonio': {'state': 'TX', 'lat': 29.4241, 'lon': -98.4936},
            'san diego': {'state': 'CA', 'lat': 32.7157, 'lon': -117.1611},
            'dallas': {'state': 'TX', 'lat': 32.7767, 'lon': -96.7970},
            'san jose': {'state': 'CA', 'lat': 37.3382, 'lon': -121.8863},
            'austin': {'state': 'TX', 'lat': 30.2672, 'lon': -97.7431},
            'jacksonville': {'state': 'FL', 'lat': 30.3322, 'lon': -81.6557},
            'fort worth': {'state': 'TX', 'lat': 32.7555, 'lon': -97.3308},
            'columbus': {'state': 'OH', 'lat': 39.9612, 'lon': -82.9988},
            'charlotte': {'state': 'NC', 'lat': 35.2271, 'lon': -80.8431},
            'seattle': {'state': 'WA', 'lat': 47.6062, 'lon': -122.3321},
            'denver': {'state': 'CO', 'lat': 39.7392, 'lon': -104.9903},
            'boston': {'state': 'MA', 'lat': 42.3601, 'lon': -71.0589},
            'detroit': {'state': 'MI', 'lat': 42.3314, 'lon': -83.0458},
            'nashville': {'state': 'TN', 'lat': 36.1627, 'lon': -86.7816}
        }
        
        # State abbreviations
        self.state_abbreviations = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
            'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
            'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
            'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
            'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
            'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
            'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
            'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
        }
    
    def parse_location_string(self, location_str: str) -> Optional[Location]:
        """
        Parse a location string into a Location object
        
        Args:
            location_str: Location string (e.g., "New York, NY" or "Los Angeles, CA, USA")
            
        Returns:
            Location object or None if parsing fails
        """
        if not location_str or not location_str.strip():
            return None
        
        location_str = location_str.strip().lower()
        
        # Try to extract components using regex
        # Pattern: City, State/Province, Country
        pattern = r'([^,]+),\s*([^,]+)(?:,\s*([^,]+))?'
        match = re.search(pattern, location_str)
        
        if not match:
            # Try simple city, state pattern
            parts = location_str.split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                state_country = parts[1].strip()
                
                # Check if it's a US state
                if state_country in self.state_abbreviations.values() or state_country in self.state_abbreviations:
                    state = state_country if state_country in self.state_abbreviations.values() else self.state_abbreviations.get(state_country, state_country)
                    country = "USA"
                else:
                    state = state_country
                    country = parts[2].strip() if len(parts) > 2 else "Unknown"
            else:
                return None
        else:
            city = match.group(1).strip()
            state = match.group(2).strip()
            country = match.group(3).strip() if match.group(3) else "Unknown"
        
        # Get coordinates
        coordinates = self._get_coordinates(city, state, country)
        
        if coordinates:
            return Location(
                latitude=coordinates['lat'],
                longitude=coordinates['lon'],
                address=location_str.title(),
                city=city.title(),
                state=state.upper(),
                country=country.title(),
                zip_code=self._extract_zip_code(location_str)
            )
        
        return None
    
    def _get_coordinates(self, city: str, state: str, country: str) -> Optional[Dict]:
        """Get latitude and longitude for a location"""
        city_lower = city.lower()
        
        # Check our known cities first
        if city_lower in self.us_cities:
            return {
                'lat': self.us_cities[city_lower]['lat'],
                'lon': self.us_cities[city_lower]['lon']
            }
        
        # Try to use a geocoding service (free tier)
        try:
            # Using Nominatim (OpenStreetMap) - free but rate limited
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': f"{city}, {state}, {country}",
                'format': 'json',
                'limit': 1
            }
            headers = {'User-Agent': 'TrialMatchAI/2.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        'lat': float(data[0]['lat']),
                        'lon': float(data[0]['lon'])
                    }
        except Exception as e:
            print(f"Geocoding error: {e}")
        
        return None
    
    def _extract_zip_code(self, location_str: str) -> Optional[str]:
        """Extract zip code from location string"""
        zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
        match = re.search(zip_pattern, location_str)
        return match.group(0) if match else None
    
    def calculate_distance(self, location1: Location, location2: Location) -> float:
        """
        Calculate distance between two locations using Haversine formula
        
        Args:
            location1: First location
            location2: Second location
            
        Returns:
            Distance in miles
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = math.radians(location1.latitude), math.radians(location1.longitude)
        lat2, lon2 = math.radians(location2.latitude), math.radians(location2.longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in miles
        earth_radius = 3959
        
        return earth_radius * c
    
    def filter_trials_by_location(
        self, 
        trials_df, 
        patient_location: Union[str, Location], 
        max_distance_miles: float = 100,
        distance_category: str = "regional"
    ) -> pd.DataFrame:
        """
        Filter clinical trials based on geographic proximity
        
        Args:
            trials_df: DataFrame containing trial data with location information
            patient_location: Patient's location (string or Location object)
            max_distance_miles: Maximum acceptable distance in miles
            distance_category: Category of distance (local, regional, national, international)
            
        Returns:
            Filtered DataFrame with distance information
        """
        if trials_df.empty:
            return trials_df
        
        # Parse patient location if it's a string
        if isinstance(patient_location, str):
            patient_loc = self.parse_location_string(patient_location)
            if not patient_loc:
                print(f"Could not parse patient location: {patient_location}")
                return trials_df
        else:
            patient_loc = patient_location
        
        # Calculate distances and filter
        filtered_trials = []
        
        for _, trial in trials_df.iterrows():
            trial_locations = self._extract_trial_locations(trial)
            
            if not trial_locations:
                continue
            
            # Find the closest location for this trial
            min_distance = float('inf')
            closest_location = None
            
            for trial_loc in trial_locations:
                if trial_loc.location:
                    distance = self.calculate_distance(patient_loc, trial_loc.location)
                    if distance < min_distance:
                        min_distance = distance
                        closest_location = trial_loc
            
            # Check if trial is within acceptable distance
            if min_distance <= max_distance_miles:
                trial_copy = trial.copy()
                trial_copy['distance_miles'] = min_distance
                trial_copy['closest_facility'] = closest_location.facility_name if closest_location else "Unknown"
                trial_copy['closest_location'] = closest_location.location.address if closest_location else "Unknown"
                trial_copy['travel_category'] = self._categorize_distance(min_distance)
                filtered_trials.append(trial_copy)
        
        if filtered_trials:
            filtered_df = pd.DataFrame(filtered_trials)
            # Sort by distance
            filtered_df = filtered_df.sort_values('distance_miles')
            return filtered_df
        else:
            return pd.DataFrame()
    
    def _extract_trial_locations(self, trial_row) -> List[TrialLocation]:
        """Extract location information from a trial row"""
        locations = []
        
        # Try to extract from Locations column
        locations_str = str(trial_row.get('Locations', ''))
        
        if locations_str and locations_str != 'nan':
            # Split by semicolon or other separators
            location_strings = re.split(r'[;|]', locations_str)
            
            for loc_str in location_strings:
                loc_str = loc_str.strip()
                if loc_str:
                    # Try to parse facility name and location
                    # Pattern: "Facility Name, City, State, Country"
                    parts = loc_str.split(',')
                    
                    if len(parts) >= 2:
                        facility_name = parts[0].strip()
                        location_str = ','.join(parts[1:]).strip()
                        
                        parsed_location = self.parse_location_string(location_str)
                        
                        if parsed_location:
                            trial_location = TrialLocation(
                                facility_name=facility_name,
                                location=parsed_location,
                                site_status="active"  # Default status
                            )
                            locations.append(trial_location)
        
        return locations
    
    def _categorize_distance(self, distance_miles: float) -> str:
        """Categorize distance into travel categories"""
        if distance_miles <= 25:
            return "local"
        elif distance_miles <= 100:
            return "regional"
        elif distance_miles <= 500:
            return "national"
        else:
            return "international"
    
    def get_location_statistics(self, trials_df: pd.DataFrame) -> Dict:
        """
        Get statistics about trial locations
        
        Args:
            trials_df: DataFrame containing trial data
            
        Returns:
            Dictionary with location statistics
        """
        if trials_df.empty:
            return {}
        
        stats = {
            'total_trials': len(trials_df),
            'trials_with_locations': 0,
            'unique_cities': set(),
            'unique_states': set(),
            'unique_countries': set(),
            'distance_categories': {
                'local': 0,
                'regional': 0,
                'national': 0,
                'international': 0
            }
        }
        
        for _, trial in trials_df.iterrows():
            locations_str = str(trial.get('Locations', ''))
            
            if locations_str and locations_str != 'nan':
                stats['trials_with_locations'] += 1
                
                # Extract cities, states, countries
                location_strings = re.split(r'[;|]', locations_str)
                
                for loc_str in location_strings:
                    loc_str = loc_str.strip()
                    if loc_str:
                        parts = loc_str.split(',')
                        if len(parts) >= 2:
                            city = parts[1].strip().title() if len(parts) > 1 else ""
                            state = parts[2].strip().upper() if len(parts) > 2 else ""
                            country = parts[3].strip().title() if len(parts) > 3 else ""
                            
                            if city:
                                stats['unique_cities'].add(city)
                            if state:
                                stats['unique_states'].add(state)
                            if country:
                                stats['unique_countries'].add(country)
            
            # Count distance categories if available
            distance_category = trial.get('travel_category', '')
            if distance_category in stats['distance_categories']:
                stats['distance_categories'][distance_category] += 1
        
        # Convert sets to counts
        stats['unique_cities_count'] = len(stats['unique_cities'])
        stats['unique_states_count'] = len(stats['unique_states'])
        stats['unique_countries_count'] = len(stats['unique_countries'])
        
        # Remove sets from final output
        del stats['unique_cities']
        del stats['unique_states']
        del stats['unique_countries']
        
        return stats
    
    def suggest_alternative_locations(
        self, 
        patient_location: Union[str, Location], 
        trials_df: pd.DataFrame,
        max_suggestions: int = 5
    ) -> List[Dict]:
        """
        Suggest alternative locations for trials that might be worth traveling to
        
        Args:
            patient_location: Patient's location
            trials_df: DataFrame containing trial data
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested locations with trial counts
        """
        if isinstance(patient_location, str):
            patient_loc = self.parse_location_string(patient_location)
            if not patient_loc:
                return []
        else:
            patient_loc = patient_location
        
        location_counts = {}
        
        # Count trials by location
        for _, trial in trials_df.iterrows():
            locations_str = str(trial.get('Locations', ''))
            
            if locations_str and locations_str != 'nan':
                location_strings = re.split(r'[;|]', locations_str)
                
                for loc_str in location_strings:
                    loc_str = loc_str.strip()
                    if loc_str:
                        parts = loc_str.split(',')
                        if len(parts) >= 2:
                            city_state = f"{parts[1].strip().title()}, {parts[2].strip().upper()}"
                            
                            if city_state not in location_counts:
                                location_counts[city_state] = {
                                    'location': city_state,
                                    'trial_count': 0,
                                    'distance': None
                                }
                            
                            location_counts[city_state]['trial_count'] += 1
        
        # Calculate distances and filter
        suggestions = []
        for city_state, data in location_counts.items():
            if data['trial_count'] >= 3:  # Only suggest locations with multiple trials
                # Parse location to get coordinates
                parsed_loc = self.parse_location_string(city_state)
                if parsed_loc:
                    distance = self.calculate_distance(patient_loc, parsed_loc)
                    
                    if distance <= 500:  # Within reasonable travel distance
                        suggestions.append({
                            'location': city_state,
                            'trial_count': data['trial_count'],
                            'distance_miles': round(distance, 1),
                            'travel_category': self._categorize_distance(distance)
                        })
        
        # Sort by trial count (descending) and distance (ascending)
        suggestions.sort(key=lambda x: (-x['trial_count'], x['distance_miles']))
        
        return suggestions[:max_suggestions]

# Example usage and testing
if __name__ == "__main__":
    # Test the geographic matcher
    matcher = GeographicMatcher()
    
    print("Testing Geographic Matcher...")
    
    # Test location parsing
    test_locations = [
        "New York, NY",
        "Los Angeles, CA, USA",
        "Chicago, IL",
        "Houston, TX"
    ]
    
    for loc_str in test_locations:
        location = matcher.parse_location_string(loc_str)
        if location:
            print(f" Parsed '{loc_str}': {location.city}, {location.state} ({location.latitude:.4f}, {location.longitude:.4f})")
        else:
            print(f" Failed to parse '{loc_str}'")
    
    # Test distance calculation
    if len(test_locations) >= 2:
        loc1 = matcher.parse_location_string(test_locations[0])
        loc2 = matcher.parse_location_string(test_locations[1])
        
        if loc1 and loc2:
            distance = matcher.calculate_distance(loc1, loc2)
            print(f" Distance between {loc1.city} and {loc2.city}: {distance:.1f} miles")
    
    # Test location statistics
    print(f"\nLocation Statistics:")
    print(f"Known US cities: {len(matcher.us_cities)}")
    print(f"State abbreviations: {len(matcher.state_abbreviations)}")
    print(f"Max distances: {matcher.max_distances}")
