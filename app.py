import streamlit as st
import pandas as pd
from models.nlp_model import extract_entities
from utils.matcher import match_patient_to_trials

# Load cancer studies data (sample CSV)
@st.cache_data
def load_trials():
    return pd.read_csv('datasets\cancer_studies.csv')

trials_df = load_trials()

st.title('GenAI Clinical Trial Screener')

st.write('Enter patient data (age, condition, etc.):')
patient_text = st.text_area('Patient Data', height=150)

if st.button('Find Matching Trials'):
    with st.spinner('Extracting entities and matching...'):
        entities = extract_entities(patient_text)
        matches = match_patient_to_trials(entities, trials_df)
        st.success(f'Found {len(matches)} matching trials!')
        # Show only the most relevant columns
        display_cols = [
            'NCT Number', 'Study Title', 'Study URL', 'Study Status',
            'Conditions', 'Sex', 'Age', 'Phases', 'Study Type', 'Locations'
        ]
        st.dataframe(matches[display_cols])
else:
    st.info('Enter patient data and click the button to find matches.') 