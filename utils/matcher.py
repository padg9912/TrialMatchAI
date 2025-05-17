import pandas as pd

def match_patient_to_trials(entities, trials_df):
    """
    Improved: Score each row by the number of patient entities found in key columns.
    Return top 20 rows sorted by score (descending).
    """
    key_cols = ['Conditions', 'Sex', 'Age', 'Phases']
    def score_row(row):
        score = 0
        for col in key_cols:
            cell = str(row.get(col, '')).lower()
            score += sum(entity in cell for entity in entities)
        return score
    trials_df = trials_df.copy()
    trials_df['__score'] = trials_df.apply(score_row, axis=1)
    matches = trials_df[trials_df['__score'] > 0]
    matches = matches.sort_values(by='__score', ascending=False).drop(columns=['__score'])
    return matches.head(20)

# TODO: Further improve with fuzzy/field-specific matching 