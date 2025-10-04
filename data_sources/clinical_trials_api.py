"""
Clinical Trials API Integration Module
Real-time data fetching from ClinicalTrials.gov API
"""

import requests
import pandas as pd
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

class ClinicalTrialsAPI:
    """
    ClinicalTrials.gov API client for real-time trial data fetching
    """
    
    def __init__(self):
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TrialMatchAI/2.0 (Healthcare AI Application)',
            'Accept': 'application/json'
        })
        
    def search_trials(
        self, 
        condition: Optional[str] = None,
        location: Optional[str] = None,
        age_range: Optional[tuple] = None,
        study_phase: Optional[str] = None,
        study_type: Optional[str] = None,
        status: str = "RECRUITING",
        limit: int = 1000
    ) -> Dict:
        """
        Search for clinical trials based on criteria
        
        Args:
            condition: Medical condition (e.g., "breast cancer")
            location: Geographic location
            age_range: Tuple of (min_age, max_age)
            study_phase: Phase of study (e.g., "PHASE1", "PHASE2")
            study_type: Type of study (e.g., "INTERVENTIONAL")
            status: Study status (e.g., "RECRUITING", "ACTIVE_NOT_RECRUITING")
            limit: Maximum number of results
            
        Returns:
            Dictionary containing trial data
        """
        
        # Build query parameters
        params = {
            'format': 'json',
            'query.term': condition or "",
            'filter.overallStatus': status,
            'pageSize': min(limit, 1000),  # API limit is 1000 per request
            'pageToken': ""
        }
        
        # Add optional filters
        if location:
            params['filter.locations'] = location
            
        if study_phase:
            params['filter.phase'] = study_phase
            
        if study_type:
            params['filter.studyType'] = study_type
            
        if age_range:
            params['filter.ageGroup'] = f"{age_range[0]}-{age_range[1]}"
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching trials: {e}")
            return {"studies": []}
    
    def get_trial_details(self, nct_id: str) -> Dict:
        """
        Get detailed information for a specific trial
        
        Args:
            nct_id: NCT identifier (e.g., "NCT04414150")
            
        Returns:
            Dictionary containing detailed trial information
        """
        url = f"{self.base_url}/{nct_id}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching trial details for {nct_id}: {e}")
            return {}
    
    def extract_trial_info(self, trial_data: Dict) -> Dict:
        """
        Extract relevant information from trial data
        
        Args:
            trial_data: Raw trial data from API
            
        Returns:
            Processed trial information
        """
        try:
            protocol_section = trial_data.get('protocolSection', {})
            identification_module = protocol_section.get('identificationModule', {})
            status_module = protocol_section.get('statusModule', {})
            design_module = protocol_section.get('designModule', {})
            eligibility_module = protocol_section.get('eligibilityModule', {})
            conditions_module = protocol_section.get('conditionsModule', {})
            contacts_location_module = protocol_section.get('contactsLocationsModule', {})
            
            # Extract basic information
            trial_info = {
                'NCT Number': identification_module.get('nctId', ''),
                'Study Title': identification_module.get('briefTitle', ''),
                'Study URL': f"https://clinicaltrials.gov/study/{identification_module.get('nctId', '')}",
                'Study Status': status_module.get('overallStatus', ''),
                'Brief Summary': protocol_section.get('descriptionModule', {}).get('briefSummary', ''),
                
                # Conditions and interventions
                'Conditions': ', '.join(conditions_module.get('conditions', [])),
                'Interventions': self._extract_interventions(protocol_section.get('armsInterventionsModule', {})),
                
                # Demographics
                'Sex': eligibility_module.get('sex', 'ALL'),
                'Age': self._extract_age_criteria(eligibility_module),
                'Phases': ', '.join(design_module.get('phases', [])),
                'Study Type': design_module.get('studyType', ''),
                
                # Timeline
                'Start Date': status_module.get('startDateStruct', {}).get('date', ''),
                'Completion Date': status_module.get('primaryCompletionDateStruct', {}).get('date', ''),
                
                # Locations
                'Locations': self._extract_locations(contacts_location_module),
                
                # Eligibility criteria
                'Inclusion Criteria': eligibility_module.get('inclusionCriteria', ''),
                'Exclusion Criteria': eligibility_module.get('exclusionCriteria', ''),
                
                # Additional metadata
                'Last Updated': datetime.now().isoformat(),
                'Data Source': 'ClinicalTrials.gov API'
            }
            
            return trial_info
            
        except Exception as e:
            print(f"Error extracting trial info: {e}")
            return {}
    
    def _extract_interventions(self, arms_interventions_module: Dict) -> str:
        """Extract intervention information"""
        interventions = []
        
        try:
            interventions_list = arms_interventions_module.get('interventions', [])
            for intervention in interventions_list:
                intervention_name = intervention.get('name', '')
                intervention_type = intervention.get('type', '')
                if intervention_name:
                    interventions.append(f"{intervention_type}: {intervention_name}")
        except:
            pass
            
        return '; '.join(interventions)
    
    def _extract_age_criteria(self, eligibility_module: Dict) -> str:
        """Extract age criteria"""
        try:
            minimum_age = eligibility_module.get('minimumAge', '')
            maximum_age = eligibility_module.get('maximumAge', '')
            
            if minimum_age and maximum_age:
                return f"{minimum_age} - {maximum_age}"
            elif minimum_age:
                return f"{minimum_age} and older"
            elif maximum_age:
                return f"up to {maximum_age}"
            else:
                return "Not specified"
        except:
            return "Not specified"
    
    def _extract_locations(self, contacts_location_module: Dict) -> str:
        """Extract location information"""
        locations = []
        
        try:
            facilities = contacts_location_module.get('facilities', [])
            for facility in facilities:
                facility_name = facility.get('name', '')
                facility_city = facility.get('city', '')
                facility_state = facility.get('state', '')
                facility_country = facility.get('country', '')
                
                location_parts = [facility_city, facility_state, facility_country]
                location_parts = [part for part in location_parts if part]
                
                if location_parts:
                    locations.append(f"{facility_name}, {', '.join(location_parts)}")
        except:
            pass
            
        return '; '.join(locations)
    
    def fetch_cancer_trials(self, limit: int = 1000) -> pd.DataFrame:
        """
        Fetch cancer-related clinical trials
        
        Args:
            limit: Maximum number of trials to fetch
            
        Returns:
            DataFrame containing cancer trials
        """
        print("Fetching cancer trials from ClinicalTrials.gov...")
        
        # Common cancer types to search for
        cancer_conditions = [
            "breast cancer",
            "lung cancer", 
            "prostate cancer",
            "colorectal cancer",
            "pancreatic cancer",
            "ovarian cancer",
            "brain cancer",
            "liver cancer",
            "kidney cancer",
            "bladder cancer",
            "leukemia",
            "lymphoma",
            "melanoma"
        ]
        
        all_trials = []
        
        for condition in cancer_conditions:
            print(f"   Searching for {condition} trials...")
            
            try:
                # Search for trials
                response_data = self.search_trials(
                    condition=condition,
                    status="RECRUITING",
                    limit=100  # Limit per condition to avoid overwhelming API
                )
                
                studies = response_data.get('studies', [])
                print(f"     Found {len(studies)} trials for {condition}")
                
                # Process each trial
                for study in studies:
                    trial_info = self.extract_trial_info(study)
                    if trial_info:
                        all_trials.append(trial_info)
                
                # Be respectful to the API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"     Error fetching {condition}: {e}")
                continue
        
        print(f" Total trials fetched: {len(all_trials)}")
        
        # Convert to DataFrame and remove duplicates
        if all_trials:
            df = pd.DataFrame(all_trials)
            df = df.drop_duplicates(subset=['NCT Number'])
            print(f" Unique trials after deduplication: {len(df)}")
            return df
        else:
            return pd.DataFrame()
    
    def update_trial_database(self, csv_path: str = "datasets/cancer_studies.csv") -> bool:
        """
        Update the local trial database with fresh data from API
        
        Args:
            csv_path: Path to save the updated CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch fresh data
            trials_df = self.fetch_cancer_trials(limit=2000)
            
            if not trials_df.empty:
                # Save to CSV
                trials_df.to_csv(csv_path, index=False)
                print(f" Updated trial database saved to {csv_path}")
                return True
            else:
                print(" No trials fetched, database not updated")
                return False
                
        except Exception as e:
            print(f" Error updating database: {e}")
            return False

# Utility functions for data management
def load_fresh_trial_data(force_update: bool = False) -> pd.DataFrame:
    """
    Load trial data, optionally updating from API
    
    Args:
        force_update: If True, fetch fresh data from API
        
    Returns:
        DataFrame containing trial data
    """
    csv_path = "datasets/cancer_studies.csv"
    
    # Check if we should update the data
    if force_update:
        print("🔄 Forcing data update from ClinicalTrials.gov...")
        api = ClinicalTrialsAPI()
        success = api.update_trial_database(csv_path)
        
        if not success:
            print(" API update failed, loading existing data...")
    
    try:
        # Load from CSV
        df = pd.read_csv(csv_path)
        print(f" Loaded {len(df)} trials from database")
        return df
        
    except FileNotFoundError:
        print(" No existing database found, fetching fresh data...")
        api = ClinicalTrialsAPI()
        api.update_trial_database(csv_path)
        
        try:
            return pd.read_csv(csv_path)
        except:
            return pd.DataFrame()

def get_trial_statistics(df: pd.DataFrame) -> Dict:
    """
    Get statistics about the trial database
    
    Args:
        df: DataFrame containing trial data
        
    Returns:
        Dictionary with statistics
    """
    if df.empty:
        return {}
    
    stats = {
        'total_trials': len(df),
        'recruiting_trials': len(df[df['Study Status'] == 'RECRUITING']),
        'active_trials': len(df[df['Study Status'].isin(['RECRUITING', 'ACTIVE_NOT_RECRUITING'])]),
        'completed_trials': len(df[df['Study Status'] == 'COMPLETED']),
        'phase_1_trials': len(df[df['Phases'].str.contains('PHASE1', na=False)]),
        'phase_2_trials': len(df[df['Phases'].str.contains('PHASE2', na=False)]),
        'phase_3_trials': len(df[df['Phases'].str.contains('PHASE3', na=False)]),
        'interventional_trials': len(df[df['Study Type'] == 'INTERVENTIONAL']),
        'observational_trials': len(df[df['Study Type'] == 'OBSERVATIONAL'])
    }
    
    return stats

# Example usage and testing
if __name__ == "__main__":
    # Test the API integration
    api = ClinicalTrialsAPI()
    
    # Test search functionality
    print("Testing ClinicalTrials.gov API integration...")
    
    # Search for breast cancer trials
    response = api.search_trials(condition="breast cancer", limit=5)
    studies = response.get('studies', [])
    
    print(f"Found {len(studies)} breast cancer trials")
    
    if studies:
        # Extract info from first trial
        trial_info = api.extract_trial_info(studies[0])
        print(f"Sample trial: {trial_info.get('Study Title', 'N/A')}")
    
    # Test database update
    print("\nTesting database update...")
    success = api.update_trial_database()
    print(f"Database update successful: {success}")
