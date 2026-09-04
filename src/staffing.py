import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.workload import calculate_unit_workload


def calculate_unit_staffing(df_units, df_nurses, df_patients, acuity_weights=None, shift_hours=12.0):
    """
    Computes unit staffing metrics:
    - Active Nurse Count
    - Total Available Nursing Hours
    - Total Required Workload Hours
    - Required Nurses (Workload Hours / Shift Hours)
    - Staffing Gap (Nurses needed to cover workload or minimum staffing)
    - Donor Staffing Surplus (Nurses available above Minimum Staffing & Workload requirement)
    - Workload Per Nurse (Total Workload / Active Nurses)
    """
    # 1. Workload aggregate
    unit_workload = calculate_unit_workload(df_patients, acuity_weights)

    # 2. Nurse aggregate per unit
    available_nurses = df_nurses[df_nurses["Availability_Status"].isin(["Available", "On Shift"])]
    
    nurse_summary = available_nurses.groupby("Unit_ID").agg(
        Active_Nurses=("Nurse_ID", "count"),
        Available_Hours=("Available_Hours", "sum")
    ).reset_index()

    # 3. Merge Units, Workload, Nurses
    merged = pd.merge(df_units, unit_workload, on=["Facility_ID", "Unit_ID"], how="left")
    merged = pd.merge(merged, nurse_summary, on="Unit_ID", how="left")

    merged["Total_Patients"] = merged["Total_Patients"].fillna(0).astype(int)
    merged["Total_Workload"] = merged["Total_Workload"].fillna(0.0)
    merged["Total_Required_Hours"] = merged["Total_Required_Hours"].fillna(0.0)
    merged["Active_Nurses"] = merged["Active_Nurses"].fillna(0).astype(int)
    merged["Available_Hours"] = merged["Available_Hours"].fillna(0.0)

    # Calculate Required Nurses based on patient workload (Shift hours per nurse = 12.0)
    merged["Required_Nurses_Workload"] = np.ceil(merged["Total_Workload"] / shift_hours).astype(int)


    
    # Target Nurses is max of Minimum_Staff and Required_Nurses_Workload
    merged["Target_Nurses"] = merged[["Minimum_Staff", "Required_Nurses_Workload"]].max(axis=1)

    # Staffing Gap (positive if understaffed)
    merged["Staffing_Gap"] = (merged["Target_Nurses"] - merged["Active_Nurses"]).clip(lower=0)

    # Staffing Surplus (positive if surplus nurses exist above Target_Nurses & Minimum_Staff)
    merged["Staffing_Surplus"] = (merged["Active_Nurses"] - merged["Target_Nurses"]).clip(lower=0)

    # Workload per nurse
    merged["Workload_Per_Nurse"] = np.where(
        merged["Active_Nurses"] > 0,
        (merged["Total_Workload"] / merged["Active_Nurses"]).round(2),
        merged["Total_Workload"].round(2)
    )

    return merged

if __name__ == "__main__":
    from src.data_cleaning import run_cleaning_pipeline
    df_units, df_nurses, df_patients = run_cleaning_pipeline()
    staffing_df = calculate_unit_staffing(df_units, df_nurses, df_patients)
    print("Staffing Summary Sample:")
    print(staffing_df[["Unit_ID", "Unit_Type", "Active_Nurses", "Minimum_Staff", "Total_Workload", "Staffing_Gap", "Staffing_Surplus", "Workload_Per_Nurse"]].head(10))
