import csv

RAW_FILE = "clinical_trials.csv"
CLEAN_FILE = "clinical_trials_clean.csv"

def clean_csv():
    print(f"Reading {RAW_FILE}...")
    with open(RAW_FILE, newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        rows = list(reader)
    if not rows:
        print("No data found.")
        return
    header = rows[0]
    num_cols = len(header)
    print(f"Header has {num_cols} columns.")
    cleaned = [header]
    bad_rows = 0
    for row in rows[1:]:
        if len(row) == num_cols and not any(cell.strip().startswith('<') for cell in row):
            cleaned.append(row)
        else:
            bad_rows += 1
    print(f"Kept {len(cleaned)-1} rows. Removed {bad_rows} malformed or HTML/script rows.")
    with open(CLEAN_FILE, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(cleaned)
    print(f"Cleaned CSV saved as {CLEAN_FILE}")

if __name__ == "__main__":
    clean_csv() 