"""
Advanced Eligibility Criteria Parser
Parses and structures clinical trial eligibility criteria using NLP
"""

import re
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

class CriteriaType(Enum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"

@dataclass
class EligibilityCriterion:
    """Structured representation of an eligibility criterion"""
    text: str
    criterion_type: CriteriaType
    category: str  # e.g., "age", "condition", "medication", "laboratory"
    value: Optional[str] = None
    operator: Optional[str] = None  # e.g., ">", "<", "=", "between"
    confidence: float = 0.0

class EligibilityParser:
    """
    Advanced parser for clinical trial eligibility criteria
    """
    
    def __init__(self):
        # Define patterns for different types of criteria
        self.patterns = {
            'age': [
                r'age\s*[<>≤≥=]\s*(\d+)',
                r'age\s+(\d+)\s*[-–]\s*(\d+)',
                r'(\d+)\s*years?\s*old',
                r'between\s+(\d+)\s*and\s*(\d+)\s*years?',
                r'(\d+)\s*to\s*(\d+)\s*years?'
            ],
            'weight': [
                r'weight\s*[<>≤≥=]\s*(\d+(?:\.\d+)?)\s*(kg|lb|lbs|pounds?)',
                r'body\s*mass\s*index\s*[<>≤≥=]\s*(\d+(?:\.\d+)?)',
                r'bmi\s*[<>≤≥=]\s*(\d+(?:\.\d+)?)'
            ],
            'gender': [
                r'(male|female|men|women)',
                r'(m|f)\b'
            ],
            'condition': [
                r'(cancer|carcinoma|tumor|tumour|neoplasm|malignancy)',
                r'(breast|lung|prostate|colon|pancreatic|ovarian|brain|liver|kidney|bladder|cervical|endometrial|thyroid)\s+cancer',
                r'(leukemia|lymphoma|melanoma|sarcoma)'
            ],
            'stage': [
                r'stage\s*([ivx0-9]+)',
                r'grade\s*([ivx0-9]+)',
                r't[0-4]n[0-3]m[0-1]'  # TNM staging
            ],
            'biomarker': [
                r'(her2|her-2|egfr|kras|braf|alk|ros1|pdl1|msi|tmb|brca1|brca2)\s*(positive|negative|high|low|mutated|wild|type)',
                r'(estrogen|progesterone)\s*(positive|negative)',
                r'triple\s*negative'
            ],
            'medication': [
                r'(chemotherapy|chemo|radiation|radiotherapy|surgery|surgical|immunotherapy|targeted\s+therapy|hormone\s+therapy)',
                r'(prior|previous|history\s+of|no\s+prior)\s+(chemotherapy|chemo|radiation|surgery)',
                r'concurrent\s+(chemotherapy|radiation)'
            ],
            'laboratory': [
                r'(hemoglobin|hgb|hct|hematocrit|wbc|white\s+blood\s+cell|platelet|creatinine|alt|ast|bilirubin)\s*[<>≤≥=]\s*(\d+(?:\.\d+)?)',
                r'ecog\s*performance\s*status\s*[<>≤≥=]\s*([0-2])',
                r'karnofsky\s*performance\s*status\s*[<>≤≥=]\s*(\d+)'
            ],
            'lifestyle': [
                r'(smoker|non-smoker|never\s+smoked|former\s+smoker|current\s+smoker)',
                r'(pregnant|pregnancy|breastfeeding|lactating)',
                r'(contraception|contraceptive)'
            ],
            'comorbidity': [
                r'(diabetes|hypertension|heart\s+disease|kidney\s+disease|liver\s+disease|lung\s+disease)',
                r'(hiv|aids|hepatitis|tuberculosis)',
                r'(autoimmune|immune\s+deficiency)'
            ]
        }
        
        # Exclusion keywords
        self.exclusion_keywords = [
            'exclusion', 'exclude', 'not eligible', 'ineligible', 'contraindication',
            'contraindicated', 'not suitable', 'not appropriate', 'must not',
            'cannot', 'unable to', 'prohibited'
        ]
        
        # Inclusion keywords
        self.inclusion_keywords = [
            'inclusion', 'include', 'eligible', 'suitable', 'appropriate',
            'must have', 'must be', 'required', 'necessary', 'criteria'
        ]
    
    def parse_eligibility_text(self, text: str) -> Dict[str, List[EligibilityCriterion]]:
        """
        Parse eligibility criteria text and extract structured information
        
        Args:
            text: Raw eligibility criteria text
            
        Returns:
            Dictionary with 'inclusion' and 'exclusion' criteria lists
        """
        if not text or not text.strip():
            return {'inclusion': [], 'exclusion': []}
        
        # Clean and normalize text
        text = text.lower().strip()
        
        # Split into sentences/criteria
        criteria_sentences = self._split_into_criteria(text)
        
        inclusion_criteria = []
        exclusion_criteria = []
        
        for sentence in criteria_sentences:
            criterion = self._parse_single_criterion(sentence)
            
            if criterion:
                if criterion.criterion_type == CriteriaType.INCLUSION:
                    inclusion_criteria.append(criterion)
                else:
                    exclusion_criteria.append(criterion)
        
        return {
            'inclusion': inclusion_criteria,
            'exclusion': exclusion_criteria
        }
    
    def _split_into_criteria(self, text: str) -> List[str]:
        """Split text into individual criteria sentences"""
        # Split by common separators
        sentences = re.split(r'[.;]\s*', text)
        
        # Further split by bullet points and numbered lists
        criteria = []
        for sentence in sentences:
            # Split by bullet points
            bullet_split = re.split(r'[•\-\*]\s*', sentence)
            criteria.extend(bullet_split)
            
            # Split by numbered lists
            number_split = re.split(r'\d+[\.\)]\s*', sentence)
            criteria.extend(number_split)
        
        # Clean up and filter
        criteria = [c.strip() for c in criteria if c.strip()]
        return criteria
    
    def _parse_single_criterion(self, text: str) -> Optional[EligibilityCriterion]:
        """Parse a single criterion sentence"""
        if not text or len(text) < 5:  # Skip very short text
            return None
        
        # Determine if this is inclusion or exclusion
        criterion_type = self._determine_criterion_type(text)
        
        # Find the most relevant category and extract information
        best_match = None
        best_confidence = 0.0
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    confidence = self._calculate_match_confidence(text, pattern, match)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = {
                            'category': category,
                            'pattern': pattern,
                            'match': match,
                            'value': self._extract_value(match, category),
                            'operator': self._extract_operator(match)
                        }
        
        if best_match and best_confidence > 0.3:  # Minimum confidence threshold
            return EligibilityCriterion(
                text=text,
                criterion_type=criterion_type,
                category=best_match['category'],
                value=best_match['value'],
                operator=best_match['operator'],
                confidence=best_confidence
            )
        
        return None
    
    def _determine_criterion_type(self, text: str) -> CriteriaType:
        """Determine if a criterion is inclusion or exclusion"""
        text_lower = text.lower()
        
        # Check for exclusion keywords
        exclusion_score = sum(1 for keyword in self.exclusion_keywords if keyword in text_lower)
        
        # Check for inclusion keywords
        inclusion_score = sum(1 for keyword in self.inclusion_keywords if keyword in text_lower)
        
        # Check for negative language patterns
        negative_patterns = [
            r'\b(no|not|without|lacking|absence|free\s+of)\b',
            r'\b(cannot|unable|prohibited|contraindicated)\b'
        ]
        
        negative_score = sum(1 for pattern in negative_patterns if re.search(pattern, text_lower))
        
        # Determine type based on scores
        if exclusion_score > 0 or negative_score > inclusion_score:
            return CriteriaType.EXCLUSION
        else:
            return CriteriaType.INCLUSION
    
    def _calculate_match_confidence(self, text: str, pattern: str, match) -> float:
        """Calculate confidence score for a pattern match"""
        base_confidence = 0.5
        
        # Boost confidence for exact matches
        if match.group() == match.group(0):
            base_confidence += 0.2
        
        # Boost confidence for longer matches
        match_length = len(match.group(0))
        if match_length > 10:
            base_confidence += 0.1
        
        # Boost confidence for specific medical terms
        medical_terms = ['cancer', 'tumor', 'malignant', 'metastatic', 'biomarker']
        for term in medical_terms:
            if term in match.group(0).lower():
                base_confidence += 0.1
                break
        
        return min(base_confidence, 1.0)
    
    def _extract_value(self, match, category: str) -> Optional[str]:
        """Extract the value from a regex match"""
        groups = match.groups()
        if not groups:
            return match.group(0)
        
        # Handle age ranges
        if category == 'age' and len(groups) >= 2:
            return f"{groups[0]}-{groups[1]}"
        
        # Handle weight with units
        if category == 'weight' and len(groups) >= 2:
            return f"{groups[0]} {groups[1]}"
        
        # Return first group or full match
        return groups[0] if groups else match.group(0)
    
    def _extract_operator(self, match) -> Optional[str]:
        """Extract operator from a regex match"""
        match_text = match.group(0)
        
        if any(op in match_text for op in ['>', '≥', 'greater than', 'more than']):
            return '>'
        elif any(op in match_text for op in ['<', '≤', 'less than', 'fewer than']):
            return '<'
        elif any(op in match_text for op in ['=', 'equals', 'equal to']):
            return '='
        elif any(op in match_text for op in ['between', '-', 'to']):
            return 'between'
        
        return None
    
    def structure_eligibility_criteria(self, raw_criteria: str) -> Dict:
        """
        Structure raw eligibility criteria into organized format
        
        Args:
            raw_criteria: Raw eligibility criteria text
            
        Returns:
            Structured dictionary with categorized criteria
        """
        parsed = self.parse_eligibility_text(raw_criteria)
        
        structured = {
            'inclusion': {
                'age': [],
                'condition': [],
                'biomarker': [],
                'medication': [],
                'laboratory': [],
                'lifestyle': [],
                'other': []
            },
            'exclusion': {
                'age': [],
                'condition': [],
                'biomarker': [],
                'medication': [],
                'laboratory': [],
                'lifestyle': [],
                'other': []
            }
        }
        
        # Organize criteria by type and category
        for criterion in parsed['inclusion']:
            category = criterion.category if criterion.category in structured['inclusion'] else 'other'
            structured['inclusion'][category].append({
                'text': criterion.text,
                'value': criterion.value,
                'operator': criterion.operator,
                'confidence': criterion.confidence
            })
        
        for criterion in parsed['exclusion']:
            category = criterion.category if criterion.category in structured['exclusion'] else 'other'
            structured['exclusion'][category].append({
                'text': criterion.text,
                'value': criterion.value,
                'operator': criterion.operator,
                'confidence': criterion.confidence
            })
        
        return structured
    
    def match_patient_to_criteria(self, patient_data: Dict, structured_criteria: Dict) -> Dict:
        """
        Match patient data against structured eligibility criteria
        
        Args:
            patient_data: Patient information dictionary
            structured_criteria: Structured eligibility criteria
            
        Returns:
            Match results with scores and explanations
        """
        match_results = {
            'overall_score': 0.0,
            'inclusion_matches': [],
            'exclusion_matches': [],
            'inclusion_violations': [],
            'exclusion_violations': [],
            'explanation': []
        }
        
        inclusion_score = 0.0
        exclusion_score = 0.0
        
        # Check inclusion criteria
        for category, criteria_list in structured_criteria['inclusion'].items():
            for criterion in criteria_list:
                match_result = self._evaluate_criterion(patient_data, criterion, category)
                
                if match_result['matches']:
                    match_results['inclusion_matches'].append({
                        'category': category,
                        'criterion': criterion,
                        'score': match_result['score']
                    })
                    inclusion_score += match_result['score']
                else:
                    match_results['inclusion_violations'].append({
                        'category': category,
                        'criterion': criterion,
                        'reason': match_result['reason']
                    })
        
        # Check exclusion criteria
        for category, criteria_list in structured_criteria['exclusion'].items():
            for criterion in criteria_list:
                match_result = self._evaluate_criterion(patient_data, criterion, category)
                
                if match_result['matches']:
                    match_results['exclusion_matches'].append({
                        'category': category,
                        'criterion': criterion,
                        'score': match_result['score']
                    })
                    exclusion_score += match_result['score']  # This is bad - exclusion match
                else:
                    match_results['exclusion_violations'].append({
                        'category': category,
                        'criterion': criterion,
                        'reason': match_result['reason']
                    })
        
        # Calculate overall score (inclusion positive, exclusion negative)
        match_results['overall_score'] = inclusion_score - (exclusion_score * 2)  # Exclusions weighted more heavily
        
        # Generate explanation
        match_results['explanation'] = self._generate_match_explanation(match_results)
        
        return match_results
    
    def _evaluate_criterion(self, patient_data: Dict, criterion: Dict, category: str) -> Dict:
        """Evaluate a single criterion against patient data"""
        patient_value = patient_data.get(category, '').lower()
        criterion_value = criterion.get('value', '').lower()
        operator = criterion.get('operator', '')
        
        # Simple matching logic (can be enhanced with more sophisticated NLP)
        if category in ['age', 'weight', 'laboratory']:
            return self._evaluate_numeric_criterion(patient_value, criterion_value, operator)
        else:
            return self._evaluate_text_criterion(patient_value, criterion_value)
    
    def _evaluate_numeric_criterion(self, patient_value: str, criterion_value: str, operator: str) -> Dict:
        """Evaluate numeric criteria"""
        try:
            # Extract numbers from patient and criterion values
            patient_nums = re.findall(r'\d+(?:\.\d+)?', patient_value)
            criterion_nums = re.findall(r'\d+(?:\.\d+)?', criterion_value)
            
            if not patient_nums or not criterion_nums:
                return {'matches': False, 'score': 0.0, 'reason': 'No numeric values found'}
            
            patient_num = float(patient_nums[0])
            criterion_num = float(criterion_nums[0])
            
            if operator == '>':
                matches = patient_num > criterion_num
            elif operator == '<':
                matches = patient_num < criterion_num
            elif operator == '=':
                matches = abs(patient_num - criterion_num) < 0.1
            else:
                matches = patient_num == criterion_num
            
            return {
                'matches': matches,
                'score': 1.0 if matches else 0.0,
                'reason': f"Patient value {patient_num} {'meets' if matches else 'does not meet'} criterion {operator} {criterion_num}"
            }
            
        except (ValueError, IndexError):
            return {'matches': False, 'score': 0.0, 'reason': 'Error parsing numeric values'}
    
    def _evaluate_text_criterion(self, patient_value: str, criterion_value: str) -> Dict:
        """Evaluate text-based criteria"""
        if not patient_value or not criterion_value:
            return {'matches': False, 'score': 0.0, 'reason': 'Missing values'}
        
        # Simple keyword matching (can be enhanced with semantic similarity)
        patient_words = set(patient_value.split())
        criterion_words = set(criterion_value.split())
        
        overlap = len(patient_words.intersection(criterion_words))
        total_words = len(patient_words.union(criterion_words))
        
        if total_words == 0:
            return {'matches': False, 'score': 0.0, 'reason': 'No words to compare'}
        
        similarity = overlap / total_words
        matches = similarity > 0.3  # Threshold for text matching
        
        return {
            'matches': matches,
            'score': similarity,
            'reason': f"Text similarity: {similarity:.2f} ({'meets' if matches else 'does not meet'} threshold)"
        }
    
    def _generate_match_explanation(self, match_results: Dict) -> List[str]:
        """Generate human-readable explanation of match results"""
        explanations = []
        
        # Inclusion matches
        if match_results['inclusion_matches']:
            explanations.append(f" Meets {len(match_results['inclusion_matches'])} inclusion criteria")
        
        # Inclusion violations
        if match_results['inclusion_violations']:
            explanations.append(f" Does not meet {len(match_results['inclusion_violations'])} inclusion criteria")
        
        # Exclusion matches (bad)
        if match_results['exclusion_matches']:
            explanations.append(f" Meets {len(match_results['exclusion_matches'])} exclusion criteria")
        
        # Overall assessment
        score = match_results['overall_score']
        if score > 2.0:
            explanations.append("🎯 Strong match - likely eligible")
        elif score > 0.0:
            explanations.append("🤔 Partial match - may be eligible with review")
        elif score > -1.0:
            explanations.append(" Weak match - unlikely to be eligible")
        else:
            explanations.append(" Poor match - probably not eligible")
        
        return explanations

# Example usage and testing
if __name__ == "__main__":
    # Test the eligibility parser
    parser = EligibilityParser()
    
    # Sample eligibility criteria
    sample_criteria = """
    Inclusion Criteria:
    - Age ≥ 18 years
    - Histologically confirmed breast cancer
    - HER2 positive status
    - ECOG performance status ≤ 2
    - Adequate organ function (hemoglobin ≥ 10 g/dL)
    
    Exclusion Criteria:
    - Prior chemotherapy for metastatic disease
    - Pregnant or breastfeeding
    - Active infection
    - Known HIV infection
    """
    
    print("Testing Eligibility Parser...")
    
    # Parse criteria
    structured = parser.structure_eligibility_criteria(sample_criteria)
    
    print("\nStructured Criteria:")
    print(f"Inclusion criteria found: {sum(len(criteria) for criteria in structured['inclusion'].values())}")
    print(f"Exclusion criteria found: {sum(len(criteria) for criteria in structured['exclusion'].values())}")
    
    # Test patient matching
    sample_patient = {
        'age': '45 years old',
        'condition': 'breast cancer',
        'biomarker': 'her2 positive',
        'laboratory': 'hemoglobin 12 g/dl',
        'medication': 'no prior chemotherapy'
    }
    
    match_results = parser.match_patient_to_criteria(sample_patient, structured)
    
    print(f"\n🎯Match Results:")
    print(f"Overall Score: {match_results['overall_score']:.2f}")
    print(f"Explanations: {'; '.join(match_results['explanation'])}")
