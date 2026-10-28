"""
Data Cleaning and Preprocessing Pipeline Module
===============================================
Project: Shift Workload-Balancing Simulator for Hospital Patient Transfers
Author: Hospital Operations Research & AI Engineering Team
Version: 3.0.0 (Review 3 Final Release)

Description:
    Processes raw hospital datasets exhibiting intentional real-world data flaws:
    - Missing patient acuity and nursing care hours
    - Duplicate patient, nurse, and unit records
    - Invalid data types (e.g. "12.0 hrs" string in numeric hours)
    - Clinical category inconsistencies (e.g. 'icu' vs 'ICU', 'night_shift' vs 'Night')
    - Physiological outliers (e.g. Age = -5, Required Hours = 99.0)

Deterministic Cleaning Rules:
    1. Deduplication: Primary key deduplication (Patient_ID, Nurse_ID, Unit_ID).
    2. Missing Acuity Imputation: Imputes missing Acuity_Level with mode ('Medium').
    3. Acuity-Conditioned Hours Imputation: Imputes missing nursing hours with acuity group median.
    4. Outlier Capping: Capped at physiological maximum (14.0 - 16.0 hrs) conditioned on acuity.
    5. Categorical Standardization: Strict dictionary mapping to canonical taxonomy.
"""

import os
import sys
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def clean_units_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw unit roster data by standardizing categories and removing duplicates.

    Parameters:
    -----------
    df : pd.DataFrame
        Raw units DataFrame.

    Returns:
    --------
    pd.DataFrame
        Cleaned units DataFrame with canonical 'Unit_Type'.
    """
    if df.empty:
        return df.copy()

    df_clean = df.copy()
    df_clean.drop_duplicates(inplace=True)

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


def clean_nurses_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw nurse roster data by parsing string hours, imputing missing specialties,
    and standardizing shift categories.

    Parameters:
    -----------
    df : pd.DataFrame
        Raw nurse roster DataFrame.

    Returns:
    --------
    pd.DataFrame
        Cleaned nurse roster DataFrame.
    """
    if df.empty:
        return df.copy()

    df_clean = df.copy()
    df_clean.drop_duplicates(subset=["Nurse_ID"], keep="first", inplace=True)

    # 1. Clean string format in Available_Hours e.g. "12.0 hrs" -> 12.0
    if df_clean["Available_Hours"].dtype == object:
        df_clean["Available_Hours"] = (
            df_clean["Available_Hours"]
            .astype(str)
            .str.replace("hrs", "", case=False)
            .str.strip()
        )
    df_clean["Available_Hours"] = pd.to_numeric(df_clean["Available_Hours"], errors="coerce").astype(float)

    # 2. Impute missing Available_Hours with standard shift default
    df_clean["Available_Hours"] = df_clean["Available_Hours"].fillna(12.0)

    # 3. Standardize Shift Taxonomy
    shift_map = {
        "Day": "Day",
        "night_shift": "Night",
        "Night": "Night",
        "EVENING": "Evening",
        "Evening": "Evening"
    }
    df_clean["Shift"] = df_clean["Shift"].map(lambda x: shift_map.get(str(x).strip(), "Day"))

    # 4. Impute and Standardize Specialty Qualifications
    df_clean["Specialty"] = df_clean["Specialty"].fillna("General")
    spec_map = {
        "icu": "ICU",
        "MedSurg": "Med-Surg",
        "EMERGENCY": "Emergency"
    }
    df_clean["Specialty"] = df_clean["Specialty"].replace(spec_map)

    return df_clean


def clean_patients_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans patient census records by eliminating duplicates, fixing invalid ages,
    normalizing clinical acuity, and capping care hour outliers.

    Parameters:
    -----------
    df : pd.DataFrame
        Raw patient records DataFrame.

    Returns:
    --------
    pd.DataFrame
        Cleaned patient census DataFrame.
    """
    if df.empty:
        return df.copy()

    df_clean = df.copy()
    initial_count = len(df_clean)

    # 1. Deduplication on Primary Key
    df_clean.drop_duplicates(subset=["Patient_ID"], keep="first", inplace=True)
    dedup_count = initial_count - len(df_clean)

    # 2. Age Sanitization (Clamp non-positive ages to median adult age)
    valid_ages = df_clean[df_clean["Age"] > 0]["Age"]
    median_age = valid_ages.median() if not valid_ages.empty else 45
    df_clean.loc[df_clean["Age"] <= 0, "Age"] = int(median_age)

    # 3. Acuity Level Normalization & Imputation
    acuity_valid = ["Low", "Medium", "High", "Critical"]
    df_clean["Acuity_Level"] = df_clean["Acuity_Level"].replace({"Ultra-Critical": "Critical"})
    df_clean.loc[~df_clean["Acuity_Level"].isin(acuity_valid), "Acuity_Level"] = np.nan
    df_clean["Acuity_Level"] = df_clean["Acuity_Level"].fillna("Medium")

    # 4. Standardize Required Specialty Skill
    skill_map = {
        "icu": "ICU",
        "MedSurg": "Med-Surg",
        "EMERGENCY": "Emergency"
    }
    df_clean["Required_Skill"] = df_clean["Required_Skill"].replace(skill_map)

    # 5. Outlier Capping and Acuity-Conditioned Hours Imputation
    df_clean["Required_Nursing_Hours"] = pd.to_numeric(df_clean["Required_Nursing_Hours"], errors="coerce")
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
        if hrs > 16.0:  # Outlier capping for extreme values (e.g. 99.0 hrs)
            return min(14.0, med)
        return hrs

    df_clean["Required_Nursing_Hours"] = df_clean.apply(impute_or_cap_hours, axis=1)

    print(f"Cleaned Patients Dataset: removed {dedup_count} duplicates, final records: {len(df_clean)}.")
    return df_clean


def run_cleaning_pipeline(raw_dir: str = "data/raw", clean_dir: str = "data/clean"):
    """
    Executes the end-to-end data cleaning workflow and persists validated CSVs.

    Parameters:
    -----------
    raw_dir : str, default='data/raw'
        Directory containing raw synthetic CSV files.
    clean_dir : str, default='data/clean'
        Output directory for cleaned and validated CSV datasets.

    Returns:
    --------
    tuple of (pd.DataFrame, pd.DataFrame, pd.DataFrame)
        Cleaned units, nurses, and patients DataFrames.
    """
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
