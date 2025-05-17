import requests

# URL for ClinicalTrials.gov API direct CSV download link for 100 studies with relevant fields
CSV_URL = "https://clinicaltrials.gov/api/v2/studies?format=csv&fields=NCTId,Condition,BriefTitle,EligibilityCriteria,Gender,MinimumAge,MaximumAge,Phase,StudyType,LocationCountry&limit=100"


OUTPUT_FILE = "clinical_trials.csv"

def download_trials():
    print("Downloading clinical trials sample CSV...")
    response = requests.get(CSV_URL)
    if response.status_code != 200:
        print(f"Failed to download CSV. Status code: {response.status_code}")
        return
    with open(OUTPUT_FILE, "wb") as f:
        f.write(response.content)
    print(f"Downloaded and saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    download_trials() 