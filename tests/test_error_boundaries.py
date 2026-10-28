"""
Granular Unit Tests for System Error Boundaries & Safeguards
============================================================
Project: Shift Workload-Balancing Simulator for Hospital Patient Transfers
Author: Hospital Operations Research & AI Engineering Team
Version: 3.0.0 (Review 3 Final Release)

This test module systematically validates critical edge conditions, mathematical boundaries,
concurrency locks, and data integrity safeguards across the simulator architecture.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.workload import calculate_patient_workload, calculate_unit_workload, calculate_workload_imbalance_metrics
from src.staffing import calculate_unit_staffing
from src.skill_matching import validate_safe_reassignment, evaluate_reassignment_candidates
from src.transfer_logic import evaluate_patient_transfer_request
from src.escalation import evaluate_action_escalations
from src.audit_log import record_manager_decision, load_audit_log


class TestMathematicalAndWorkloadBoundaries:
    """Tests mathematical edge cases, zero divisions, and extreme inputs in workload math."""

    def test_zero_active_nurses_division_by_zero_protection(self):
        """Boundary: Unit has 0 active nurses. Workload_Per_Nurse must not raise ZeroDivisionError."""
        df_units = pd.DataFrame([{
            "Facility_ID": "F01", "Unit_ID": "U_ZERO", "Unit_Type": "Med-Surg",
            "Bed_Capacity": 20, "Occupied_Beds": 10, "Minimum_Staff": 5, "Maximum_Staff": 10, "Current_Staff": 5
        }])
        df_nurses = pd.DataFrame()  # Empty nurse roster
        df_patients = pd.DataFrame([{
            "Patient_ID": "P01", "Facility_ID": "F01", "Unit_ID": "U_ZERO",
            "Acuity_Level": "Medium", "Required_Nursing_Hours": 5.0, "Transfer_Status": "Admitted"
        }])

        staffing = calculate_unit_staffing(df_units, df_nurses, df_patients)
        assert len(staffing) == 1
        assert staffing.iloc[0]["Active_Nurses"] == 0
        # When active nurses = 0, Workload_Per_Nurse defaults to Total_Workload
        assert staffing.iloc[0]["Workload_Per_Nurse"] == staffing.iloc[0]["Total_Workload"]
        assert not np.isinf(staffing.iloc[0]["Workload_Per_Nurse"])
        assert not np.isnan(staffing.iloc[0]["Workload_Per_Nurse"])

    def test_empty_patient_pool_boundary(self):
        """Boundary: Zero patients admitted. Workload calculations must return zeroed metrics without crashing."""
        df_empty_patients = pd.DataFrame()
        unit_wl = calculate_unit_workload(df_empty_patients)
        assert unit_wl.empty
        assert "Total_Workload" in unit_wl.columns

    def test_unclassified_acuity_weight_fallback(self):
        """Boundary: Unknown/corrupt acuity category defaults gracefully to weight 1.0."""
        df_patients = pd.DataFrame([{
            "Patient_ID": "P_UNKNOWN", "Acuity_Level": "UNKNOWN_CUSTOM_TIER",
            "Required_Nursing_Hours": 4.0, "Transfer_Status": "Admitted"
        }])
        res = calculate_patient_workload(df_patients)
        assert res.iloc[0]["Acuity_Weight"] == 1.0
        assert res.iloc[0]["Patient_Workload"] == 4.0

    def test_imbalance_metrics_single_unit_boundary(self):
        """Boundary: Only 1 unit in hospital. Standard deviation must return 0.0 without crash."""
        df_staffing = pd.DataFrame([{"Unit_ID": "U01", "Workload_Per_Nurse": 14.5}])
        metrics = calculate_workload_imbalance_metrics(df_staffing)
        assert metrics["Workload_Imbalance_Std"] == 0.0
        assert metrics["Workload_Imbalance_Max_Min_Gap"] == 0.0
        assert metrics["Coefficient_of_Variation_Pct"] == 0.0


class TestClinicalSafetyAndCapacityBoundaries:
    """Tests clinical safety boundaries, minimum staffing limits, and physical bed constraints."""

    def test_donor_staffing_exact_threshold_boundaries(self):
        """
        Boundary Analysis:
        - If active == min_staff: transfer drops active - 1 < min_staff -> BLOCKED.
        - If active == min_staff + 1: transfer drops active - 1 == min_staff -> SAFE.
        """
        nurse = pd.Series({"Nurse_ID": "N01", "Specialty": "ICU", "Nurse_Skill_Level": 4, "Availability_Status": "Available", "Shift": "Day"})
        donor_u = pd.Series({"Unit_ID": "U_DONOR", "Minimum_Staff": 5})
        rec_u = pd.Series({"Unit_ID": "U_REC", "Unit_Type": "ICU", "Bed_Capacity": 20, "Occupied_Beds": 10})
        rec_stf = pd.Series({"Active_Nurses": 4})

        # Sub-case A: active == 5 (min_staff == 5) -> remaining = 4 < 5 -> MUST BE UNSAFE
        donor_stf_at_min = pd.Series({"Active_Nurses": 5})
        res_blocked = validate_safe_reassignment(nurse, donor_u, rec_u, donor_stf_at_min, rec_stf)
        assert res_blocked["status"] == "Unsafe"
        assert "breach donor unit" in res_blocked["reason"]

        # Sub-case B: active == 6 (min_staff == 5) -> remaining = 5 == 5 -> MUST BE SAFE
        donor_stf_above_min = pd.Series({"Active_Nurses": 6})
        res_safe = validate_safe_reassignment(nurse, donor_u, rec_u, donor_stf_above_min, rec_stf)
        assert res_safe["status"] == "Safe"
        assert res_safe["remaining_donor_staffing"] == 5

    def test_receiving_bed_capacity_exact_threshold_boundaries(self):
        """
        Boundary Analysis:
        - If Occupied == Capacity: Blocked.
        - If Occupied == Capacity - 1: Safe.
        """
        nurse = pd.Series({"Nurse_ID": "N01", "Specialty": "Med-Surg", "Nurse_Skill_Level": 3, "Availability_Status": "Available", "Shift": "Day"})
        donor_u = pd.Series({"Unit_ID": "U_DONOR", "Minimum_Staff": 4})
        donor_stf = pd.Series({"Active_Nurses": 8})
        rec_stf = pd.Series({"Active_Nurses": 4})

        # Sub-case A: 100% capacity saturation (20/20) -> MUST BE UNSAFE
        rec_full = pd.Series({"Unit_ID": "U_REC", "Unit_Type": "Med-Surg", "Bed_Capacity": 20, "Occupied_Beds": 20})
        res_full = validate_safe_reassignment(nurse, donor_u, rec_full, donor_stf, rec_stf)
        assert res_full["status"] == "Unsafe"
        assert "bed capacity" in res_full["reason"]

        # Sub-case B: 95% capacity (19/20 beds occupied) -> MUST BE SAFE
        rec_room = pd.Series({"Unit_ID": "U_REC", "Unit_Type": "Med-Surg", "Bed_Capacity": 20, "Occupied_Beds": 19})
        res_room = validate_safe_reassignment(nurse, donor_u, rec_room, donor_stf, rec_stf)
        assert res_room["status"] == "Safe"

    def test_specialty_competency_tier_boundaries(self):
        """
        Boundary Analysis for Critical Care (ICU):
        - Med-Surg nurse Level 3 -> Unsafe for ICU.
        - Med-Surg nurse Level 4 (Expert certified) -> Safe for ICU.
        """
        donor_u = pd.Series({"Unit_ID": "U_DONOR", "Minimum_Staff": 4})
        donor_stf = pd.Series({"Active_Nurses": 8})
        rec_icu = pd.Series({"Unit_ID": "U_ICU", "Unit_Type": "ICU", "Bed_Capacity": 20, "Occupied_Beds": 10})
        rec_stf = pd.Series({"Active_Nurses": 4})

        # Level 3 non-ICU nurse -> Unsafe
        nurse_lvl3 = pd.Series({"Nurse_ID": "N03", "Specialty": "Med-Surg", "Nurse_Skill_Level": 3, "Availability_Status": "Available", "Shift": "Day"})
        res_lvl3 = validate_safe_reassignment(nurse_lvl3, donor_u, rec_icu, donor_stf, rec_stf)
        assert res_lvl3["status"] == "Unsafe"
        assert "Skill mismatch" in res_lvl3["reason"]

        # Level 4 nurse -> Safe
        nurse_lvl4 = pd.Series({"Nurse_ID": "N04", "Specialty": "Med-Surg", "Nurse_Skill_Level": 4, "Availability_Status": "Available", "Shift": "Day"})
        res_lvl4 = validate_safe_reassignment(nurse_lvl4, donor_u, rec_icu, donor_stf, rec_stf)
        assert res_lvl4["status"] == "Safe"

    def test_nurse_double_assignment_concurrency_lock(self):
        """Boundary: A nurse assigned to Unit A cannot be assigned concurrently to Unit B."""
        df_units = pd.DataFrame([
            {"Facility_ID": "F01", "Unit_ID": "U_DONOR", "Unit_Type": "Med-Surg", "Bed_Capacity": 30, "Occupied_Beds": 10, "Minimum_Staff": 2},
            {"Facility_ID": "F01", "Unit_ID": "U_REC1", "Unit_Type": "Med-Surg", "Bed_Capacity": 30, "Occupied_Beds": 10, "Minimum_Staff": 5},
            {"Facility_ID": "F01", "Unit_ID": "U_REC2", "Unit_Type": "Med-Surg", "Bed_Capacity": 30, "Occupied_Beds": 10, "Minimum_Staff": 5}
        ])
        # Only 1 available nurse in donor unit
        df_nurses = pd.DataFrame([
            {"Nurse_ID": "N_SINGLE", "Unit_ID": "U_DONOR", "Facility_ID": "F01", "Shift": "Day", "Available_Hours": 12.0, "Nurse_Skill_Level": 3, "Specialty": "Med-Surg", "Availability_Status": "Available"}
        ])
        df_staffing = pd.DataFrame([
            {"Unit_ID": "U_DONOR", "Facility_ID": "F01", "Active_Nurses": 4, "Staffing_Surplus": 2, "Staffing_Gap": 0, "Bed_Capacity": 30, "Occupied_Beds": 10, "Minimum_Staff": 2, "Unit_Type": "Med-Surg"},
            {"Unit_ID": "U_REC1", "Facility_ID": "F01", "Active_Nurses": 2, "Staffing_Surplus": 0, "Staffing_Gap": 1, "Bed_Capacity": 30, "Occupied_Beds": 10, "Minimum_Staff": 5, "Unit_Type": "Med-Surg"},
            {"Unit_ID": "U_REC2", "Facility_ID": "F01", "Active_Nurses": 2, "Staffing_Surplus": 0, "Staffing_Gap": 1, "Bed_Capacity": 30, "Occupied_Beds": 10, "Minimum_Staff": 5, "Unit_Type": "Med-Surg"}
        ])

        candidates = evaluate_reassignment_candidates(df_units, df_nurses, df_staffing)
        reassigns = candidates["reassignments"]
        # Candidate nurse N_SINGLE can be reassigned at most once
        assert len(reassigns) == 1
        assert reassigns.iloc[0]["Nurse_ID"] == "N_SINGLE"


class TestEscalationAndAuditBoundaries:
    """Tests action item auto-escalation dates and audit log storage safeguards."""

    def test_escalation_date_comparison_boundary(self):
        """
        Boundary Analysis:
        - Due date yesterday (due < today) -> Escalated.
        - Due date today (due == today) -> Not overdue.
        - Due date tomorrow (due > today) -> Not overdue.
        """
        today = date.today()
        yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        df_actions = pd.DataFrame([
            {"Action_ID": "A_YEST", "Issue": "Issue 1", "Priority": "High", "Status": "Open", "Due_Date": yesterday_str, "Escalation_Level": "Level 0 – Normal", "Comments": ""},
            {"Action_ID": "A_TODAY", "Issue": "Issue 2", "Priority": "High", "Status": "Open", "Due_Date": today_str, "Escalation_Level": "Level 0 – Normal", "Comments": ""},
            {"Action_ID": "A_TOMO", "Issue": "Issue 3", "Priority": "High", "Status": "Open", "Due_Date": tomorrow_str, "Escalation_Level": "Level 0 – Normal", "Comments": ""},
            {"Action_ID": "A_RESOLVED", "Issue": "Issue 4", "Priority": "High", "Status": "Resolved", "Due_Date": yesterday_str, "Escalation_Level": "Level 0 – Normal", "Comments": ""}
        ])

        evaluated = evaluate_action_escalations(df_actions, current_date=today)
        yest_row = evaluated[evaluated["Action_ID"] == "A_YEST"].iloc[0]
        today_row = evaluated[evaluated["Action_ID"] == "A_TODAY"].iloc[0]
        tomo_row = evaluated[evaluated["Action_ID"] == "A_TOMO"].iloc[0]
        resolved_row = evaluated[evaluated["Action_ID"] == "A_RESOLVED"].iloc[0]

        assert yest_row["Escalation_Level"] == "Level 2 – Clinical/Ops Lead"
        assert today_row["Escalation_Level"] == "Level 0 – Normal"
        assert tomo_row["Escalation_Level"] == "Level 0 – Normal"
        assert resolved_row["Escalation_Level"] == "Level 0 – Normal"  # Resolved items must never escalate

    def test_audit_log_corrupt_file_recovery(self, tmp_path):
        """Boundary: If audit log CSV file is empty or corrupted, write succeeds without crash."""
        corrupt_file = os.path.join(tmp_path, "corrupt_audit.csv")
        with open(corrupt_file, "w") as f:
            f.write("")  # 0 bytes file

        record_manager_decision("REC-999", "N99", "U1", "U2", "Supervisor", "Approved", "Test reason", audit_file=corrupt_file)
        loaded = load_audit_log(audit_file=corrupt_file)
        assert len(loaded) == 1
        assert loaded.iloc[0]["Recommendation_ID"] == "REC-999"
