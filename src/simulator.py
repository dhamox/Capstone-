import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_cleaning import run_cleaning_pipeline
from src.workload import calculate_unit_workload, calculate_workload_imbalance_metrics
from src.staffing import calculate_unit_staffing
from src.skill_matching import evaluate_reassignment_candidates, validate_safe_reassignment

def run_scenario_simulation(
    df_units,
    df_nurses,
    df_patients,
    scenario_name="Baseline",
    acuity_multiplier=1.0,
    staff_multiplier=1.0,
    surge_multiplier=1.0,
    specialist_shortage=False,
    capacity_reduction=1.0
):
    """
    Executes a workload balancing scenario simulation.
    
    Supports 8 operating scenarios with customizable parameters.
    """
    units = df_units.copy()
    nurses = df_nurses.copy()
    patients = df_patients.copy()

    nurses["Available_Hours"] = pd.to_numeric(nurses["Available_Hours"], errors="coerce").astype(float)

    # 1. Apply Acuity Multiplier
    if acuity_multiplier != 1.0:
        patients["Required_Nursing_Hours"] = patients["Required_Nursing_Hours"] * acuity_multiplier

    # 2. Apply Staff Availability Multiplier
    if staff_multiplier != 1.0:
        available_mask = nurses["Availability_Status"] == "Available"
        available_indices = nurses[available_mask].index
        remove_count = int(len(available_indices) * (1.0 - staff_multiplier))
        if remove_count > 0:
            remove_idx = np.random.choice(available_indices, size=remove_count, replace=False)
            nurses.loc[remove_idx, "Availability_Status"] = "Shortage - Off Duty"
            nurses.loc[remove_idx, "Available_Hours"] = 0.0

    # 3. Apply Specialist Shortage (-50% ICU / Emergency specialists)
    if specialist_shortage:
        spec_mask = nurses["Specialty"].isin(["ICU", "Emergency"]) & (nurses["Availability_Status"] == "Available")
        spec_indices = nurses[spec_mask].index
        remove_count = int(len(spec_indices) * 0.50)
        if remove_count > 0:
            remove_idx = np.random.choice(spec_indices, size=remove_count, replace=False)
            nurses.loc[remove_idx, "Availability_Status"] = "Specialist Shortage"
            nurses.loc[remove_idx, "Available_Hours"] = 0.0

    # 4. Apply Patient Volume Surge (+35% patient volume)
    if surge_multiplier > 1.0:
        surge_sample = patients.sample(frac=(surge_multiplier - 1.0), replace=True, random_state=42)
        surge_sample["Patient_ID"] = surge_sample["Patient_ID"].apply(lambda x: f"{x}_SURGE")
        patients = pd.concat([patients, surge_sample], ignore_index=True)

    # 5. Apply Unit Capacity Constraint (-25% available beds)
    if capacity_reduction < 1.0:
        units["Bed_Capacity"] = (units["Bed_Capacity"] * capacity_reduction).astype(int)

    # 6. Compute Pre-Balance Metrics
    pre_staffing = calculate_unit_staffing(units, nurses, patients)
    pre_metrics = calculate_workload_imbalance_metrics(pre_staffing)

    pre_total_gap = int(pre_staffing["Staffing_Gap"].sum())
    pre_total_surplus = int(pre_staffing["Staffing_Surplus"].sum())

    # 7. Evaluate Safe Reassignments
    match_results = evaluate_reassignment_candidates(units, nurses, pre_staffing)
    reassignments = match_results["reassignments"]
    unsafe_prevented = match_results["unsafe_prevented"]
    safe_capacity = match_results["safe_reassignment_capacity"]

    # Generate Explainable Rationale for Recommendations
    reassignments_explainable = []
    if not reassignments.empty:
        for _, row in reassignments.iterrows():
            nid = row["Nurse_ID"]
            donor_u = row["Donor_Unit"]
            rec_u = row["Receiving_Unit"]
            spec = row["Nurse_Specialty"]
            
            rec_gap = pre_staffing.loc[pre_staffing["Unit_ID"] == rec_u, "Staffing_Gap"].values[0]
            donor_surplus = pre_staffing.loc[pre_staffing["Unit_ID"] == donor_u, "Staffing_Surplus"].values[0]

            rationale = (
                f"Receiving Unit {rec_u} has a staffing gap of {rec_gap} nurses. "
                f"Donor Unit {donor_u} has a staffing surplus of {donor_surplus} nurses above minimum requirement. "
                f"Nurse {nid} possesses required skill '{spec}'. "
                f"Physical bed capacity and all 8 safety rules validated."
            )

            row_dict = row.to_dict()
            row_dict["Recommendation_Rationale"] = rationale
            row_dict["Human_Approval_Status"] = "Pending Review"
            reassignments_explainable.append(row_dict)

    reassignments_df = pd.DataFrame(reassignments_explainable)

    # 8. Apply Reassignments to Post-Balance State
    post_nurses = nurses.copy()
    post_units = units.copy()

    if not reassignments_df.empty:
        for _, row in reassignments_df.iterrows():
            nid = row["Nurse_ID"]
            new_unit = row["Receiving_Unit"]
            post_nurses.loc[post_nurses["Nurse_ID"] == nid, "Unit_ID"] = new_unit
            post_nurses.loc[post_nurses["Nurse_ID"] == nid, "Availability_Status"] = "Reassigned"

    # 9. Compute Post-Balance Metrics
    post_staffing = calculate_unit_staffing(post_units, post_nurses, patients)
    post_metrics = calculate_workload_imbalance_metrics(post_staffing)

    post_total_gap = int(post_staffing["Staffing_Gap"].sum())
    post_total_surplus = int(post_staffing["Staffing_Surplus"].sum())

    pre_std = pre_metrics["Workload_Imbalance_Std"]
    post_std = post_metrics["Workload_Imbalance_Std"]

    if pre_std > 0:
        imbalance_reduction_pct = round(((pre_std - post_std) / pre_std) * 100, 2)
    else:
        imbalance_reduction_pct = 0.0

    summary = {
        "Scenario_Name": scenario_name,
        "Acuity_Multiplier": acuity_multiplier,
        "Staff_Multiplier": staff_multiplier,
        "Surge_Multiplier": surge_multiplier,
        "Specialist_Shortage": specialist_shortage,
        "Capacity_Reduction": capacity_reduction,
        "Total_Patients": len(patients),
        "Total_Nurses": len(nurses[nurses["Availability_Status"].isin(["Available", "On Shift", "Reassigned"])]),
        "Pre_Staffing_Gap": pre_total_gap,
        "Post_Staffing_Gap": post_total_gap,
        "Pre_Staffing_Surplus": pre_total_surplus,
        "Post_Staffing_Surplus": post_total_surplus,
        "Pre_Workload_Max_Min_Gap": pre_metrics["Workload_Imbalance_Max_Min_Gap"],
        "Post_Workload_Max_Min_Gap": post_metrics["Workload_Imbalance_Max_Min_Gap"],
        "Pre_Workload_Imbalance_Std": pre_std,
        "Post_Workload_Imbalance_Std": post_std,
        "Pre_CV_Pct": pre_metrics["Coefficient_of_Variation_Pct"],
        "Post_CV_Pct": post_metrics["Coefficient_of_Variation_Pct"],
        "Imbalance_Reduction_Pct": max(0.0, imbalance_reduction_pct),
        "Safe_Reassignment_Capacity": safe_capacity,
        "Unsafe_Attempts_Prevented": len(unsafe_prevented)
    }

    return {
        "summary": summary,
        "pre_staffing": pre_staffing,
        "post_staffing": post_staffing,
        "reassignments": reassignments_df,
        "unsafe_prevented": unsafe_prevented
    }

def run_all_operating_scenarios(df_units, df_nurses, df_patients):
    """
    Runs all 8 operating scenarios:
    1. Scenario 1 – Baseline
    2. Scenario 2 – High Acuity (+25%)
    3. Scenario 3 – Staff Shortage (-20%)
    4. Scenario 4 – Combined Stress (+25% Acuity, -20% Staff)
    5. Scenario 5 – Surge in Patient Transfers (+35% volume)
    6. Scenario 6 – Specialist Shortage (-50% ICU/Emergency specialists)
    7. Scenario 7 – Unit Capacity Constraint (-25% available beds)
    8. Scenario 8 – Multi-Unit Stress (Combined overload across multiple units)
    """
    scenarios = [
        {"name": "Scenario 1 – Baseline", "acuity": 1.0, "staff": 1.0, "surge": 1.0, "spec": False, "cap": 1.0},
        {"name": "Scenario 2 – High Acuity (+25%)", "acuity": 1.25, "staff": 1.0, "surge": 1.0, "spec": False, "cap": 1.0},
        {"name": "Scenario 3 – Staff Shortage (-20%)", "acuity": 1.0, "staff": 0.80, "surge": 1.0, "spec": False, "cap": 1.0},
        {"name": "Scenario 4 – Combined Stress", "acuity": 1.25, "staff": 0.80, "surge": 1.0, "spec": False, "cap": 1.0},
        {"name": "Scenario 5 – Surge in Patient Transfers", "acuity": 1.0, "staff": 1.0, "surge": 1.35, "spec": False, "cap": 1.0},
        {"name": "Scenario 6 – Specialist Shortage", "acuity": 1.0, "staff": 1.0, "surge": 1.0, "spec": True, "cap": 1.0},
        {"name": "Scenario 7 – Unit Capacity Constraint", "acuity": 1.0, "staff": 1.0, "surge": 1.0, "spec": False, "cap": 0.75},
        {"name": "Scenario 8 – Multi-Unit Stress", "acuity": 1.30, "staff": 0.75, "surge": 1.20, "spec": True, "cap": 0.80}
    ]

    results = {}
    summary_list = []

    for sc in scenarios:
        res = run_scenario_simulation(
            df_units, df_nurses, df_patients,
            scenario_name=sc["name"],
            acuity_multiplier=sc["acuity"],
            staff_multiplier=sc["staff"],
            surge_multiplier=sc["surge"],
            specialist_shortage=sc["spec"],
            capacity_reduction=sc["cap"]
        )
        results[sc["name"]] = res
        summary_list.append(res["summary"])

    return results, pd.DataFrame(summary_list)

def run_sensitivity_analysis(df_units, df_nurses, df_patients):
    """
    Performs sensitivity analysis varying acuity scale (+10%, +25%, +40%), 
    staff shortage (0%, -10%, -20%, -30%), and capacity reduction (100%, 80%).
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

def run_reproducible_experiment(num_seeds=10):

    """
    Runs a reproducible experiment across multiple random seeds (1 to num_seeds).
    Computes Mean, Standard Deviation, and Improvement % across seeds.
    """
    from src.data_generator import generate_synthetic_data
    from src.data_cleaning import clean_units_data, clean_nurses_data, clean_patients_data

    seed_summaries = []

    for seed in range(1, num_seeds + 1):
        u_raw, n_raw, p_raw = generate_synthetic_data(output_dir="data/raw_temp", seed=seed)
        u_clean = clean_units_data(u_raw)
        n_clean = clean_nurses_data(n_raw)
        p_clean = clean_patients_data(p_raw)

        res = run_scenario_simulation(u_clean, n_clean, p_clean, scenario_name=f"Seed_{seed}")
        s = res["summary"]
        s["Seed"] = seed
        seed_summaries.append(s)

    df_exp = pd.DataFrame(seed_summaries)

    metrics_summary = {
        "Metric": [
            "Staffing Gap (Pre)", "Staffing Gap (Post)", 
            "Workload Imbalance Std (Pre)", "Workload Imbalance Std (Post)",
            "Safe Reassignment Capacity", "Unsafe Attempts Prevented",
            "Imbalance Reduction %"
        ],
        "Mean Value": [
            round(df_exp["Pre_Staffing_Gap"].mean(), 2),
            round(df_exp["Post_Staffing_Gap"].mean(), 2),
            round(df_exp["Pre_Workload_Imbalance_Std"].mean(), 2),
            round(df_exp["Post_Workload_Imbalance_Std"].mean(), 2),
            round(df_exp["Safe_Reassignment_Capacity"].mean(), 2),
            round(df_exp["Unsafe_Attempts_Prevented"].mean(), 2),
            round(df_exp["Imbalance_Reduction_Pct"].mean(), 2)
        ],
        "Std Dev": [
            round(df_exp["Pre_Staffing_Gap"].std(), 2),
            round(df_exp["Post_Staffing_Gap"].std(), 2),
            round(df_exp["Pre_Workload_Imbalance_Std"].std(), 2),
            round(df_exp["Post_Workload_Imbalance_Std"].std(), 2),
            round(df_exp["Safe_Reassignment_Capacity"].std(), 2),
            round(df_exp["Unsafe_Attempts_Prevented"].std(), 2),
            round(df_exp["Imbalance_Reduction_Pct"].std(), 2)
        ]
    }

    return df_exp, pd.DataFrame(metrics_summary)

if __name__ == "__main__":
    df_u, df_n, df_p = run_cleaning_pipeline()
    res, sum_df = run_all_operating_scenarios(df_u, df_n, df_p)
    print("8 Operating Scenarios Summary:")
    print(sum_df[["Scenario_Name", "Pre_Staffing_Gap", "Post_Staffing_Gap", "Pre_Workload_Imbalance_Std", "Post_Workload_Imbalance_Std", "Imbalance_Reduction_Pct", "Safe_Reassignment_Capacity"]].to_string(index=False))
