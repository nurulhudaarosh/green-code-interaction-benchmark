import pandas as pd
import numpy as np

# 1. Sample Dataset (Includes edge cases/invalid data: missing values, negative scores, scores > 100, bad attendance)
data = {
    'Student_ID': [101, 102, 103, 104, 105, 106, 107, 108],
    'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva', 'Frank', 'Grace', 'Hannah'],
    'Math': [85, -10, 92, 45, 78, 105, 95, None],
    'Science': [90, 65, 88, 50, np.nan, 79, 91, 58],
    'English': [78, 72, 95, 60, 85, 80, 89, 70],
    'Attendance_%': [92, 80, 105, -5, 88, 91, 96, 75]
}

df = pd.DataFrame(data)

# 2. Data Validation & Cleaning Function
def validate_student_data(data_frame):
    df_clean = data_frame.copy()
    validation_log = []
    
    subject_cols = ['Math', 'Science', 'English']
    
    # Fill missing scores with median (or drop/flag if required)
    for col in subject_cols:
        null_count = df_clean[col].isnull().sum()
        if null_count > 0:
            median_val = df_clean[col].median()
            df_clean[col].fillna(median_val, inplace=True)
            validation_log.append(f"Filled {null_count} missing value(s) in {col} with median ({median_val:.1f}).")
        
        # Clip scores to valid range [0, 100]
        invalid_mask = (df_clean[col] < 0) | (df_clean[col] > 100)
        if invalid_mask.any():
            invalid_indices = df_clean[invalid_mask]['Student_ID'].tolist()
            validation_log.append(f"Out-of-bound scores in {col} clipped to [0, 100] for Student IDs: {invalid_indices}")
            df_clean[col] = df_clean[col].clip(lower=0, upper=100)
            
    # Clip attendance percentage to [0, 100]
    att_invalid = (df_clean['Attendance_%'] < 0) | (df_clean['Attendance_%'] > 100)
    if att_invalid.any():
        invalid_ids = df_clean[att_invalid]['Student_ID'].tolist()
        validation_log.append(f"Out-of-bound Attendance clipped to [0, 100] for Student IDs: {invalid_ids}")
        df_clean['Attendance_%'] = df_clean['Attendance_%'].clip(lower=0, upper=100)
        
    return df_clean, validation_log

# Execute Validation
df_clean, validation_report = validate_student_data(df)

# 3. Performance Analysis on Cleaned Data
subject_cols = ['Math', 'Science', 'English']
df_clean['Total_Score'] = df_clean[subject_cols].sum(axis=1)
df_clean['Average_Score'] = df_clean[subject_cols].mean(axis=1).round(2)

def calculate_grade(avg):
    if avg >= 90: return 'A+'
    elif avg >= 80: return 'A'
    elif avg >= 70: return 'B'
    elif avg >= 60: return 'C'
    else: return 'F'

df_clean['Grade'] = df_clean['Average_Score'].apply(calculate_grade)
df_clean['At_Risk'] = (df_clean['Average_Score'] < 60) | (df_clean['Attendance_%'] < 75)
df_clean['Rank'] = df_clean['Total_Score'].rank(ascending=False, method='min').astype(int)

# 4. Output Validation Logs & Final Data
print("--- VALIDATION REPORT ---")
for log in validation_report:
    print(f"✔ {log}")

print("\n--- VALIDATED STUDENT PERFORMANCE REPORT ---")
print(df_clean.sort_values('Rank').to_string(index=False))