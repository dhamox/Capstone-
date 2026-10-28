"""
Staffing Calculation Module
===========================
Project: Shift Workload-Balancing Simulator for Hospital Patient Transfers
Author: Hospital Operations Research & AI Engineering Team
Version: 3.0.0 (Review 3 Final Release)

Description:
    Computes unit-level staffing requirements, available nurse capacity,
    staffing shortages (gaps), donor surpluses, and nurse workload intensities.

Mathematical Formulation:
    1. Required Nurses based on Patient Workload:
       N_req = ceil( Total_Unit_Workload / Shift_Hours )
       where Shift_Hours defaults to 12.0 hours per shift.

    2. Target Safe Staffing:
       N_target = max( Minimum_Staff_Bound, N_req )
       Enforces minimum safe staffing regulatory/clinical standards regardless of census.

    3. Staffing Shortage (Gap):
       Staffing_Gap = max( 0, N_target - N_active )
       Positive integer representing the count of nurses required to stabilize the unit.

    4. Donor Staffing Surplus:
       Staffing_Surplus = max( 0, N_active - N_target )
       Positive integer representing nurses available to safely donate to deficit units.

    5. Workload Intensity Per Active Nurse:
       Workload_Per_Nurse = Total_Unit_Workload / N_active   (if N_active > 0)
                          = Total_Unit_Workload              (if N_active == 0, error boundary)
"""

import os
import sys
import pandas as pd
import numpy as np

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.workload import calculate_unit_workload


def calculate_unit_staffing(
    df_units: pd.DataFrame,
    df_nurses: pd.DataFrame,
    df_patients: pd.DataFrame,
    acuity_weights: dict = None,
    shift_hours: float = 12.0
) -> pd.DataFrame:
    """
    Computes comprehensive unit staffing metrics by combining units, nurses, and patient workloads.

    Parameters:
    -----------
    df_units : pd.DataFrame
        Hospital units roster table. Required columns:
        - 'Facility_ID': Hospital identifier (str)
        - 'Unit_ID': Unique unit identifier (str)
        - 'Unit_Type': Specialty ('ICU', 'Emergency', 'Med-Surg', etc.)
        - 'Bed_Capacity': Licensed bed capacity (int)
        - 'Occupied_Beds': Currently occupied beds (int)
        - 'Minimum_Staff': Minimum regulatory safe staffing threshold (int)
        - 'Maximum_Staff': Maximum physical nurse staffing capacity (int)
        - 'Current_Staff': Base assigned nurses (int)
    df_nurses : pd.DataFrame
        Nurse roster table. Required columns:
        - 'Nurse_ID': Unique nurse identifier (str)
        - 'Unit_ID': Unit assignment (str)
        - 'Availability_Status': Status ('Available', 'On Shift', 'Off Duty', etc.)
        - 'Available_Hours': Shift availability in hours (float)
    df_patients : pd.DataFrame
        Patient records table used for calculating unit workload.
    acuity_weights : dict, optional
        Clinical acuity weight mapping.
    shift_hours : float, default=12.0
        Hours per standard operational shift.

    Returns:
    --------
    pd.DataFrame
        Augmented units table containing:
        - 'Active_Nurses': Count of active, available nurses on shift (int)
        - 'Available_Hours': Total available care hours (float)
        - 'Total_Patients': Active patient census in unit (int)
        - 'Total_Workload': Aggregated shift workload (float)
        - 'Required_Nurses_Workload': Nurses needed by acuity workload (int)
        - 'Target_Nurses': Max of Minimum_Staff and Required_Nurses_Workload (int)
        - 'Staffing_Gap': Shortage deficit count (int)
        - 'Staffing_Surplus': Safe excess donor count (int)
        - 'Workload_Per_Nurse': Workload intensity score per active nurse (float)

    Error Boundaries & Safeguards:
    ------------------------------
    - Zero active nurses (N_active = 0): Workload_Per_Nurse defaults to Total_Workload
      instead of raising ZeroDivisionError.
    - Missing units/nurses data is gracefully imputed with zeros.
    - Non-positive shift_hours defaults to 12.0 to prevent zero division.
    - Negative gaps or surpluses are strictly clipped to 0.0 using .clip(lower=0).
    """
    if shift_hours <= 0:
        shift_hours = 12.0

    # 1. Calculate aggregated unit workload
    unit_workload = calculate_unit_workload(df_patients, acuity_weights)

    # 2. Filter for active available nurses on duty (with schema validation guard)
    if not df_nurses.empty and "Availability_Status" in df_nurses.columns and "Unit_ID" in df_nurses.columns:
        available_nurses = df_nurses[df_nurses["Availability_Status"].isin(["Available", "On Shift", "Reassigned"])].copy()
        if not available_nurses.empty:
            nurse_summary = available_nurses.groupby("Unit_ID").agg(
                Active_Nurses=("Nurse_ID", "count"),
                Available_Hours=("Available_Hours", "sum")
            ).reset_index()
        else:
            nurse_summary = pd.DataFrame(columns=["Unit_ID", "Active_Nurses", "Available_Hours"])
    else:
        nurse_summary = pd.DataFrame(columns=["Unit_ID", "Active_Nurses", "Available_Hours"])


    # 3. Merge Unit Roster, Patient Workload, and Nurse Availability
    merged = pd.merge(df_units, unit_workload, on=["Facility_ID", "Unit_ID"], how="left")
    merged = pd.merge(merged, nurse_summary, on="Unit_ID", how="left")

    # Impute missing values for units with zero active census or zero nurses
    merged["Total_Patients"] = merged["Total_Patients"].fillna(0).astype(int)
    merged["Total_Workload"] = merged["Total_Workload"].fillna(0.0).astype(float)
    merged["Total_Required_Hours"] = merged["Total_Required_Hours"].fillna(0.0).astype(float)
    merged["Active_Nurses"] = merged["Active_Nurses"].fillna(0).astype(int)
    merged["Available_Hours"] = merged["Available_Hours"].fillna(0.0).astype(float)

    # 4. Compute workload-derived nurse requirements
    merged["Required_Nurses_Workload"] = np.ceil(merged["Total_Workload"] / shift_hours).astype(int)
    
    # 5. Target Nurses is the maximum of regulatory minimum and workload requirement
    merged["Target_Nurses"] = merged[["Minimum_Staff", "Required_Nurses_Workload"]].max(axis=1)

    # 6. Staffing Gap (Positive if understaffed)
    merged["Staffing_Gap"] = (merged["Target_Nurses"] - merged["Active_Nurses"]).clip(lower=0).astype(int)

    # 7. Staffing Surplus (Positive if surplus nurses exist above Target_Nurses & Minimum_Staff)
    merged["Staffing_Surplus"] = (merged["Active_Nurses"] - merged["Target_Nurses"]).clip(lower=0).astype(int)

    # 8. Workload intensity per nurse (with ZeroDivisionError safeguard)
    merged["Workload_Per_Nurse"] = np.where(
        merged["Active_Nurses"] > 0,
        (merged["Total_Workload"] / merged["Active_Nurses"]).round(2),
        merged["Total_Workload"].round(2)
    )

    return merged


if __name__ == "__main__":
    from src.data_cleaning import run_cleaning_pipeline
    df_u, df_n, df_p = run_cleaning_pipeline()
    staffing_df = calculate_unit_staffing(df_u, df_n, df_p)
    print("Staffing Summary Sample:")
    print(staffing_df[["Unit_ID", "Unit_Type", "Active_Nurses", "Minimum_Staff", "Total_Workload", "Staffing_Gap", "Staffing_Surplus", "Workload_Per_Nurse"]].head(10))
