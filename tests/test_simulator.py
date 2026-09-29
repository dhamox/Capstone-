import os
import sys
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_cleaning import clean_patients_data, clean_nurses_data, clean_units_data, run_cleaning_pipeline
from src.workload import calculate_patient_workload, calculate_unit_workload, calculate_workload_imbalance_metrics
from src.staffing import calculate_unit_staffing
from src.skill_matching import evaluate_reassignment_candidates, validate_safe_reassignment
from src.simulator import run_scenario_simulation, run_all_operating_scenarios, run_sensitivity_analysis, run_reproducible_experiment
from src.transfer_logic import evaluate_patient_transfer_request, process_batch_transfer_requests
from src.escalation import evaluate_action_escalations, get_sample_action_items
from src.audit_log import record_manager_decision, load_audit_log

def test_data_cleaning_pipeline():
    """Verify data cleaning rules handle duplicates, negative values, and missing values."""
    df_pat_raw = pd.DataFrame([
        {"Patient_ID": "P001", "Age": -5, "Acuity_Level": "Ultra-Critical", "Required_Nursing_Hours": 99.0, "Required_Skill": "icu", "Transfer_Status": "Admitted"},
        {"Patient_ID": "P001", "Age": -5, "Acuity_Level": "Ultra-Critical", "Required_Nursing_Hours": 99.0, "Required_Skill": "icu", "Transfer_Status": "Admitted"},
        {"Patient_ID": "P002", "Age": 45, "Acuity_Level": np.nan, "Required_Nursing_Hours": np.nan, "Required_Skill": "Med-Surg", "Transfer_Status": "Admitted"}
    ])

    df_clean = clean_patients_data(df_pat_raw)
    assert len(df_clean) == 2
    assert (df_clean["Age"] > 0).all()
    assert "Ultra-Critical" not in df_clean["Acuity_Level"].values
    assert df_clean.loc[df_clean["Patient_ID"] == "P001", "Required_Nursing_Hours"].values[0] <= 16.0

def test_workload_and_imbalance_metrics():
    """Verify workload math and imbalance metrics calculation."""
    df_pat = pd.DataFrame([
        {"Patient_ID": "P101", "Acuity_Level": "Low", "Required_Nursing_Hours": 2.0, "Transfer_Status": "Admitted"},
        {"Patient_ID": "P102", "Acuity_Level": "Critical", "Required_Nursing_Hours": 10.0, "Transfer_Status": "Admitted"}
    ])
    df_res = calculate_patient_workload(df_pat)
    assert df_res.loc[df_res["Patient_ID"] == "P101", "Patient_Workload"].values[0] == 2.0
    assert df_res.loc[df_res["Patient_ID"] == "P102", "Patient_Workload"].values[0] == 20.0

    df_staffing = pd.DataFrame([
        {"Unit_ID": "U1", "Workload_Per_Nurse": 10.0},
        {"Unit_ID": "U2", "Workload_Per_Nurse": 20.0}
    ])
    metrics = calculate_workload_imbalance_metrics(df_staffing)
    assert metrics["Workload_Imbalance_Max_Min_Gap"] == 10.0
    assert metrics["Workload_Mean"] == 15.0

def test_validate_safe_reassignment_rules():
    """Verify validate_safe_reassignment function enforcing safety criteria."""
    nurse = pd.Series({"Nurse_ID": "N01", "Specialty": "Med-Surg", "Nurse_Skill_Level": 2, "Availability_Status": "Available", "Shift": "Day"})
    donor_u = pd.Series({"Unit_ID": "U01", "Minimum_Staff": 5})
    rec_u = pd.Series({"Unit_ID": "U02", "Unit_Type": "ICU", "Bed_Capacity": 20, "Occupied_Beds": 10})
    donor_stf = pd.Series({"Active_Nurses": 6})
    rec_stf = pd.Series({"Active_Nurses": 4})

    # Med-Surg nurse to ICU -> Skill Mismatch
    res = validate_safe_reassignment(nurse, donor_u, rec_u, donor_stf, rec_stf)
    assert res["status"] == "Unsafe"
    assert "Skill mismatch" in res["reason"]

def test_patient_transfer_logic_outcomes():
    """Verify patient transfer logic assigning 1 of 7 outcome states."""
    p = pd.Series({"Patient_ID": "P99", "Acuity_Level": "Critical", "Required_Skill": "ICU"})
    src_u = pd.Series({"Unit_ID": "U01", "Facility_ID": "F01"})
    dest_u = pd.Series({"Unit_ID": "U02", "Facility_ID": "F01", "Unit_Type": "ICU", "Bed_Capacity": 10, "Occupied_Beds": 10}) # Full
    dest_stf = pd.Series({"Staffing_Gap": 2, "Active_Nurses": 5})
    df_nurses = pd.DataFrame()

    eval_res = evaluate_patient_transfer_request(p, src_u, dest_u, dest_stf, df_nurses)
    assert eval_res["Outcome"] == "Blocked – no capacity"

def test_all_8_operating_scenarios():
    """Verify execution of all 8 operating scenarios."""
    df_u, df_n, df_p = run_cleaning_pipeline()
    res_dict, summary_df = run_all_operating_scenarios(df_u, df_n, df_p)
    assert len(summary_df) == 8
    assert "Scenario 8 – Multi-Unit Stress" in summary_df["Scenario_Name"].values

def test_reproducible_multi_seed_experiment():
    """Verify multi-seed experiment runs across seeds and produces summary statistics."""
    df_seeds, df_summary = run_reproducible_experiment(num_seeds=3)
    assert len(df_seeds) == 3
    assert "Mean Value" in df_summary.columns

def test_auto_escalation_engine():
    """Verify auto-escalation of overdue high-priority action items."""
    df_actions = pd.DataFrame([{
        "Action_ID": "ACT-TEST",
        "Issue": "Critical Gap",
        "Priority": "High",
        "Owner": "Mgr",
        "Due_Date": "2026-08-01", # Overdue
        "Status": "Open",
        "Escalation_Level": "Level 0 – Normal",
        "Escalation_Date": "",
        "Comments": ""
    }])
    esc_df = evaluate_action_escalations(df_actions, current_date="2026-09-04")
    assert esc_df.iloc[0]["Escalation_Level"] == "Level 2 – Clinical/Ops Lead"

def test_audit_log_recording(tmp_path):
    """Verify audit log recording and loading."""
    log_file = os.path.join(tmp_path, "test_audit.csv")
    record_manager_decision("REC-001", "N01", "U1", "U2", "Manager", "Approved", "Test approve", audit_file=log_file)
    log_df = load_audit_log(audit_file=log_file)
    assert len(log_df) == 1
    assert log_df.iloc[0]["Decision"] == "Approved"
