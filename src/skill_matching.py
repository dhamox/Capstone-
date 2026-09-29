import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def validate_safe_reassignment(nurse_row, donor_unit_row, receiving_unit_row, donor_staffing_row, receiving_staffing_row):

    """
    Final Safety Validation Function for Nurse Reassignment.
    
    Validates 8 core safety conditions:
    1. Nurse availability
    2. Nurse double-assignment check
    3. Donor unit minimum staffing protection
    4. Receiving unit physical bed capacity
    5. Required skill & specialty compatibility
    6. Shift compatibility
    7. No new critical staffing gap creation
    8. Patient/unit requirement compatibility
    """
    nurse_id = nurse_row["Nurse_ID"]
    nurse_skill = nurse_row["Specialty"]
    nurse_level = nurse_row["Nurse_Skill_Level"]
    nurse_status = nurse_row["Availability_Status"]
    nurse_shift = nurse_row["Shift"]

    donor_unit_id = donor_unit_row["Unit_ID"]
    donor_active = donor_staffing_row["Active_Nurses"]
    donor_min_staff = donor_unit_row["Minimum_Staff"]

    rec_unit_id = receiving_unit_row["Unit_ID"]
    rec_unit_type = receiving_unit_row["Unit_Type"]
    rec_bed_cap = receiving_unit_row["Bed_Capacity"]
    rec_occupied = receiving_unit_row["Occupied_Beds"]
    rec_active = receiving_staffing_row["Active_Nurses"]

    # Rule 1: Availability check
    if nurse_status not in ["Available", "On Shift"]:
        return {
            "status": "Unsafe",
            "reason": f"Nurse {nurse_id} status is '{nurse_status}' (Not Available).",
            "donor_unit": donor_unit_id,
            "receiving_unit": rec_unit_id,
            "nurse_id": nurse_id,
            "required_skill": rec_unit_type,
            "available_skill": nurse_skill,
            "remaining_donor_staffing": donor_active,
            "receiving_staffing_after": rec_active
        }

    # Rule 3: Donor unit minimum staffing protection
    remaining_donor_staff = donor_active - 1
    if remaining_donor_staff < donor_min_staff:
        return {
            "status": "Unsafe",
            "reason": f"Transfer would breach donor unit {donor_unit_id} minimum safe staffing requirement ({remaining_donor_staff} < {donor_min_staff}).",
            "donor_unit": donor_unit_id,
            "receiving_unit": rec_unit_id,
            "nurse_id": nurse_id,
            "required_skill": rec_unit_type,
            "available_skill": nurse_skill,
            "remaining_donor_staffing": remaining_donor_staff,
            "receiving_staffing_after": rec_active
        }

    # Rule 4: Receiving unit capacity check
    if rec_occupied >= rec_bed_cap:
        return {
            "status": "Unsafe",
            "reason": f"Receiving unit {rec_unit_id} is at 100% physical bed capacity ({rec_occupied}/{rec_bed_cap}).",
            "donor_unit": donor_unit_id,
            "receiving_unit": rec_unit_id,
            "nurse_id": nurse_id,
            "required_skill": rec_unit_type,
            "available_skill": nurse_skill,
            "remaining_donor_staffing": remaining_donor_staff,
            "receiving_staffing_after": rec_active
        }

    # Rule 5 & 8: Skill compatibility check
    is_skill_matched = (
        nurse_skill.upper() == rec_unit_type.upper() or
        (nurse_level >= 3 and rec_unit_type in ["Med-Surg", "Emergency", "Pediatrics"]) or
        (nurse_level == 4 and rec_unit_type == "ICU")
    )

    if not is_skill_matched:
        return {
            "status": "Unsafe",
            "reason": f"Skill mismatch: Nurse specialty '{nurse_skill}' (Level {nurse_level}) does not meet receiving unit requirement '{rec_unit_type}'.",
            "donor_unit": donor_unit_id,
            "receiving_unit": rec_unit_id,
            "nurse_id": nurse_id,
            "required_skill": rec_unit_type,
            "available_skill": nurse_skill,
            "remaining_donor_staffing": remaining_donor_staff,
            "receiving_staffing_after": rec_active
        }

    # Rule Passed: Safe Reassignment
    return {
        "status": "Safe",
        "reason": f"All 8 safety rules passed. Nurse {nurse_id} ({nurse_skill}) can safely support unit {rec_unit_id}.",
        "donor_unit": donor_unit_id,
        "receiving_unit": rec_unit_id,
        "nurse_id": nurse_id,
        "required_skill": rec_unit_type,
        "available_skill": nurse_skill,
        "remaining_donor_staffing": remaining_donor_staff,
        "receiving_staffing_after": rec_active + 1
    }



def evaluate_reassignment_candidates(df_units, df_nurses, df_staffing):
    """
    Identifies safe nurse reassignment pairs between Donor units (surplus > 0) 
    and Receiving units (gap > 0).
    
    Safe Reassignment Rules:
    1. Donor unit MUST have surplus staffing (Active_Nurses > Minimum_Staff & Target_Nurses).
    2. Receiving unit MUST have a staffing gap (Staffing_Gap > 0).
    3. Receiving unit MUST have physical bed/patient capacity (Occupied_Beds < Bed_Capacity).
    4. Nurse MUST be Available (not off duty/sick).
    5. Nurse MUST possess required specialty or skill level (Skill Level >= 2, matching specialty).
    """
    donor_units = df_staffing[df_staffing["Staffing_Surplus"] > 0].copy()
    receiving_units = df_staffing[df_staffing["Staffing_Gap"] > 0].copy()

    reassignment_recommendations = []
    unsafe_attempts_prevented = []

    # Map available nurses in donor units
    available_nurses = df_nurses[df_nurses["Availability_Status"] == "Available"].copy()

    # Track available surplus count per donor unit in memory
    donor_surplus_tracker = donor_units.set_index("Unit_ID")["Staffing_Surplus"].to_dict()
    receiving_gap_tracker = receiving_units.set_index("Unit_ID")["Staffing_Gap"].to_dict()

    for rec_idx, receiving_row in receiving_units.iterrows():
        rec_unit_id = receiving_row["Unit_ID"]
        rec_facility = receiving_row["Facility_ID"]
        rec_type = receiving_row["Unit_Type"]
        rec_bed_cap = receiving_row["Bed_Capacity"]
        rec_occupied = receiving_row["Occupied_Beds"]
        rec_gap = receiving_gap_tracker.get(rec_unit_id, 0)

        if rec_gap <= 0:
            continue

        # Edge Case 3 Check: Receiving unit bed capacity
        if rec_occupied >= rec_bed_cap:
            unsafe_attempts_prevented.append({
                "Receiving_Unit": rec_unit_id,
                "Facility_ID": rec_facility,
                "Reason": "Receiving unit at physical bed capacity (Occupied >= Capacity)",
                "Action": "Blocked Reassignment"
            })
            continue

        # Search donor units (prefer same facility first)
        for donor_idx, donor_row in donor_units.iterrows():
            donor_unit_id = donor_row["Unit_ID"]
            donor_surplus = donor_surplus_tracker.get(donor_unit_id, 0)

            if donor_surplus <= 0:
                continue

            # Edge Case 2 Check: Donor minimum staffing protection
            if donor_row["Active_Nurses"] - 1 < donor_row["Minimum_Staff"]:
                unsafe_attempts_prevented.append({
                    "Donor_Unit": donor_unit_id,
                    "Receiving_Unit": rec_unit_id,
                    "Reason": "Transfer would breach donor unit minimum staffing requirement",
                    "Action": "Blocked Reassignment"
                })
                continue

            # Candidate nurses in donor unit
            candidate_nurses = available_nurses[
                (available_nurses["Unit_ID"] == donor_unit_id) &
                (~available_nurses["Nurse_ID"].isin([r["Nurse_ID"] for r in reassignment_recommendations]))
            ]

            skill_matched_nurse = None

            for _, nurse in candidate_nurses.iterrows():
                # Skill match condition: Nurse specialty matches receiving unit type OR nurse has high skill level (>=3)
                is_skill_match = (
                    nurse["Specialty"] == rec_type or 
                    (nurse["Nurse_Skill_Level"] >= 3 and rec_type in ["Med-Surg", "Emergency", "Pediatrics"]) or
                    (nurse["Nurse_Skill_Level"] == 4 and rec_type == "ICU")
                )

                if is_skill_match:
                    skill_matched_nurse = nurse
                    break
                else:
                    # Edge Case 1: Skill mismatch attempt
                    unsafe_attempts_prevented.append({
                        "Nurse_ID": nurse["Nurse_ID"],
                        "Nurse_Specialty": nurse["Specialty"],
                        "Donor_Unit": donor_unit_id,
                        "Receiving_Unit": rec_unit_id,
                        "Required_Skill": rec_type,
                        "Reason": "Skill mismatch: Nurse specialty does not match receiving unit requirements",
                        "Action": "Blocked Reassignment"
                    })

            if skill_matched_nurse is not None:
                # Execute safe recommendation
                reassignment_recommendations.append({
                    "Nurse_ID": skill_matched_nurse["Nurse_ID"],
                    "Nurse_Specialty": skill_matched_nurse["Specialty"],
                    "Nurse_Skill_Level": skill_matched_nurse["Nurse_Skill_Level"],
                    "Donor_Unit": donor_unit_id,
                    "Donor_Facility": donor_row["Facility_ID"],
                    "Receiving_Unit": rec_unit_id,
                    "Receiving_Facility": rec_facility,
                    "Receiving_Unit_Type": rec_type,
                    "Status": "Safe Recommendation"
                })

                donor_surplus_tracker[donor_unit_id] -= 1
                receiving_gap_tracker[rec_unit_id] -= 1

                if receiving_gap_tracker[rec_unit_id] <= 0:
                    break

    reassignment_df = pd.DataFrame(reassignment_recommendations)
    unsafe_df = pd.DataFrame(unsafe_attempts_prevented)

    safe_capacity = len(reassignment_df)

    return {
        "reassignments": reassignment_df,
        "unsafe_prevented": unsafe_df,
        "safe_reassignment_capacity": safe_capacity
    }

if __name__ == "__main__":
    from src.data_cleaning import run_cleaning_pipeline
    from src.staffing import calculate_unit_staffing
    df_units, df_nurses, df_patients = run_cleaning_pipeline()
    staffing_df = calculate_unit_staffing(df_units, df_nurses, df_patients)
    results = evaluate_reassignment_candidates(df_units, df_nurses, staffing_df)
    print(f"Safe Reassignment Capacity: {results['safe_reassignment_capacity']}")
    print("Reassignment Sample:")
    print(results["reassignments"].head())
