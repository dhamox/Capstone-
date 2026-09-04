import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Prototype Acuity Weights (Note: Synthetic assumptions, not validated clinical standards)
DEFAULT_ACUITY_WEIGHTS = {
    "Low": 1.0,
    "Medium": 1.25,
    "High": 1.5,
    "Critical": 2.0
}

def calculate_patient_workload(df_patients, acuity_weights=None, active_only=True):
    """
    Calculates patient workload using formula:
    Patient Workload = Required Nursing Hours * Acuity Weight
    
    Note: Prototype assumption for simulation, not a validated clinical standard.
    """
    if acuity_weights is None:
        acuity_weights = DEFAULT_ACUITY_WEIGHTS

    df = df_patients.copy()
    if active_only and "Transfer_Status" in df.columns:
        df = df[df["Transfer_Status"].isin(["Admitted", "Pending Transfer"])].copy()

    df["Acuity_Weight"] = df["Acuity_Level"].map(lambda x: acuity_weights.get(x, 1.0))
    df["Patient_Workload"] = df["Required_Nursing_Hours"] * df["Acuity_Weight"]
    return df


def calculate_unit_workload(df_patients, acuity_weights=None):
    """
    Aggregates workload metrics per hospital unit:
    - Total Workload
    - Total Patient Count
    - Average Workload per Patient
    - Total Required Nursing Hours
    """
    df_p = calculate_patient_workload(df_patients, acuity_weights)
    
    unit_summary = df_p.groupby(["Facility_ID", "Unit_ID"]).agg(
        Total_Patients=("Patient_ID", "count"),
        Cumulative_Workload=("Patient_Workload", "sum"),
        Total_Required_Hours=("Required_Nursing_Hours", "sum"),
        Avg_Patient_Workload=("Patient_Workload", "mean")
    ).reset_index()

    # Shift Workload (Assuming 12h shift operational cycle across active admitted census)
    unit_summary["Total_Workload"] = (unit_summary["Cumulative_Workload"] / 15.0).round(2)
    unit_summary["Total_Required_Hours"] = (unit_summary["Total_Required_Hours"] / 15.0).round(2)
    unit_summary["Avg_Patient_Workload"] = unit_summary["Avg_Patient_Workload"].round(2)

    return unit_summary


if __name__ == "__main__":
    from src.data_cleaning import run_cleaning_pipeline
    _, _, df_patients = run_cleaning_pipeline()
    workload_df = calculate_unit_workload(df_patients)
    print("Unit Workload Sample:")
    print(workload_df.head())
