# GenAI Clinical Trial Screener

A modern, AI-powered tool to match patient data to relevant cancer clinical trials. Built for rapid prototyping, demo, and as a portfolio project for applications to pharma, medical companies, and hospitals.

---

## 🚀 Project Overview
This app allows users to enter patient data (age, sex, condition, etc.) and instantly find matching cancer clinical trials from a curated dataset. It uses basic NLP for entity extraction and a scoring system to prioritize the most relevant trials.

---

## ✨ Features
- **Patient Data Input:** Free-text box for age, sex, condition, and more
- **AI Entity Extraction:** Extracts keywords/entities from patient data
- **Smart Matching:** Prioritizes matches in key fields (Conditions, Sex, Age, Phases)
- **Relevant Results:** Displays only the most important columns for easy review
- **Fast & Interactive UI:** Built with Streamlit for rapid feedback
- **Easy to Extend:** Modular code for adding new models or data sources

---

## 🛠️ Tech Stack
- **Python 3.8+**
- **Streamlit** (UI)
- **Pandas** (data handling)
- **Hugging Face Transformers** (for future NER upgrades)
- **scikit-learn** (optional, for future ML improvements)

---

## ⚡ Setup Instructions
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Add the dataset**
   - Place your `cancer_studies.csv` file in the project root.
   - (Optional) Run `python clean_trials.py` if you want to clean/validate the CSV.
4. **Run the app**
   ```bash
   streamlit run app.py
   ```

---

## 🧑‍💻 Usage
- Enter patient data in the text box (e.g., `female, 45 years old, breast cancer, HER2 positive, non-smoker`).
- Click **Find Matching Trials**.
- View the top 20 most relevant clinical trials in the results table.

### Sample Patient Data
```
female, 45 years old, breast cancer, HER2 positive, no prior chemotherapy, non-smoker
male, 68, prostate cancer, stage II, hypertension, prior surgery
male, 10, acute lymphoblastic leukemia, no CNS involvement, first relapse
female, 62, lung cancer, smoker, stage III, prior radiation therapy
```

---

## 📸 Screenshots
*Add screenshots here after running the app locally!*

---

## 🤝 Contributing
1. Fork the repo and create your branch (`git checkout -b feature/your-feature`)
2. Commit your changes (`git commit -am 'Add new feature'`)
3. Push to the branch (`git push origin feature/your-feature`)
4. Create a Pull Request

---

## 🗺️ Future Updates / Roadmap
- [ ] **Advanced NLP:** Integrate PubMedBERT or BioClinicalBERT for real medical entity extraction
- [ ] **Fuzzy Matching:** Use fuzzy string matching for better trial-patient alignment
- [ ] **Eligibility Parsing:** Parse and match detailed eligibility criteria
- [ ] **EHR Integration:** Support FHIR API for real-world hospital/EHR data
- [ ] **User Accounts:** Allow users to save searches and results
- [ ] **Export/Share:** Export matched trials as PDF/CSV or share via email
- [ ] **Deployment:** Deploy on Streamlit Cloud, Hugging Face Spaces, or Heroku
- [ ] **Mobile UI:** Responsive design for mobile devices
- [ ] **Analytics Dashboard:** Track usage, popular searches, and trial engagement

---

## 📄 License
MIT (or your preferred license)

---

## 🙌 Acknowledgements
- ClinicalTrials.gov for open clinical trial data
- Streamlit and Hugging Face for open-source tools

---

*Built for learning, demo, and real-world impact. Contributions and feedback welcome!* 