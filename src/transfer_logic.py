import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def evaluate_patient_transfer_request(
    patient_row,
    source_unit_row,
    dest_unit_row,
    dest_staffing_row,
    available_nurses_df
):
    """
    Evaluates a patient transfer request between source and destination units/facilities.
    
    Returns a structured dictionary with 1 of 7 outcome states:
    1. Approved for simulation
    2. Requires clinical review
    3. Blocked – no capacity
    4. Blocked – insufficient staffing
    5. Blocked – no skill match
    6. Blocked – unsafe reassignment
    7. Escalated
    """
    patient_id = patient_row["Patient_ID"]
    acuity = patient_row["Acuity_Level"]
    required_skill = patient_row["Required_Skill"]

    src_unit_id = source_unit_row["Unit_ID"]
    src_facility = source_unit_row["Facility_ID"]
    
    dest_unit_id = dest_unit_row["Unit_ID"]
    dest_facility = dest_unit_row["Facility_ID"]
    dest_type = dest_unit_row["Unit_Type"]
    dest_bed_cap = dest_unit_row["Bed_Capacity"]
    dest_occupied = dest_unit_row["Occupied_Beds"]

    dest_gap = dest_staffing_row.get("Staffing_Gap", 0)
    dest_active_nurses = dest_staffing_row.get("Active_Nurses", 0)

    # 1. Capacity Check: Blocked – no capacity
    if dest_occupied >= dest_bed_cap:
        return {
            "Patient_ID": patient_id,
            "Acuity_Level": acuity,
            "Source_Unit": src_unit_id,
            "Source_Facility": src_facility,
            "Dest_Unit": dest_unit_id,
            "Dest_Facility": dest_facility,
            "Outcome": "Blocked – no capacity",
            "Rationale": f"Destination unit {dest_unit_id} is at 100% bed capacity ({dest_occupied}/{dest_bed_cap} occupied beds).",
            "Priority": "High" if acuity in ["High", "Critical"] else "Medium"
        }

    # 2. Staffing Check: Blocked – insufficient staffing
    if dest_active_nurses <= 0 or (dest_gap >= 5 and acuity == "Critical"):
        return {
            "Patient_ID": patient_id,
            "Acuity_Level": acuity,
            "Source_Unit": src_unit_id,
            "Source_Facility": src_facility,
            "Dest_Unit": dest_unit_id,
            "Dest_Facility": dest_facility,
            "Outcome": "Blocked – insufficient staffing",
            "Rationale": f"Destination unit {dest_unit_id} has severe staffing deficit (Active staff: {dest_active_nurses}, Gap: {dest_gap}).",
            "Priority": "High"
        }

    # 3. Skill Match Check: Blocked – no skill match
    qualified_nurses = available_nurses_df[
        (available_nurses_df["Unit_ID"] == dest_unit_id) &
        (available_nurses_df["Specialty"].str.upper() == required_skill.upper())
    ]

    if qualified_nurses.empty and required_skill in ["ICU", "Oncology", "Emergency"]:
        return {
            "Patient_ID": patient_id,
            "Acuity_Level": acuity,
            "Source_Unit": src_unit_id,
            "Source_Facility": src_facility,
            "Dest_Unit": dest_unit_id,
            "Dest_Facility": dest_facility,
            "Outcome": "Blocked – no skill match",
            "Rationale": f"Destination unit {dest_unit_id} has no available nurse certified in required specialty '{required_skill}'.",
            "Priority": "High"
        }

    # 4. Critical Escalation Check: Escalated
    if acuity == "Critical" and dest_gap > 3:
        return {
            "Patient_ID": patient_id,
            "Acuity_Level": acuity,
            "Source_Unit": src_unit_id,
            "Source_Facility": src_facility,
            "Dest_Unit": dest_unit_id,
            "Dest_Facility": dest_facility,
            "Outcome": "Escalated",
            "Rationale": f"Critical acuity patient transfer to high-shortage unit {dest_unit_id} requires immediate Operations Lead escalation.",
            "Priority": "High"
        }

    # 5. Clinical Review Gate: Requires clinical review
    if acuity in ["High", "Critical"] or src_facility != dest_facility:
        return {
            "Patient_ID": patient_id,
            "Acuity_Level": acuity,
            "Source_Unit": src_unit_id,
            "Source_Facility": src_facility,
            "Dest_Unit": dest_unit_id,
            "Dest_Facility": dest_facility,
            "Outcome": "Requires clinical review",
            "Rationale": f"Inter-facility or high-acuity transfer requires clinical charge nurse sign-off before execution.",
            "Priority": "High" if acuity == "Critical" else "Medium"
        }

    # 6. Default Approval: Approved for simulation
    return {
        "Patient_ID": patient_id,
        "Acuity_Level": acuity,
        "Source_Unit": src_unit_id,
        "Source_Facility": src_facility,
        "Dest_Unit": dest_unit_id,
        "Dest_Facility": dest_facility,
        "Outcome": "Approved for simulation",
        "Rationale": f"Patient transfer request meets physical bed capacity, staffing, and skill requirements.",
        "Priority": "Low" if acuity == "Low" else "Medium"
    }

def process_batch_transfer_requests(df_patients, df_units, df_nurses, df_staffing):
    """Processes all pending patient transfer requests across units."""
    pending_transfers = df_patients[df_patients["Transfer_Status"].isin(["Pending Transfer", "Admitted"])].copy()
    
    results = []
    unit_map = df_units.set_index("Unit_ID").to_dict("index")
    staffing_map = df_staffing.set_index("Unit_ID").to_dict("index")

    for _, p in pending_transfers.sample(min(100, len(pending_transfers)), random_state=42).iterrows():
        src_unit = p["Unit_ID"]
        src_unit_info = unit_map.get(src_unit, {})
        
        # Pick potential destination unit
        dest_unit_id = df_units[df_units["Unit_Type"] == p["Required_Skill"]]["Unit_ID"].sample(1, random_state=42).iloc[0]
        dest_unit_info = unit_map.get(dest_unit_id, {})
        dest_staffing_info = staffing_map.get(dest_unit_id, {})

        eval_res = evaluate_patient_transfer_request(
            p, src_unit_info, dest_unit_info, dest_staffing_info, df_nurses
        )
        results.append(eval_res)

    return pd.DataFrame(results)

if __name__ == "__main__":
    from src.data_cleaning import run_cleaning_pipeline
    from src.staffing import calculate_unit_staffing
    df_u, df_n, df_p = run_cleaning_pipeline()
    stf = calculate_unit_staffing(df_u, df_n, df_p)
    res_df = process_batch_transfer_requests(df_p, df_u, df_n, stf)
    print("Patient Transfer Outcomes Sample:")
    print(res_df["Outcome"].value_counts())
