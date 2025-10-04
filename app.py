import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import os
import sys

# Add data_sources and utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'data_sources'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from models.nlp_model import extractor
from utils.matcher import match_patient_to_trials, get_match_explanation
from utils.eligibility_parser import EligibilityParser
from utils.geographic_matcher import GeographicMatcher
from data_sources.clinical_trials_api import ClinicalTrialsAPI, load_fresh_trial_data, get_trial_statistics

# Page configuration
st.set_page_config(
    page_title="TrialMatchAI - Clinical Trial Screener",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    .trial-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e1e5e9;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: bold;
    }
    .confidence-high {
        background-color: #d4edda;
        color: #155724;
    }
    .confidence-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    .confidence-low {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Load cancer studies data with enhanced capabilities
@st.cache_data
def load_trials(force_update: bool = False):
    """
    Load trial data with option to fetch fresh data from ClinicalTrials.gov API
    """
    try:
        if force_update:
            st.info("Fetching fresh data from ClinicalTrials.gov...")
            df = load_fresh_trial_data(force_update=True)
        else:
            df = pd.read_csv('datasets/cancer_studies.csv')
        
        if not df.empty:
            st.success(f"Loaded {len(df)} clinical trials from dataset")
            
            # Show statistics
            stats = get_trial_statistics(df)
            if stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Recruiting", stats.get('recruiting_trials', 0))
                with col2:
                    st.metric("Phase 2/3", stats.get('phase_2_trials', 0) + stats.get('phase_3_trials', 0))
                with col3:
                    st.metric("Interventional", stats.get('interventional_trials', 0))
        
        return df
    except Exception as e:
        st.error(f" Error loading dataset: {e}")
        return pd.DataFrame()

# Sample patient data for demos
SAMPLE_PATIENTS = {
    "Breast Cancer Patient": "female, 45 years old, breast cancer, HER2 positive, no prior chemotherapy, non-smoker",
    "Prostate Cancer Patient": "male, 68, prostate cancer, stage II, hypertension, prior surgery",
    "Pediatric Leukemia": "male, 10, acute lymphoblastic leukemia, no CNS involvement, first relapse",
    "Lung Cancer Patient": "female, 62, lung cancer, smoker, stage III, prior radiation therapy",
    "Advanced Melanoma": "male, 55, metastatic melanoma, BRAF positive, immunotherapy naive"
}

def get_confidence_badge_class(confidence):
    """Get CSS class for confidence badge based on percentage."""
    if confidence >= 70:
        return "confidence-high"
    elif confidence >= 40:
        return "confidence-medium"
    else:
        return "confidence-low"

def create_confidence_chart(matches_df):
    """Create a confidence score distribution chart."""
    if len(matches_df) == 0:
        return None
    
    fig = px.histogram(
        matches_df, 
        x='confidence_percentage',
        nbins=10,
        title="Confidence Score Distribution",
        labels={'confidence_percentage': 'Confidence Score (%)', 'count': 'Number of Trials'}
    )
    fig.update_layout(
        xaxis_title="Confidence Score (%)",
        yaxis_title="Number of Trials",
        showlegend=False
    )
    return fig

def create_conditions_chart(matches_df):
    """Create a chart showing condition distribution in matches."""
    if len(matches_df) == 0:
        return None
    
    # Extract and count conditions
    all_conditions = []
    for conditions in matches_df['Conditions'].dropna():
        if isinstance(conditions, str):
            all_conditions.extend([c.strip() for c in conditions.split(',')])
    
    if not all_conditions:
        return None
    
    condition_counts = pd.Series(all_conditions).value_counts().head(10)
    
    fig = px.bar(
        x=condition_counts.values,
        y=condition_counts.index,
        orientation='h',
        title="Top Conditions in Matching Trials",
        labels={'x': 'Number of Trials', 'y': 'Condition'}
    )
    fig.update_layout(height=400)
    return fig

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">TrialMatchAI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Clinical Trial Matching System for Cancer Patients</p>', unsafe_allow_html=True)
    
    # Load data
trials_df = load_trials()

    if trials_df.empty:
        st.error("Unable to load clinical trials data. Please check the dataset file.")
        return
    
    # Sidebar
    with st.sidebar:
        st.header(" Quick Start")
        
        # Data refresh option
        st.markdown("###  Data Management")
        if st.button(" Refresh Trial Data", help="Fetch fresh data from ClinicalTrials.gov"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("###  Sample Patient Cases")
        selected_sample = st.selectbox(
            "Choose a sample case:",
            ["Custom Input"] + list(SAMPLE_PATIENTS.keys())
        )
        
        if selected_sample != "Custom Input":
            sample_text = SAMPLE_PATIENTS[selected_sample]
            st.text_area("Sample Patient Data:", value=sample_text, height=100, disabled=True)
        
        st.markdown("---")
        st.markdown("###  Dataset Info")
        st.metric("Total Trials", len(trials_df))
        st.metric("Active Studies", len(trials_df[trials_df['Study Status'] == 'RECRUITING']))
        st.metric("Completed Studies", len(trials_df[trials_df['Study Status'] == 'COMPLETED']))
        
        # Geographic filtering
        st.markdown("---")
        st.markdown("###  Geographic Filtering")
        patient_location = st.text_input(
            "Patient Location:", 
            placeholder="e.g., New York, NY or Los Angeles, CA",
            help="Enter patient's location for distance-based filtering"
        )
        
        max_distance = st.selectbox(
            "Maximum Distance:",
            ["25 miles (Local)", "100 miles (Regional)", "500 miles (National)", "No limit"],
            index=1
        )
        
        # Parse distance
        distance_miles = {
            "25 miles (Local)": 25,
            "100 miles (Regional)": 100, 
            "500 miles (National)": 500,
            "No limit": float('inf')
        }[max_distance]
        
        st.markdown("---")
        st.markdown("###  How It Works")
        st.markdown("""
        1. **Enter patient data** (age, condition, etc.)
        2. **AI extracts entities** using medical NLP
        3. **Smart matching** finds relevant trials
        4. **Geographic filtering** by distance
        5. **Confidence scoring** ranks results
        """)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(" Patient Information")
        
        # Patient input
        if selected_sample != "Custom Input":
            patient_text = st.text_area(
                "Patient Data:", 
                value=SAMPLE_PATIENTS[selected_sample],
                height=150,
                help="Enter patient demographics, medical conditions, and relevant information"
            )
        else:
            patient_text = st.text_area(
                "Patient Data:", 
                height=150,
                placeholder="e.g., female, 45 years old, breast cancer, HER2 positive, no prior chemotherapy, non-smoker",
                help="Enter patient demographics, medical conditions, and relevant information"
            )
        
        # Action buttons
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            find_matches = st.button(" Find Matching Trials", type="primary", use_container_width=True)
        
        with col_btn2:
            analyze_entities = st.button(" Analyze Entities", use_container_width=True)
        
        with col_btn3:
            clear_input = st.button(" Clear", use_container_width=True)
            if clear_input:
                st.rerun()
    
    with col2:
        st.header(" Tips")
        st.markdown("""
        **Include these details:**
        - Age and gender
        - Cancer type and stage
        - Biomarker status (HER2, EGFR, etc.)
        - Treatment history
        - Smoking status
        - Geographic preferences
        """)
        
        st.markdown("**Example:**")
        st.code("""
female, 45 years old, 
breast cancer, HER2 positive, 
no prior chemotherapy, non-smoker
        """)
    
    # Process input
    if find_matches and patient_text.strip():
        with st.spinner(' Analyzing patient data and finding matching trials...'):
            try:
                # Extract entities
                entities_dict = extractor.extract_entities(patient_text)
                
                if not entities_dict.get("all_entities"):
                    st.warning(" No medical entities detected. Please provide more detailed patient information.")
                    return
                
                # Find matches
                matches = match_patient_to_trials(entities_dict, trials_df)
                
                if len(matches) == 0:
                    st.warning(" No matching trials found. Try providing more detailed information.")
                    return
                
                # Apply geographic filtering if location is provided
                if patient_location and patient_location.strip() and distance_miles != float('inf'):
                    st.info(f" Filtering trials within {distance_miles} miles of {patient_location}")
                    
                    geo_matcher = GeographicMatcher()
                    matches = geo_matcher.filter_trials_by_location(
                        matches, 
                        patient_location, 
                        distance_miles
                    )
                    
                    if len(matches) == 0:
                        st.warning(f" No trials found within {distance_miles} miles. Try expanding the search radius.")
                        return
                
                # Display results
                st.success(f" Found {len(matches)} matching clinical trials!")
                
                # Metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Total Matches", len(matches))
                with col2:
                    avg_confidence = matches['confidence_percentage'].mean()
                    st.metric("Avg Confidence", f"{avg_confidence:.1f}%")
                with col3:
                    high_conf = len(matches[matches['confidence_percentage'] >= 70])
                    st.metric("High Confidence", high_conf)
                with col4:
                    recruiting = len(matches[matches['Study Status'] == 'RECRUITING'])
                    st.metric("Currently Recruiting", recruiting)
                with col5:
                    if 'distance_miles' in matches.columns:
                        avg_distance = matches['distance_miles'].mean()
                        st.metric("Avg Distance", f"{avg_distance:.0f} mi")
                    else:
                        st.metric("Geographic Filter", "Off")
                
                # Charts
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    conf_chart = create_confidence_chart(matches)
                    if conf_chart:
                        st.plotly_chart(conf_chart, use_container_width=True)
                
                with chart_col2:
                    cond_chart = create_conditions_chart(matches)
                    if cond_chart:
                        st.plotly_chart(cond_chart, use_container_width=True)
                
                # Trial results
                st.header(" Matching Clinical Trials")
                
                for idx, (_, trial) in enumerate(matches.iterrows()):
                    confidence = trial['confidence_percentage']
                    badge_class = get_confidence_badge_class(confidence)
                    explanation = get_match_explanation(trial)
                    
                    with st.expander(f"Trial {idx+1}: {trial['Study Title'][:80]}{'...' if len(trial['Study Title']) > 80 else ''}", expanded=idx<3):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**NCT Number:** {trial['NCT Number']}")
                            st.markdown(f"**Study Title:** {trial['Study Title']}")
                            st.markdown(f"**Status:** {trial['Study Status']}")
                            st.markdown(f"**Conditions:** {trial['Conditions']}")
                            st.markdown(f"**Age:** {trial['Age']}")
                            st.markdown(f"**Sex:** {trial['Sex']}")
                            st.markdown(f"**Phases:** {trial['Phases']}")
                            
                            # Show geographic information if available
                            if 'distance_miles' in trial and pd.notna(trial['distance_miles']):
                                st.markdown(f"**Distance:** {trial['distance_miles']:.1f} miles")
                                st.markdown(f"**Nearest Site:** {trial.get('closest_facility', 'Unknown')}")
                                st.markdown(f"**Travel Category:** {trial.get('travel_category', 'Unknown').title()}")
                            
                            st.markdown(f"**Match Reason:** {explanation}")
                        
                        with col2:
                            st.markdown(f'<span class="confidence-badge {badge_class}">{confidence}% Match</span>', unsafe_allow_html=True)
                            
                            # Show distance badge if available
                            if 'distance_miles' in trial and pd.notna(trial['distance_miles']):
                                distance = trial['distance_miles']
                                if distance <= 25:
                                    distance_color = "green"
                                elif distance <= 100:
                                    distance_color = "orange"
                                else:
                                    distance_color = "red"
                                
                                st.markdown(f'<span style="background-color: {distance_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.875rem;">{distance:.0f} mi</span>', unsafe_allow_html=True)
                            
                            if pd.notna(trial['Study URL']):
                                st.link_button("View Study", trial['Study URL'])
                
                # Download results
                csv = matches.to_csv(index=False)
                st.download_button(
                    label=" Download Results as CSV",
                    data=csv,
                    file_name=f"trial_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f" Error processing request: {e}")
                st.exception(e)
    
    elif analyze_entities and patient_text.strip():
        with st.spinner(' Analyzing medical entities...'):
            try:
                entities_dict = extractor.extract_entities(patient_text)
                
                st.header(" Extracted Medical Entities")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.subheader("🏥 Conditions")
                    if entities_dict.get("conditions"):
                        for condition in entities_dict["conditions"]:
                            st.markdown(f"• {condition}")
                    else:
                        st.markdown("*No conditions detected*")
                
                with col2:
                    st.subheader(" Demographics")
                    if entities_dict.get("demographics"):
                        for demo in entities_dict["demographics"]:
                            st.markdown(f"• {demo}")
                    else:
                        st.markdown("*No demographics detected*")
                
                with col3:
                    st.subheader("💊 Treatments")
                    if entities_dict.get("treatments"):
                        for treatment in entities_dict["treatments"]:
                            st.markdown(f"• {treatment}")
                    else:
                        st.markdown("*No treatments detected*")
                
                with col4:
                    st.subheader("🧬 Lab Values")
                    if entities_dict.get("lab_values"):
                        for lab in entities_dict["lab_values"]:
                            st.markdown(f"• {lab}")
else:
                        st.markdown("*No lab values detected*")
                
                # Show all entities
                if entities_dict.get("all_entities"):
                    st.subheader(" All Detected Entities")
                    st.write(", ".join(entities_dict["all_entities"]))
                
            except Exception as e:
                st.error(f" Error analyzing entities: {e}")
    
    elif find_matches and not patient_text.strip():
        st.warning(" Please enter patient information before searching for trials.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>TrialMatchAI - Clinical Trial Matching System</p>
        <p>Built with Streamlit, Transformers, and Medical NLP</p>
        <p><em>This tool is for research and educational purposes. Always consult healthcare professionals for medical decisions.</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 