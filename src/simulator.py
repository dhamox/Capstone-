import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_cleaning import run_cleaning_pipeline

from src.workload import DEFAULT_ACUITY_WEIGHTS
from src.staffing import calculate_unit_staffing
from src.skill_matching import evaluate_reassignment_candidates

def run_scenario_simulation(df_units, df_nurses, df_patients, scenario_name="Baseline", acuity_multiplier=1.0, staff_multiplier=1.0):
    """
    Executes a workload balancing scenario simulation.
    
    Parameters:
    - scenario_name: Name of operating scenario
    - acuity_multiplier: Factor to scale patient acuity/required hours (e.g. 1.25 for +25%)
    - staff_multiplier: Factor to scale nurse availability (e.g. 0.80 for 20% shortage)
    """
    # Copy data to avoid mutation
    units = df_units.copy()
    nurses = df_nurses.copy()
    patients = df_patients.copy()

    nurses["Available_Hours"] = pd.to_numeric(nurses["Available_Hours"], errors="coerce").astype(float)


    # 1. Apply scenario modifications
    if acuity_multiplier != 1.0:
        patients["Required_Nursing_Hours"] = patients["Required_Nursing_Hours"] * acuity_multiplier

    if staff_multiplier != 1.0:
        # Randomly mark (1 - staff_multiplier) % of available nurses as Off Duty / Sick
        available_mask = nurses["Availability_Status"] == "Available"
        available_indices = nurses[available_mask].index
        remove_count = int(len(available_indices) * (1.0 - staff_multiplier))
        if remove_count > 0:
            remove_idx = np.random.choice(available_indices, size=remove_count, replace=False)
            nurses.loc[remove_idx, "Availability_Status"] = "Shortage - Off Duty"
            nurses.loc[remove_idx, "Available_Hours"] = 0.0

    # 2. Compute pre-balance staffing and workload
    pre_staffing = calculate_unit_staffing(units, nurses, patients)

    pre_total_gap = int(pre_staffing["Staffing_Gap"].sum())
    pre_total_surplus = int(pre_staffing["Staffing_Surplus"].sum())
    
    # Measure Workload Imbalance (Standard Deviation of Workload Per Nurse across units)
    pre_imbalance = float(pre_staffing["Workload_Per_Nurse"].std())

    # 3. Evaluate Safe Reassignments
    match_results = evaluate_reassignment_candidates(units, nurses, pre_staffing)
    reassignments = match_results["reassignments"]
    unsafe_prevented = match_results["unsafe_prevented"]
    safe_capacity = match_results["safe_reassignment_capacity"]

    # 4. Apply reassignments to post-balance state
    post_nurses = nurses.copy()
    post_units = units.copy()

    if not reassignments.empty:
        for _, row in reassignments.iterrows():
            nid = row["Nurse_ID"]
            new_unit = row["Receiving_Unit"]
            post_nurses.loc[post_nurses["Nurse_ID"] == nid, "Unit_ID"] = new_unit
            post_nurses.loc[post_nurses["Nurse_ID"] == nid, "Availability_Status"] = "Reassigned"

    # 5. Compute post-balance staffing and workload
    post_staffing = calculate_unit_staffing(post_units, post_nurses, patients)

    post_total_gap = int(post_staffing["Staffing_Gap"].sum())
    post_total_surplus = int(post_staffing["Staffing_Surplus"].sum())
    post_imbalance = float(post_staffing["Workload_Per_Nurse"].std())

    # 6. Calculate Imbalance Reduction %
    if pre_imbalance > 0:
        imbalance_reduction_pct = round(((pre_imbalance - post_imbalance) / pre_imbalance) * 100, 2)
    else:
        imbalance_reduction_pct = 0.0

    summary = {
        "Scenario_Name": scenario_name,
        "Acuity_Multiplier": acuity_multiplier,
        "Staff_Multiplier": staff_multiplier,
        "Total_Patients": len(patients),
        "Total_Nurses": len(nurses[nurses["Availability_Status"].isin(["Available", "On Shift", "Reassigned"])]),
        "Pre_Staffing_Gap": pre_total_gap,
        "Post_Staffing_Gap": post_total_gap,
        "Pre_Staffing_Surplus": pre_total_surplus,
        "Post_Staffing_Surplus": post_total_surplus,
        "Pre_Workload_Imbalance_Std": round(pre_imbalance, 2),
        "Post_Workload_Imbalance_Std": round(post_imbalance, 2),
        "Imbalance_Reduction_Pct": max(0.0, imbalance_reduction_pct),
        "Safe_Reassignment_Capacity": safe_capacity,
        "Unsafe_Attempts_Prevented": len(unsafe_prevented)
    }

    return {
        "summary": summary,
        "pre_staffing": pre_staffing,
        "post_staffing": post_staffing,
        "reassignments": reassignments,
        "unsafe_prevented": unsafe_prevented
    }

def run_all_operating_scenarios(df_units, df_nurses, df_patients):
    """
    Runs the 4 standard operating scenarios:
    1. Baseline
    2. High Acuity (+25%)
    3. Staff Shortage (-20%)
    4. Combined Stress (+25% Acuity & -20% Staff)
    """
    scenarios = [
        {"name": "Scenario 1 – Baseline", "acuity": 1.0, "staff": 1.0},
        {"name": "Scenario 2 – High Acuity (+25%)", "acuity": 1.25, "staff": 1.0},
        {"name": "Scenario 3 – Staff Shortage (-20%)", "acuity": 1.0, "staff": 0.80},
        {"name": "Scenario 4 – Combined Stress", "acuity": 1.25, "staff": 0.80}
    ]

    results = {}
    summary_list = []

    for sc in scenarios:
        res = run_scenario_simulation(
            df_units, df_nurses, df_patients,
            scenario_name=sc["name"],
            acuity_multiplier=sc["acuity"],
            staff_multiplier=sc["staff"]
        )
        results[sc["name"]] = res
        summary_list.append(res["summary"])

    summary_df = pd.DataFrame(summary_list)
    return results, summary_df

def run_sensitivity_analysis(df_units, df_nurses, df_patients):
    """
    Performs sensitivity analysis varying acuity increase (10%, 25%, 40%) 
    and staff shortage (10%, 20%, 30%).
    """
    acuity_levels = [1.10, 1.25, 1.40]
    staff_levels = [0.90, 0.80, 0.70]

    matrix_rows = []

    for ac in acuity_levels:
        for st in staff_levels:
            ac_label = f"+{int((ac - 1.0)*100)}% Acuity"
            st_label = f"-{int((1.0 - st)*100)}% Staff"
            
            res = run_scenario_simulation(
                df_units, df_nurses, df_patients,
                scenario_name=f"{ac_label} / {st_label}",
                acuity_multiplier=ac,
                staff_multiplier=st
            )
            s = res["summary"]
            matrix_rows.append({
                "Acuity_Increase": ac_label,
                "Staff_Shortage": st_label,
                "Pre_Staffing_Gap": s["Pre_Staffing_Gap"],
                "Post_Staffing_Gap": s["Post_Staffing_Gap"],
                "Safe_Capacity": s["Safe_Reassignment_Capacity"],
                "Imbalance_Reduction_Pct": s["Imbalance_Reduction_Pct"],
                "Unsafe_Prevented": s["Unsafe_Attempts_Prevented"]
            })

    return pd.DataFrame(matrix_rows)

if __name__ == "__main__":
    df_units, df_nurses, df_patients = run_cleaning_pipeline()
    results, summary_df = run_all_operating_scenarios(df_units, df_nurses, df_patients)
    print("Scenario Comparison Matrix:")
    print(summary_df.to_string(index=False))
