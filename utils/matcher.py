import pandas as pd
import re
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

def match_patient_to_trials(entities_dict: Dict[str, List[str]], trials_df: pd.DataFrame) -> pd.DataFrame:
    """
    Enhanced matching algorithm with confidence scores and weighted field matching.
    
    Args:
        entities_dict: Dictionary with categorized entities from NLP extraction
        trials_df: DataFrame containing clinical trials data
    
    Returns:
        DataFrame with top matching trials sorted by confidence score
    """
    if not entities_dict or not entities_dict.get("all_entities"):
        return pd.DataFrame()
    
    # Define field weights (higher = more important for matching)
    field_weights = {
        'Conditions': 3.0,    # Most important
        'Sex': 2.0,           # Very important
        'Age': 2.0,           # Very important
        'Phases': 1.5,        # Important
        'Study Status': 1.0,  # Somewhat important
        'Study Type': 0.5,    # Less important
        'Locations': 0.3      # Least important
    }
    
    # Extract entities for backward compatibility
    all_entities = entities_dict.get("all_entities", [])
    conditions = entities_dict.get("conditions", [])
    demographics = entities_dict.get("demographics", [])
    treatments = entities_dict.get("treatments", [])
    
    def calculate_confidence_score(row) -> Tuple[float, Dict[str, float]]:
        """
        Calculate confidence score for a trial match.
        Returns (total_score, field_scores)
        """
        field_scores = {}
        total_score = 0.0
        
        # Process each field with appropriate entity matching
        for field, weight in field_weights.items():
            if field not in row.index:
                continue
                
            field_value = str(row[field]).lower()
            field_score = 0.0
            
            if field == 'Conditions':
                # Match conditions with higher precision
                field_score = _match_conditions(field_value, conditions, all_entities)
            elif field == 'Sex':
                # Match sex/gender
                field_score = _match_sex(field_value, demographics, all_entities)
            elif field == 'Age':
                # Match age ranges
                field_score = _match_age(field_value, demographics, all_entities)
            elif field == 'Phases':
                # Match trial phases
                field_score = _match_phases(field_value, all_entities)
            else:
                # General text matching for other fields
                field_score = _match_general(field_value, all_entities)
            
            field_scores[field] = field_score
            total_score += field_score * weight
        
        return total_score, field_scores
    
    def _match_conditions(field_value: str, condition_entities: List[str], all_entities: List[str]) -> float:
        """Match cancer conditions with high precision."""
        score = 0.0
        
        # Direct condition matches (highest weight)
        for condition in condition_entities:
            if condition in field_value:
                score += 2.0
            # Fuzzy matching for similar conditions
            elif _fuzzy_match(condition, field_value, threshold=0.8):
                score += 1.5
        
        # General entity matches (lower weight)
        for entity in all_entities:
            if entity in field_value and entity not in condition_entities:
                score += 0.5
        
        return min(score, 5.0)  # Cap at 5.0
    
    def _match_sex(field_value: str, demo_entities: List[str], all_entities: List[str]) -> float:
        """Match patient sex/gender."""
        score = 0.0
        
        # Check for explicit sex matches
        sex_terms = ['male', 'female', 'm', 'f', 'men', 'women']
        for sex_term in sex_terms:
            if sex_term in field_value and sex_term in demo_entities:
                score += 2.0
            elif sex_term in field_value and any(sex in demo_entities for sex in ['male', 'female', 'm', 'f']):
                score += 1.5
        
        return min(score, 3.0)
    
    def _match_age(field_value: str, demo_entities: List[str], all_entities: List[str]) -> float:
        """Match patient age ranges."""
        score = 0.0
        
        # Extract age from entities
        patient_age = None
        for entity in demo_entities:
            age_match = re.search(r'(\d+)', entity)
            if age_match:
                patient_age = int(age_match.group(1))
                break
        
        if patient_age:
            # Check if age matches trial criteria
            age_terms = ['adult', 'older_adult', 'pediatric', 'child']
            for age_term in age_terms:
                if age_term in field_value:
                    if age_term == 'adult' and 18 <= patient_age <= 64:
                        score += 2.0
                    elif age_term == 'older_adult' and patient_age >= 65:
                        score += 2.0
                    elif age_term in ['pediatric', 'child'] and patient_age < 18:
                        score += 2.0
        
        return min(score, 3.0)
    
    def _match_phases(field_value: str, all_entities: List[str]) -> float:
        """Match trial phases."""
        score = 0.0
        
        phase_terms = ['phase1', 'phase2', 'phase3', 'phase4', 'phase i', 'phase ii', 'phase iii']
        for phase_term in phase_terms:
            if phase_term in field_value and phase_term in all_entities:
                score += 1.5
        
        return min(score, 2.0)
    
    def _match_general(field_value: str, entities: List[str]) -> float:
        """General text matching for other fields."""
        score = 0.0
        
        for entity in entities:
            if entity in field_value:
                score += 1.0
            elif _fuzzy_match(entity, field_value, threshold=0.7):
                score += 0.5
        
        return min(score, 3.0)
    
    def _fuzzy_match(text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two texts are similar using fuzzy matching."""
        return SequenceMatcher(None, text1, text2).ratio() >= threshold
    
    # Calculate scores for all trials
    trials_df = trials_df.copy()
    scores_and_details = trials_df.apply(calculate_confidence_score, axis=1)
    
    trials_df['confidence_score'] = [score for score, _ in scores_and_details]
    trials_df['field_scores'] = [details for _, details in scores_and_details]
    
    # Filter and sort results
    matches = trials_df[trials_df['confidence_score'] > 0]
    matches = matches.sort_values(by='confidence_score', ascending=False)
    
    # Add confidence percentage
    max_score = matches['confidence_score'].max() if len(matches) > 0 else 1
    matches['confidence_percentage'] = (matches['confidence_score'] / max_score * 100).round(1)
    
    return matches.head(20)

def get_match_explanation(row: pd.Series) -> str:
    """
    Generate human-readable explanation for why a trial matched.
    """
    if 'field_scores' not in row:
        return "No matching details available."
    
    field_scores = row['field_scores']
    explanations = []
    
    for field, score in field_scores.items():
        if score > 0:
            if field == 'Conditions' and score >= 2.0:
                explanations.append(f"✓ Strong condition match")
            elif field == 'Sex' and score >= 1.5:
                explanations.append(f"✓ Gender criteria match")
            elif field == 'Age' and score >= 1.5:
                explanations.append(f"✓ Age criteria match")
            elif field == 'Phases' and score >= 1.0:
                explanations.append(f"✓ Trial phase match")
            elif score >= 1.0:
                explanations.append(f"✓ {field} match")
    
    if not explanations:
        return "Partial match based on general criteria"
    
    return " | ".join(explanations) 