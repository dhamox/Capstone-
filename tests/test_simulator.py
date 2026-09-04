import os
import sys
import pytest
import pandas as pd
import numpy as np

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_cleaning import clean_patients_data, clean_nurses_data, clean_units_data
from src.workload import calculate_patient_workload, calculate_unit_workload
from src.staffing import calculate_unit_staffing
from src.skill_matching import evaluate_reassignment_candidates
from src.simulator import run_scenario_simulation, run_sensitivity_analysis

def test_data_cleaning_pipeline():
    """Verify data cleaning rules handle duplicates, negative values, and missing values."""
    df_pat_raw = pd.DataFrame([
        {"Patient_ID": "P001", "Age": -5, "Acuity_Level": "Ultra-Critical", "Required_Nursing_Hours": 99.0, "Required_Skill": "icu", "Transfer_Status": "Admitted"},
        {"Patient_ID": "P001", "Age": -5, "Acuity_Level": "Ultra-Critical", "Required_Nursing_Hours": 99.0, "Required_Skill": "icu", "Transfer_Status": "Admitted"}, # Duplicate
        {"Patient_ID": "P002", "Age": 45, "Acuity_Level": np.nan, "Required_Nursing_Hours": np.nan, "Required_Skill": "Med-Surg", "Transfer_Status": "Admitted"}
    ])

    df_clean = clean_patients_data(df_pat_raw)
    
    # 1. Deduplication check
    assert len(df_clean) == 2
    # 2. Negative age fix check
    assert (df_clean["Age"] > 0).all()
    # 3. Invalid acuity level replacement check
    assert "Ultra-Critical" not in df_clean["Acuity_Level"].values
    assert df_clean.loc[df_clean["Patient_ID"] == "P001", "Acuity_Level"].values[0] == "Critical"
    # 4. Outlier capping check
    assert df_clean.loc[df_clean["Patient_ID"] == "P001", "Required_Nursing_Hours"].values[0] <= 16.0

def test_workload_calculation():
    """Verify Patient Workload = Required Nursing Hours * Acuity Weight."""
    df_pat = pd.DataFrame([
        {"Patient_ID": "P101", "Acuity_Level": "Low", "Required_Nursing_Hours": 2.0, "Transfer_Status": "Admitted"},
        {"Patient_ID": "P102", "Acuity_Level": "Critical", "Required_Nursing_Hours": 10.0, "Transfer_Status": "Admitted"}
    ])

    df_res = calculate_patient_workload(df_pat)
    # Low acuity weight = 1.0 -> Workload = 2.0
    assert df_res.loc[df_res["Patient_ID"] == "P101", "Patient_Workload"].values[0] == 2.0
    # Critical acuity weight = 2.0 -> Workload = 20.0
    assert df_res.loc[df_res["Patient_ID"] == "P102", "Patient_Workload"].values[0] == 20.0

def test_edge_case_no_donor_surplus():
    """Failure Case 2: No donor unit surplus (donor at minimum staff) -> block transfer."""
    df_units = pd.DataFrame([{
        "Facility_ID": "F01", "Unit_ID": "U001", "Unit_Type": "ICU",
        "Bed_Capacity": 20, "Occupied_Beds": 10, "Minimum_Staff": 5, "Maximum_Staff": 10, "Current_Staff": 5
    }, {
        "Facility_ID": "F01", "Unit_ID": "U002", "Unit_Type": "Med-Surg",
        "Bed_Capacity": 20, "Occupied_Beds": 10, "Minimum_Staff": 5, "Maximum_Staff": 10, "Current_Staff": 2
    }])

    df_nurses = pd.DataFrame([
        {"Nurse_ID": "N01", "Unit_ID": "U001", "Facility_ID": "F01", "Shift": "Day", "Available_Hours": 12.0, "Nurse_Skill_Level": 4, "Specialty": "Med-Surg", "Availability_Status": "Available"}
    ])

    # Patients creating workload gap in U002
    df_patients = pd.DataFrame([
        {"Patient_ID": f"P{i}", "Unit_ID": "U002", "Facility_ID": "F01", "Acuity_Level": "Critical", "Required_Nursing_Hours": 10.0, "Transfer_Status": "Admitted"}
        for i in range(10)
    ])

    staffing = calculate_unit_staffing(df_units, df_nurses, df_patients)
    match_res = evaluate_reassignment_candidates(df_units, df_nurses, staffing)

    # Reassignments should be empty because U001 active nurses (1) <= Minimum_Staff (5)
    assert match_res["safe_reassignment_capacity"] == 0

def test_edge_case_receiving_unit_at_capacity():
    """Failure Case 3: Receiving unit physical bed capacity reached (Occupied >= Capacity) -> block transfer."""
    df_units = pd.DataFrame([{
        "Facility_ID": "F01", "Unit_ID": "U001", "Unit_Type": "ICU",
        "Bed_Capacity": 10, "Occupied_Beds": 10, "Minimum_Staff": 2, "Maximum_Staff": 10, "Current_Staff": 8
    }, {
        "Facility_ID": "F01", "Unit_ID": "U002", "Unit_Type": "Med-Surg",
        "Bed_Capacity": 10, "Occupied_Beds": 10, "Minimum_Staff": 2, "Maximum_Staff": 10, "Current_Staff": 2
    }])

    df_nurses = pd.DataFrame([
        {"Nurse_ID": "N01", "Unit_ID": "U001", "Facility_ID": "F01", "Shift": "Day", "Available_Hours": 12.0, "Nurse_Skill_Level": 3, "Specialty": "Med-Surg", "Availability_Status": "Available"},
        {"Nurse_ID": "N02", "Unit_ID": "U001", "Facility_ID": "F01", "Shift": "Day", "Available_Hours": 12.0, "Nurse_Skill_Level": 3, "Specialty": "Med-Surg", "Availability_Status": "Available"}
    ])

    df_patients = pd.DataFrame([
        {"Patient_ID": f"P{i}", "Unit_ID": "U002", "Facility_ID": "F01", "Acuity_Level": "High", "Required_Nursing_Hours": 8.0, "Transfer_Status": "Admitted"}
        for i in range(8)
    ])

    staffing = calculate_unit_staffing(df_units, df_nurses, df_patients)
    match_res = evaluate_reassignment_candidates(df_units, df_nurses, staffing)

    # Transfer blocked due to receiving unit at bed capacity
    assert match_res["safe_reassignment_capacity"] == 0
    assert len(match_res["unsafe_prevented"]) > 0

def test_scenario_simulation_execution():
    """Verify end-to-end scenario simulation executes without errors."""
    from src.data_cleaning import run_cleaning_pipeline
    df_units, df_nurses, df_patients = run_cleaning_pipeline()
    res = run_scenario_simulation(df_units, df_nurses, df_patients, scenario_name="Baseline")
    assert "summary" in res
    assert res["summary"]["Total_Patients"] == 5200
    assert res["summary"]["Imbalance_Reduction_Pct"] >= 0.0
