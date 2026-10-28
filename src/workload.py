"""
Workload Calculation Module
===========================
Project: Shift Workload-Balancing Simulator for Hospital Patient Transfers
Author: Hospital Operations Research & AI Engineering Team
Version: 3.0.0 (Review 3 Final Release)

Description:
    This module computes patient acuity-weighted workload and unit-level workload metrics.
    It provides mathematically grounded, explainable indicators for shift managers to
    monitor nursing workload intensity across inpatient wards, emergency rooms, and ICUs.

Mathematical Formulation:
    1. Patient-Level Acuity Workload:
       W_patient = H_req * W_acuity
       where:
         - H_req: Required base nursing hours per shift (1.5 to 14.0 hours)
         - W_acuity: Dimensionless acuity weighting multiplier:
             * Low Acuity:      1.00
             * Medium Acuity:   1.25
             * High Acuity:     1.50
             * Critical Acuity: 2.00

    2. Unit-Level Aggregated Workload:
       W_unit = (sum_{p in Active_Patients} W_patient) / 15.0
       (Normalized for a standard 12-hour operational shift cycle across admitted census)

    3. Workload Imbalance Metrics:
       - Max-Min Gap: max(WPN) - min(WPN)
       - Standard Deviation: sqrt( (1 / (N - 1)) * sum (WPN_i - mean(WPN))^2 )
       - Coefficient of Variation (CV%): (Std(WPN) / Mean(WPN)) * 100
"""

import os
import sys
import pandas as pd
import numpy as np

# Ensure project root directory is accessible in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ==============================================================================
# GLOBAL CONSTANTS & CLINICAL ASSUMPTIONS
# ==============================================================================
# Prototype Acuity Weights (Note: Synthetic assumptions, not validated clinical standards)
DEFAULT_ACUITY_WEIGHTS = {
    "Low": 1.0,
    "Medium": 1.25,
    "High": 1.5,
    "Critical": 2.0
}

# Shift normalization divisor representing patient turnover / multi-bed shift horizon
SHIFT_NORMALIZATION_DIVISOR = 15.0


def calculate_patient_workload(df_patients: pd.DataFrame, acuity_weights: dict = None, active_only: bool = True) -> pd.DataFrame:
    """
    Computes individual patient workload weighted by clinical acuity.

    Parameters:
    -----------
    df_patients : pd.DataFrame
        DataFrame containing patient records. Required columns:
        - 'Patient_ID': Unique identifier (str)
        - 'Acuity_Level': Clinical acuity string ('Low', 'Medium', 'High', 'Critical')
        - 'Required_Nursing_Hours': Base care hours required per shift (float)
        - 'Transfer_Status': Current status ('Admitted', 'Pending Transfer', etc.)
    acuity_weights : dict, optional
        Dictionary mapping acuity level strings to float weights. Defaults to DEFAULT_ACUITY_WEIGHTS.
    active_only : bool, default=True
        If True, filters exclusively for active patients ('Admitted' or 'Pending Transfer').

    Returns:
    --------
    pd.DataFrame
        Copy of input DataFrame augmented with:
        - 'Acuity_Weight': Multiplier applied based on Acuity_Level
        - 'Patient_Workload': Float product (Required_Nursing_Hours * Acuity_Weight)

    Error Boundaries & Safeguards:
    ------------------------------
    - Missing or unmapped acuity levels default to 1.0.
    - Non-numeric or NaN required hours default to safe median (handled in preprocessing).
    - Empty input DataFrame returns an empty DataFrame with expected columns without raising exceptions.
    """
    if df_patients.empty:
        df_empty = df_patients.copy()
        df_empty["Acuity_Weight"] = pd.Series(dtype=float)
        df_empty["Patient_Workload"] = pd.Series(dtype=float)
        return df_empty

    if acuity_weights is None:
        acuity_weights = DEFAULT_ACUITY_WEIGHTS

    df = df_patients.copy()

    # Filter for active admitted census requiring nurse attention
    if active_only and "Transfer_Status" in df.columns:
        df = df[df["Transfer_Status"].isin(["Admitted", "Pending Transfer"])].copy()

    # Map acuity weights with safe fallback to 1.0 for unclassified categories
    df["Acuity_Weight"] = df["Acuity_Level"].map(lambda x: acuity_weights.get(x, 1.0)).astype(float)
    
    # Calculate patient-level workload product
    df["Patient_Workload"] = (df["Required_Nursing_Hours"] * df["Acuity_Weight"]).astype(float)
    
    return df


def calculate_unit_workload(df_patients: pd.DataFrame, acuity_weights: dict = None) -> pd.DataFrame:
    """
    Aggregates patient workload metrics per hospital unit.

    Parameters:
    -----------
    df_patients : pd.DataFrame
        DataFrame of patient records containing 'Facility_ID', 'Unit_ID',
        'Required_Nursing_Hours', 'Acuity_Level', etc.
    acuity_weights : dict, optional
        Acuity weight dictionary for calculation.

    Returns:
    --------
    pd.DataFrame
        Aggregated summary per (Facility_ID, Unit_ID) containing:
        - 'Facility_ID': Hospital facility identifier (str)
        - 'Unit_ID': Unit identifier (str)
        - 'Total_Patients': Active census count (int)
        - 'Cumulative_Workload': Raw sum of patient workload (float)
        - 'Total_Required_Hours': Normalized care hours required (float)
        - 'Avg_Patient_Workload': Mean workload per patient (float)
        - 'Total_Workload': Shift-normalized workload score (float)

    Error Boundaries & Safeguards:
    ------------------------------
    - If df_patients is empty, returns DataFrame with zeroed metrics.
    - Zero active patients yields Total_Workload = 0.0 and Avg_Patient_Workload = 0.0.
    """
    if df_patients.empty:
        return pd.DataFrame(columns=[
            "Facility_ID", "Unit_ID", "Total_Patients", "Cumulative_Workload",
            "Total_Required_Hours", "Avg_Patient_Workload", "Total_Workload"
        ])

    df_p = calculate_patient_workload(df_patients, acuity_weights, active_only=True)

    if df_p.empty:
        return pd.DataFrame(columns=[
            "Facility_ID", "Unit_ID", "Total_Patients", "Cumulative_Workload",
            "Total_Required_Hours", "Avg_Patient_Workload", "Total_Workload"
        ])

    unit_summary = df_p.groupby(["Facility_ID", "Unit_ID"]).agg(
        Total_Patients=("Patient_ID", "count"),
        Cumulative_Workload=("Patient_Workload", "sum"),
        Total_Required_Hours=("Required_Nursing_Hours", "sum"),
        Avg_Patient_Workload=("Patient_Workload", "mean")
    ).reset_index()

    # Shift Workload (Normalized across 12h operational shift cycle)
    unit_summary["Total_Workload"] = (unit_summary["Cumulative_Workload"] / SHIFT_NORMALIZATION_DIVISOR).round(2)
    unit_summary["Total_Required_Hours"] = (unit_summary["Total_Required_Hours"] / SHIFT_NORMALIZATION_DIVISOR).round(2)
    unit_summary["Avg_Patient_Workload"] = unit_summary["Avg_Patient_Workload"].round(2)

    return unit_summary


def calculate_workload_imbalance_metrics(staffing_df: pd.DataFrame) -> dict:
    """
    Computes explainable statistical workload imbalance metrics across hospital units.

    Parameters:
    -----------
    staffing_df : pd.DataFrame
        DataFrame containing unit staffing summary with 'Workload_Per_Nurse'.

    Returns:
    --------
    dict
        Dictionary containing:
        - 'Max_Workload_Per_Nurse': Highest workload intensity observed (float)
        - 'Min_Workload_Per_Nurse': Lowest workload intensity observed (float)
        - 'Workload_Imbalance_Max_Min_Gap': Max - Min spread (float)
        - 'Workload_Imbalance_Std': Sample standard deviation (float)
        - 'Workload_Mean': Arithmetic mean of workload per nurse (float)
        - 'Coefficient_of_Variation_Pct': CV percentage (Std / Mean * 100) (float)

    Error Boundaries & Safeguards:
    ------------------------------
    - Handles single-unit or empty staffing DataFrames without crashing.
    - Avoids ZeroDivisionError when Mean is zero or negative.
    - Replaces NaNs resulting from single observations with 0.0.
    """
    if staffing_df.empty or "Workload_Per_Nurse" not in staffing_df.columns:
        return {
            "Max_Workload_Per_Nurse": 0.0,
            "Min_Workload_Per_Nurse": 0.0,
            "Workload_Imbalance_Max_Min_Gap": 0.0,
            "Workload_Imbalance_Std": 0.0,
            "Workload_Mean": 0.0,
            "Coefficient_of_Variation_Pct": 0.0
        }

    wpn = staffing_df["Workload_Per_Nurse"].dropna()
    
    if len(wpn) == 0:
        return {
            "Max_Workload_Per_Nurse": 0.0,
            "Min_Workload_Per_Nurse": 0.0,
            "Workload_Imbalance_Max_Min_Gap": 0.0,
            "Workload_Imbalance_Std": 0.0,
            "Workload_Mean": 0.0,
            "Coefficient_of_Variation_Pct": 0.0
        }

    max_wpn = float(wpn.max())
    min_wpn = float(wpn.min())
    max_min_gap = round(max_wpn - min_wpn, 2)
    std_wpn = float(wpn.std()) if len(wpn) > 1 else 0.0
    mean_wpn = float(wpn.mean())
    cv_pct = round((std_wpn / mean_wpn * 100), 2) if mean_wpn > 0 else 0.0

    return {
        "Max_Workload_Per_Nurse": round(max_wpn, 2),
        "Min_Workload_Per_Nurse": round(min_wpn, 2),
        "Workload_Imbalance_Max_Min_Gap": max_min_gap,
        "Workload_Imbalance_Std": round(std_wpn, 2),
        "Workload_Mean": round(mean_wpn, 2),
        "Coefficient_of_Variation_Pct": cv_pct
    }


if __name__ == "__main__":
    from src.data_cleaning import run_cleaning_pipeline
    _, _, df_patients_clean = run_cleaning_pipeline()
    workload_df = calculate_unit_workload(df_patients_clean)
    print("Unit Workload Sample:")
    print(workload_df.head())
