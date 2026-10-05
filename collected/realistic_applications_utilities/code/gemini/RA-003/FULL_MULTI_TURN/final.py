import pandas as pd
import numpy as np

# 1. Sample Dataset (Includes empty/missing data, 0s, 100s, duplicates, and edge boundaries)
data = {
    'Student_ID': [101, 102, 103, 104, 105, 106, 107, 108],
    'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva', 'Frank', 'Grace', 'Hannah'],
    'Math': [100, 0, None, np.nan, 78.5, -5, 105, 78.5],       # Boundary values (0, 100), tied scores, negative, >100, NaN
    'Science': [100, 0, np.nan, None, np.nan, 80, 95, 78.5],    # All NaNs across subjects for David (104)
    'English': [100, 0, np.nan, None, 85, 80, 89, 78.5],
    'Attendance_%': [100, 0, 75, 0, np.nan, -10, 110, 88]        # Exact threshold boundary (75%), NaN, invalid bounds
}

df = pd.DataFrame(data)

# 2. Robust Data Validation & Cleaning Function
def validate_and_analyze_students(data_frame):
    # Boundary Check: Completely Empty DataFrame
    if data_frame is None or data_frame.empty:
        print("⚠ WARNING: Provided DataFrame is empty. Returning empty results.")
        return pd.DataFrame(), ["Dataset is completely empty."]

    df_clean = data_frame.copy()
    validation_log = []
    subject_cols = ['Math', 'Science', 'English']

    # Ensure required columns exist
    missing_cols = [c for c in ['Student_ID', 'Name', 'Attendance_%'] + subject_cols if c not in df_clean.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    # Handle Missing Values safely per column
    for col in subject_cols:
        null_count = df_clean[col].isnull().sum()
        if null_count > 0:
            valid_scores = df_clean[col].dropna()
            # Boundary Check: If all values in a column are NaN, default to 0
            median_val = valid_scores.median() if not valid_scores.empty else 0.0
            df_clean[col] = df_clean[col].fillna(median_val)
            validation_log.append(f"Filled {null_count} missing value(s) in {col} with fallback value ({median_val:.1f}).")

        # Clip scores to exact valid bounds [0, 100]
        invalid_mask = (df_clean[col] < 0) | (df_clean[col] > 100)
        if invalid_mask.any():
            invalid_ids = df_clean[invalid_mask]['Student_ID'].tolist()
            validation_log.append(f"Clipped out-of-bound scores in {col} to [0, 100] for Student IDs: {invalid_ids}")
            df_clean[col] = df_clean[col].clip(lower=0.0, upper=100.0)

    # Clean Attendance: Default NaN to 0%, clip bounds [0, 100]
    att_nulls = df_clean['Attendance_%'].isnull().sum()
    if att_nulls > 0:
        df_clean['Attendance_%'] = df_clean['Attendance_%'].fillna(0.0)
        validation_log.append(f"Filled {att_nulls} missing Attendance value(s) with 0.0%.")

    att_invalid = (df_clean['Attendance_%'] < 0) | (df_clean['Attendance_%'] > 100)
    if att_invalid.any():
        invalid_ids = df_clean[att_invalid]['Student_ID'].tolist()
        validation_log.append(f"Clipped out-of-bound Attendance to [0, 100] for Student IDs: {invalid_ids}")
        df_clean['Attendance_%'] = df_clean['Attendance_%'].clip(lower=0.0, upper=100.0)

    # 3. Performance Metrics
    df_clean['Total_Score'] = df_clean[subject_cols].sum(axis=1)
    df_clean['Average_Score'] = df_clean[subject_cols].mean(axis=1).round(2)

    # Precise Grade Allocation addressing exact boundaries
    def calculate_grade(avg):
        if avg >= 90: return 'A+'
        elif avg >= 80: return 'A'
        elif avg >= 70: return 'B'
        elif avg >= 60: return 'C'
        else: return 'F'

    df_clean['Grade'] = df_clean['Average_Score'].apply(calculate_grade)
    
    # At-Risk Threshold: Strict inequality (<60 score or <75% attendance)
    df_clean['At_Risk'] = (df_clean['Average_Score'] < 60) | (df_clean['Attendance_%'] < 75)

    # 4. Safe Ranking (Handles ties and single-element or zero variance data)
    # Dense rank guarantees contiguous rank numbers on ties
    df_clean['Overall_Rank'] = df_clean['Total_Score'].rank(ascending=False, method='min').astype(int)
    
    # Safe Percentile Calculation (Handles N=1 edge case to avoid division by zero)
    n_students = len(df_clean)
    if n_students > 1:
        df_clean['Percentile'] = ((df_clean['Total_Score'].rank(method='min') - 1) / (n_students - 1) * 100).round(1)
    else:
        df_clean['Percentile'] = 100.0

    for col in subject_cols:
        df_clean[f'{col}_Rank'] = df_clean[col].rank(ascending=False, method='min').astype(int)

    return df_clean.sort_values(['Overall_Rank', 'Student_ID']), validation_log

# Run Analysis
df_processed, logs = validate_and_analyze_students(df)

# Output Summary & Table
print("--- VALIDATION & BOUNDARY LOGS ---")
for log in logs:
    print(f"✔ {log}")

print("\n--- BOUNDARY-HANDLED STUDENT REPORT ---")
cols_to_show = ['Overall_Rank', 'Name', 'Total_Score', 'Average_Score', 'Percentile', 'Attendance_%', 'Grade', 'At_Risk']
print(df_processed[cols_to_show].to_string(index=False))