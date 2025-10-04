# models/nlp_model.py
# Enhanced medical entity extraction using transformers

import re
from typing import List, Dict, Set
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

class MedicalEntityExtractor:
    def __init__(self):
        """Initialize the medical entity extractor with a medical NER model."""
        try:
            # Use a biomedical NER model (fallback to basic if not available)
            self.ner_pipeline = pipeline(
                "ner",
                model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
                aggregation_strategy="simple"
            )
            self.model_available = True
        except Exception as e:
            print(f"Could not load biomedical NER model: {e}")
            print("Falling back to enhanced rule-based extraction")
            self.model_available = False
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract medical entities from patient text.
        Returns a dictionary with categorized entities.
        """
        if not text.strip():
            return {"all_entities": [], "conditions": [], "demographics": [], "treatments": []}
        
        # Clean and normalize text
        text = text.lower().strip()
        
        if self.model_available:
            return self._extract_with_ner(text)
        else:
            return self._extract_with_rules(text)
    
    def _extract_with_ner(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using the biomedical NER model."""
        try:
            entities = self.ner_pipeline(text)
            
            # Categorize entities
            result = {
                "all_entities": [],
                "conditions": [],
                "demographics": [],
                "treatments": [],
                "lab_values": []
            }
            
            for entity in entities:
                entity_text = entity['word'].lower()
                entity_type = entity['entity_group']
                
                result["all_entities"].append(entity_text)
                
                if entity_type in ['DISEASE', 'SYMPTOM']:
                    result["conditions"].append(entity_text)
                elif entity_type in ['AGE', 'SEX', 'GENDER']:
                    result["demographics"].append(entity_text)
                elif entity_type in ['DRUG', 'TREATMENT']:
                    result["treatments"].append(entity_text)
                elif entity_type in ['LAB_VALUE', 'BIOMARKER']:
                    result["lab_values"].append(entity_text)
            
            return result
            
        except Exception as e:
            print(f"NER extraction failed: {e}")
            return self._extract_with_rules(text)
    
    def _extract_with_rules(self, text: str) -> Dict[str, List[str]]:
        """Enhanced rule-based entity extraction."""
        result = {
            "all_entities": [],
            "conditions": [],
            "demographics": [],
            "treatments": [],
            "lab_values": []
        }
        
        # Medical conditions patterns
        condition_patterns = [
            r'\b(breast|lung|prostate|colon|pancreatic|ovarian|brain|liver|kidney|bladder|cervical|endometrial|thyroid|leukemia|lymphoma|melanoma|sarcoma|cancer|carcinoma|tumor|tumour|neoplasm)\b',
            r'\b(stage\s+[ivx0-9]+)\b',
            r'\b(her2|her-2|egfr|kras|braf|alk|ros1|pdl1|msi|tmb)\s*(positive|negative|high|low|mutated|wild|type)\b',
            r'\b(metastatic|metastasis|advanced|locally\s+advanced|recurrent|relapse)\b'
        ]
        
        # Demographics patterns
        demo_patterns = [
            r'\b(male|female|m|f)\b',
            r'\b(\d+)\s*(years?\s*old|yo|y\.o\.)\b',
            r'\b(adult|older\s+adult|pediatric|child|infant)\b'
        ]
        
        # Treatment patterns
        treatment_patterns = [
            r'\b(chemotherapy|chemo|radiation|radiotherapy|surgery|surgical|immunotherapy|targeted\s+therapy|hormone\s+therapy)\b',
            r'\b(prior|previous|history\s+of|no\s+prior)\s+(chemotherapy|chemo|radiation|surgery)\b',
            r'\b(smoker|non-smoker|never\s+smoked|former\s+smoker)\b'
        ]
        
        # Extract all patterns
        all_matches = set()
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                all_matches.add(match.lower())
                result["conditions"].append(match.lower())
        
        for pattern in demo_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                all_matches.add(match.lower())
                result["demographics"].append(match.lower())
        
        for pattern in treatment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                all_matches.add(match.lower())
                result["treatments"].append(match.lower())
        
        # Add individual words for additional matching
        words = set(text.lower().split())
        medical_words = {
            'cancer', 'tumor', 'tumour', 'malignant', 'metastatic', 'stage', 'grade',
            'biopsy', 'pathology', 'oncology', 'chemotherapy', 'radiation', 'surgery',
            'male', 'female', 'years', 'old', 'adult', 'pediatric', 'child'
        }
        
        for word in words:
            if word in medical_words:
                all_matches.add(word)
        
        result["all_entities"] = list(all_matches)
        
        # Remove duplicates from all lists
        for key in result:
            result[key] = list(set(result[key]))
        
        return result

# Global instance
extractor = MedicalEntityExtractor()

def extract_entities(text: str) -> List[str]:
    """
    Main function to extract entities from patient text.
    Returns a list of all extracted entities for backward compatibility.
    """
    entities_dict = extractor.extract_entities(text)
    return entities_dict["all_entities"] 