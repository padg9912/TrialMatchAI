# models/nlp_model.py
# Stub for entity extraction using PubMedBERT (to be replaced with real NER)

def extract_entities(text):
    """
    Extract entities from patient text. For MVP, just split by space (stub).
    Replace with real NER using transformers for production.
    """
    return list(set(text.lower().split()))

# TODO: Integrate PubMedBERT or similar for real medical entity extraction 