import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_synthetic_data(output_dir="data/raw", num_patients=5200, seed=42):
    """
    Generates synthetic dataset for hospital patient transfer workload simulator.
    Intentionally introduces real-world data quality issues (missing values, duplicates, 
    dirty types, inconsistent categories, extreme outliers).
    """
    random.seed(seed)
    np.random.seed(seed)

    os.makedirs(output_dir, exist_ok=True)

    # 1. Units Table Generation
    facilities = [
        {"id": "F01", "name": "St. Jude Memorial Hospital"},
        {"id": "F02", "name": "Metro Health Medical Center"},
        {"id": "F03", "name": "City General Hospital"}
    ]

    unit_types = ["ICU", "Emergency", "Med-Surg", "Pediatrics", "Oncology"]
    
    units = []
    unit_id_counter = 1
    for fac in facilities:
        for u_type in unit_types:
            unit_id = f"U{unit_id_counter:03d}"
            bed_cap = random.randint(25, 60)
            occupied = random.randint(int(bed_cap * 0.5), min(bed_cap, int(bed_cap * 0.95)))
            min_staff = random.randint(6, 12)
            max_staff = min_staff + random.randint(8, 15)
            # Intentionally create some understaffed and overstaffed units
            current_staff = random.randint(max(3, min_staff - 4), max_staff + 2)
            
            units.append({
                "Unit_ID": unit_id,
                "Facility_ID": fac["id"],
                "Facility_Name": fac["name"],
                "Unit_Type": u_type,
                "Bed_Capacity": bed_cap,
                "Occupied_Beds": occupied,
                "Minimum_Staff": min_staff,
                "Maximum_Staff": max_staff,
                "Current_Staff": current_staff
            })
            unit_id_counter += 1

    df_units = pd.DataFrame(units)

    # Introduce minor category inconsistencies in Units
    df_units_raw = df_units.copy()
    # Inconsistent category in 2 rows
    df_units_raw.loc[2, "Unit_Type"] = "icu"
    df_units_raw.loc[7, "Unit_Type"] = "MedSurg"

    df_units_raw.to_csv(os.path.join(output_dir, "units_raw.csv"), index=False)
    print(f"Generated raw units dataset: {len(df_units_raw)} records.")

    # 2. Nurses Table Generation
    skills_map = {
        "ICU": "ICU",
        "Emergency": "Emergency",
        "Med-Surg": "Med-Surg",
        "Pediatrics": "Pediatrics",
        "Oncology": "Oncology"
    }

    shifts = ["Day", "Night", "Evening"]
    experience_levels = ["Junior", "Mid", "Senior", "Specialist"]
    
    nurses = []
    nurse_id_counter = 1
    
    for idx, u in df_units.iterrows():
        # Generate nurses per unit
        n_count = u["Current_Staff"] + random.randint(2, 6) # includes off-shift nurses
        for _ in range(n_count):
            nid = f"N{nurse_id_counter:04d}"
            nurse_skill_level = random.choice([1, 2, 3, 4]) # 1: Basic, 2: Intermediate, 3: Advanced, 4: Expert
            exp = experience_levels[nurse_skill_level - 1]
            shift = random.choice(shifts)
            
            # Specialty matching unit or adjacent
            specialty = u["Unit_Type"] if random.random() > 0.15 else random.choice(unit_types)
            available_hrs = random.choice([8.0, 12.0, 12.0, 0.0]) # 0 if off/sick
            status = "Available" if available_hrs > 0 else "Off Duty"

            nurses.append({
                "Nurse_ID": nid,
                "Unit_ID": u["Unit_ID"],
                "Facility_ID": u["Facility_ID"],
                "Shift": shift,
                "Available_Hours": available_hrs,
                "Nurse_Skill_Level": nurse_skill_level,
                "Specialty": specialty,
                "Experience_Level": exp,
                "Availability_Status": status
            })
            nurse_id_counter += 1

    df_nurses = pd.DataFrame(nurses)

    # Ingest data issues into Nurses raw dataset
    df_nurses_raw = df_nurses.copy()
    
    # Missing values
    missing_indices = np.random.choice(df_nurses_raw.index, size=int(len(df_nurses_raw) * 0.03), replace=False)
    df_nurses_raw.loc[missing_indices, "Specialty"] = np.nan

    # Dirty types (Available_Hours as string with " hrs")
    df_nurses_raw["Available_Hours"] = df_nurses_raw["Available_Hours"].astype(object)
    dirty_hrs_indices = np.random.choice(df_nurses_raw.index, size=int(len(df_nurses_raw) * 0.05), replace=False)
    for i in dirty_hrs_indices:
        df_nurses_raw.loc[i, "Available_Hours"] = f"{df_nurses_raw.loc[i, 'Available_Hours']} hrs"


    # Category inconsistencies
    df_nurses_raw["Shift"] = df_nurses_raw["Shift"].replace({"Day": "Day", "Night": "night_shift", "Evening": "EVENING"})
    
    # Duplicate records (1.5%)
    dups = df_nurses_raw.sample(frac=0.015, random_state=seed)
    df_nurses_raw = pd.concat([df_nurses_raw, dups], ignore_index=True)

    df_nurses_raw.to_csv(os.path.join(output_dir, "nurses_raw.csv"), index=False)
    print(f"Generated raw nurses dataset: {len(df_nurses_raw)} records.")

    # 3. Patient Table Generation (~5,200 records)
    acuity_levels = ["Low", "Medium", "High", "Critical"]
    acuity_weights = {"Low": 1.0, "Medium": 1.25, "High": 1.5, "Critical": 2.0}
    diagnoses = {
        "ICU": ["Acute Respiratory Distress", "Septic Shock", "Multi-organ Dysfunction", "Post-Cardiac Arrest"],
        "Emergency": ["Polytrauma", "Acute Myocardial Infarction", "Stroke", "Severe Abdominal Pain"],
        "Med-Surg": ["Post-Operative Recovery", "Diabetes Complications", "Pneumonia", "Cellulitis"],
        "Pediatrics": ["Pediatric Asthma", "Bronchiolitis", "Dehydration", "Congenital Heart Defect"],
        "Oncology": ["Chemotherapy Monitoring", "Febrile Neutropenia", "Tumor Lysis Syndrome", "Palliative Care"]
    }

    transfer_statuses = ["Admitted", "Pending Transfer", "Transfer Approved", "Discharged"]

    patients = []
    base_date = datetime(2026, 8, 1)

    unit_list = df_units["Unit_ID"].tolist()

    for pid_idx in range(1, num_patients + 1):
        pid = f"P{pid_idx:05d}"
        age = random.randint(1, 92)
        gender = random.choice(["Male", "Female", "Non-Binary"])
        acuity = np.random.choice(acuity_levels, p=[0.35, 0.35, 0.20, 0.10])
        
        assigned_unit_row = df_units.sample(1).iloc[0]
        unit_id = assigned_unit_row["Unit_ID"]
        facility_id = assigned_unit_row["Facility_ID"]
        unit_type = assigned_unit_row["Unit_Type"]

        diag = random.choice(diagnoses[unit_type])
        
        # Base hours depend on acuity
        if acuity == "Low":
            req_hrs = round(random.uniform(1.5, 3.5), 1)
        elif acuity == "Medium":
            req_hrs = round(random.uniform(3.5, 5.5), 1)
        elif acuity == "High":
            req_hrs = round(random.uniform(5.5, 8.5), 1)
        else: # Critical
            req_hrs = round(random.uniform(8.5, 14.0), 1)

        req_skill = unit_type if random.random() > 0.1 else random.choice(unit_types)
        adm_date = base_date + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        status = np.random.choice(transfer_statuses, p=[0.70, 0.15, 0.10, 0.05])

        patients.append({
            "Patient_ID": pid,
            "Age": age,
            "Gender": gender,
            "Acuity_Level": acuity,
            "Diagnosis_Category": diag,
            "Required_Nursing_Hours": req_hrs,
            "Required_Skill": req_skill,
            "Unit_ID": unit_id,
            "Facility_ID": facility_id,
            "Admission_Date": adm_date.strftime("%Y-%m-%d %H:%M:%S"),
            "Transfer_Status": status
        })

    df_patients = pd.DataFrame(patients)

    # Ingest synthetic data quality flaws into Patients table
    df_patients_raw = df_patients.copy()

    # 1. Missing values (~3%)
    missing_acuity_idx = np.random.choice(df_patients_raw.index, size=int(len(df_patients_raw) * 0.02), replace=False)
    df_patients_raw.loc[missing_acuity_idx, "Acuity_Level"] = np.nan

    missing_hrs_idx = np.random.choice(df_patients_raw.index, size=int(len(df_patients_raw) * 0.015), replace=False)
    df_patients_raw.loc[missing_hrs_idx, "Required_Nursing_Hours"] = np.nan

    # 2. Duplicate records (~1.5%)
    dup_patients = df_patients_raw.sample(frac=0.015, random_state=seed)
    df_patients_raw = pd.concat([df_patients_raw, dup_patients], ignore_index=True)

    # 3. Invalid values (negative age, unknown acuity 'Ultra-Critical')
    invalid_age_idx = np.random.choice(df_patients_raw.index, size=5, replace=False)
    df_patients_raw.loc[invalid_age_idx, "Age"] = -5

    invalid_acuity_idx = np.random.choice(df_patients_raw.index, size=5, replace=False)
    df_patients_raw.loc[invalid_acuity_idx, "Acuity_Level"] = "Ultra-Critical"

    # 4. Inconsistent categories
    df_patients_raw["Required_Skill"] = df_patients_raw["Required_Skill"].replace({
        "ICU": "icu",
        "Med-Surg": "MedSurg",
        "Emergency": "EMERGENCY"
    })

    # 5. Outliers (Extreme workload hours e.g. 99.0 hours)
    outlier_idx = np.random.choice(df_patients_raw.index, size=8, replace=False)
    df_patients_raw.loc[outlier_idx, "Required_Nursing_Hours"] = 99.0

    df_patients_raw.to_csv(os.path.join(output_dir, "patients_raw.csv"), index=False)
    print(f"Generated raw patients dataset: {len(df_patients_raw)} records.")

    return df_units_raw, df_nurses_raw, df_patients_raw

if __name__ == "__main__":
    generate_synthetic_data()
