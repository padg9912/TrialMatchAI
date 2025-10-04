# TrialMatchAI - Clinical Trial Matching System

A comprehensive healthcare application that matches cancer patients to relevant clinical trials using advanced natural language processing and intelligent scoring algorithms. Designed for healthcare professionals, researchers, and medical institutions.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37+-red.svg)](https://streamlit.io)
[![Transformers](https://img.shields.io/badge/Transformers-4.51+-yellow.svg)](https://huggingface.co/transformers)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Project Overview

TrialMatchAI combines advanced medical natural language processing with intelligent scoring algorithms to match cancer patients with relevant clinical trials. The application processes natural language patient descriptions, extracts medical entities using biomedical language models, and matches them against a comprehensive database of cancer clinical trials with confidence scoring.

### Key Features
- **Medical NLP:** Uses PubMedBERT and rule-based extraction for medical entity recognition
- **Intelligent Matching:** Weighted scoring system prioritizing conditions, demographics, and trial phases
- **Confidence Scoring:** Provides match confidence percentages and explanations
- **Analytics Dashboard:** Real-time charts and visualizations of matching results
- **Professional Interface:** Modern, responsive design for healthcare workflows

---

## Enhanced Features

### Medical Entity Extraction
- **Named Entity Recognition:** Automatically identifies medical conditions, demographics, treatments, and lab values
- **Categorized Entities:** Groups entities into logical categories for better matching
- **Fallback System:** Robust rule-based extraction when advanced models aren't available
- **Entity Visualization:** Interactive display of extracted medical entities

### Intelligent Trial Matching
- **Weighted Scoring:** Prioritizes critical fields (conditions, age, sex) over secondary criteria
- **Confidence Metrics:** Provides match confidence percentages (0-100%)
- **Match Explanations:** Human-readable explanations for why trials matched
- **Fuzzy Matching:** Handles variations in medical terminology

### Analytics Dashboard
- **Confidence Distribution:** Histogram showing match quality distribution
- **Condition Analysis:** Bar charts of most common conditions in matches
- **Real-time Metrics:** Live statistics on total matches, average confidence, and recruiting trials
- **Export Functionality:** Download results as CSV for further analysis

### User Experience
- **Sample Cases:** Pre-loaded patient scenarios for quick testing
- **Interactive Interface:** Modern, responsive design with custom styling
- **Error Handling:** Comprehensive error handling with informative messages
- **Help System:** Built-in guidance for optimal usage

---

## Technical Stack

- **Python 3.8+** - Core programming language
- **Streamlit** - Modern web application framework
- **Transformers** - Hugging Face library for medical NLP models
- **Plotly** - Interactive data visualization
- **Pandas** - Advanced data manipulation and analysis
- **scikit-learn** - Machine learning utilities
- **PubMedBERT** - Biomedical language model for medical entity extraction

---

## Quick Start

### Live Demo
*Streamlit Cloud Deployment Coming Soon*

### Local Installation
```bash
# Clone the repository
git clone https://github.com/padg9912/TrialMatchAI.git
cd TrialMatchAI

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The app will be available at `http://localhost:8501`

---

## Usage Guide

### Basic Usage
1. **Enter Patient Data:** Use the text area to describe patient demographics and medical conditions
2. **Choose Sample Cases:** Select from pre-loaded patient scenarios or enter custom data
3. **Analyze Entities:** Click "Analyze Entities" to see what medical terms were extracted
4. **Find Matches:** Click "Find Matching Trials" to get ranked results with confidence scores
5. **Review Results:** Explore matching trials with detailed explanations and confidence metrics

### Sample Patient Cases
The application includes pre-loaded sample cases:

- **Breast Cancer Patient:** `female, 45 years old, breast cancer, HER2 positive, no prior chemotherapy, non-smoker`
- **Prostate Cancer Patient:** `male, 68, prostate cancer, stage II, hypertension, prior surgery`
- **Pediatric Leukemia:** `male, 10, acute lymphoblastic leukemia, no CNS involvement, first relapse`
- **Lung Cancer Patient:** `female, 62, lung cancer, smoker, stage III, prior radiation therapy`
- **Advanced Melanoma:** `male, 55, metastatic melanoma, BRAF positive, immunotherapy naive`

### Tips for Best Results
- Include age, gender, and specific cancer type
- Mention cancer stage and biomarker status (HER2, EGFR, etc.)
- Include treatment history and smoking status
- Be specific about geographic preferences if relevant

---

## Features in Detail

### Medical Entity Extraction
- **Medical NER:** Automatically identifies medical conditions, demographics, treatments, and lab values
- **Categorization:** Groups entities into logical categories for better matching
- **Visualization:** Shows extracted entities in an organized, color-coded display

### Intelligent Matching
- **Weighted Scoring:** Conditions (3x), Demographics (2x), Trial Phases (1.5x), Other fields (1x or less)
- **Confidence Scoring:** Provides match percentages and explanations
- **Fuzzy Matching:** Handles medical terminology variations

### Analytics Dashboard
- **Confidence Distribution:** Visual histogram of match quality
- **Condition Analysis:** Bar chart of most common conditions in matches
- **Real-time Metrics:** Live statistics and KPIs
- **Export Options:** Download results as CSV for further analysis

---

## Architecture

```
TrialMatchAI/
├── app.py                 # Main Streamlit application
├── models/
│   └── nlp_model.py      # Medical entity extraction (PubMedBERT + rules)
├── utils/
│   └── matcher.py        # Intelligent trial matching algorithm
├── datasets/
│   └── cancer_studies.csv # Clinical trials database
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Key Components
- **MedicalEntityExtractor:** Handles NLP with fallback to rule-based extraction
- **TrialMatcher:** Implements weighted scoring and confidence calculation
- **Streamlit UI:** Modern, responsive interface with analytics
- **Data Pipeline:** Efficient CSV loading and caching

---

## Performance & Accuracy

### Matching Accuracy
- **High Confidence Matches:** >70% confidence indicates strong alignment
- **Medium Confidence:** 40-70% indicates good potential matches
- **Low Confidence:** <40% indicates partial or weak matches

### Performance Metrics
- **Entity Extraction:** ~2-3 seconds for complex medical descriptions
- **Trial Matching:** ~1-2 seconds for 1000+ trial database
- **UI Responsiveness:** Real-time updates and smooth interactions

---

## Future Roadmap

### Completed (v2.0)
- [x] Advanced medical NLP with PubMedBERT integration
- [x] Intelligent weighted scoring system
- [x] Confidence metrics and explanations
- [x] Interactive analytics and visualizations
- [x] Professional UI with sample cases
- [x] Comprehensive error handling

### In Development (v2.1)
- [ ] Streamlit Cloud deployment
- [ ] Real-time clinical trial data updates
- [ ] Advanced eligibility criteria parsing
- [ ] Integration with ClinicalTrials.gov API

### Planned (v3.0)
- [ ] EHR integration via FHIR API
- [ ] Multi-language support
- [ ] Mobile-optimized interface
- [ ] User accounts and saved searches
- [ ] Advanced reporting and analytics
- [ ] Integration with hospital systems

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a Pull Request

---

## License

MIT License

---

## Acknowledgments

- ClinicalTrials.gov for open clinical trial data
- Streamlit and Hugging Face for open-source tools
- Biomedical NLP research community for language models

---

*Built for healthcare professionals, researchers, and medical institutions. Contributions and feedback welcome.*