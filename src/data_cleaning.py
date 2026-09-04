import os
import sys
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def clean_units_data(df):
    """Clean unit roster data."""
    df_clean = df.copy()
    df_clean.drop_duplicates(inplace=True)

    # Normalize category names
    category_map = {
        "icu": "ICU",
        "ICU": "ICU",
        "MedSurg": "Med-Surg",
        "med-surg": "Med-Surg",
        "Emergency": "Emergency",
        "Pediatrics": "Pediatrics",
        "Oncology": "Oncology"
    }
    df_clean["Unit_Type"] = df_clean["Unit_Type"].map(lambda x: category_map.get(str(x).strip(), str(x).strip()))
    return df_clean

def clean_nurses_data(df):
    """Clean nurse roster data."""
    df_clean = df.copy()
    df_clean.drop_duplicates(inplace=True)

    # Clean string format in Available_Hours e.g. "12.0 hrs" -> 12.0
    if df_clean["Available_Hours"].dtype == object:
        df_clean["Available_Hours"] = (
            df_clean["Available_Hours"]
            .astype(str)
            .str.replace("hrs", "", case=False)
            .str.strip()
        )
    df_clean["Available_Hours"] = pd.to_numeric(df_clean["Available_Hours"], errors="coerce").astype(float)


    # Impute missing Available_Hours with median
    df_clean["Available_Hours"] = df_clean["Available_Hours"].fillna(12.0)

    # Normalize Shifts
    shift_map = {
        "Day": "Day",
        "night_shift": "Night",
        "Night": "Night",
        "EVENING": "Evening",
        "Evening": "Evening"
    }
    df_clean["Shift"] = df_clean["Shift"].map(lambda x: shift_map.get(str(x).strip(), "Day"))

    # Impute missing Specialty
    df_clean["Specialty"] = df_clean["Specialty"].fillna("General")
    
    # Standardize Specialty categories
    spec_map = {
        "icu": "ICU",
        "MedSurg": "Med-Surg",
        "EMERGENCY": "Emergency"
    }
    df_clean["Specialty"] = df_clean["Specialty"].replace(spec_map)

    return df_clean

def clean_patients_data(df):
    """Clean patient records dataset."""
    df_clean = df.copy()
    initial_count = len(df_clean)

    # 1. Deduplication
    df_clean.drop_duplicates(subset=["Patient_ID"], keep="first", inplace=True)
    dedup_count = initial_count - len(df_clean)

    # 2. Age Cleaning (Fix negative values)
    median_age = df_clean[df_clean["Age"] > 0]["Age"].median()
    df_clean.loc[df_clean["Age"] <= 0, "Age"] = int(median_age)

    # 3. Acuity Level Normalization & Imputation
    acuity_valid = ["Low", "Medium", "High", "Critical"]
    df_clean["Acuity_Level"] = df_clean["Acuity_Level"].replace({"Ultra-Critical": "Critical"})
    df_clean.loc[~df_clean["Acuity_Level"].isin(acuity_valid), "Acuity_Level"] = np.nan
    df_clean["Acuity_Level"] = df_clean["Acuity_Level"].fillna("Medium")

    # 4. Standardize Required Skill
    skill_map = {
        "icu": "ICU",
        "MedSurg": "Med-Surg",
        "EMERGENCY": "Emergency"
    }
    df_clean["Required_Skill"] = df_clean["Required_Skill"].replace(skill_map)

    # 5. Outliers and Missing Required Nursing Hours
    df_clean["Required_Nursing_Hours"] = pd.to_numeric(df_clean["Required_Nursing_Hours"], errors="coerce")
    
    # Median hours by acuity for imputation
    acuity_hours_median = df_clean.groupby("Acuity_Level")["Required_Nursing_Hours"].median().to_dict()
    default_median = 4.5

    def impute_or_cap_hours(row):
        hrs = row["Required_Nursing_Hours"]
        acuity = row["Acuity_Level"]
        med = acuity_hours_median.get(acuity, default_median)
        if pd.isna(med) or med > 14.0:
            med = 8.0 if acuity in ["High", "Critical"] else 4.0

        if pd.isna(hrs) or hrs <= 0:
            return med
        if hrs > 16.0:  # Outlier capping
            return min(14.0, med)
        return hrs


    df_clean["Required_Nursing_Hours"] = df_clean.apply(impute_or_cap_hours, axis=1)

    print(f"Cleaned Patients Dataset: removed {dedup_count} duplicates, final records: {len(df_clean)}.")
    return df_clean

def run_cleaning_pipeline(raw_dir="data/raw", clean_dir="data/clean"):
    """Execute complete cleaning pipeline and save processed files."""
    os.makedirs(clean_dir, exist_ok=True)

    units_raw_path = os.path.join(raw_dir, "units_raw.csv")
    nurses_raw_path = os.path.join(raw_dir, "nurses_raw.csv")
    patients_raw_path = os.path.join(raw_dir, "patients_raw.csv")

    if not (os.path.exists(units_raw_path) and os.path.exists(nurses_raw_path) and os.path.exists(patients_raw_path)):
        from src.data_generator import generate_synthetic_data
        generate_synthetic_data(output_dir=raw_dir)


    df_units = pd.read_csv(units_raw_path)
    df_nurses = pd.read_csv(nurses_raw_path)
    df_patients = pd.read_csv(patients_raw_path)

    df_units_clean = clean_units_data(df_units)
    df_nurses_clean = clean_nurses_data(df_nurses)
    df_patients_clean = clean_patients_data(df_patients)

    df_units_clean.to_csv(os.path.join(clean_dir, "units.csv"), index=False)
    df_nurses_clean.to_csv(os.path.join(clean_dir, "nurses.csv"), index=False)
    df_patients_clean.to_csv(os.path.join(clean_dir, "patients.csv"), index=False)

    print("Data cleaning pipeline completed successfully. Clean datasets saved to data/clean.")
    return df_units_clean, df_nurses_clean, df_patients_clean

if __name__ == "__main__":
    run_cleaning_pipeline()
