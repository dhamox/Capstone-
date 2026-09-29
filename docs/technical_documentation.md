# Complete Technical Documentation - Hospital Workload Balancing Simulator

**Project Title**: Shift Workload-Balancing Simulator for Hospital Patient Transfers  
**Milestone**: Final Project Submission (100% Target)  
**Date**: September 2026  

---

## 1. Executive Summary & Problem Statement
Hospital networks routinely transfer patients between facilities and units, but shift managers lack a real-time, explainable view of cross-unit nursing workload and staffing imbalances. Uncoordinated reassignments can lead to nurse burnout or unsafe staffing levels. This software project provides a quantitative **decision-support simulator** that balances workload across units while strictly protecting donor unit safety and enforcing skill-matching rules.

---

## 2. System Architecture & Module Structure

```
[Synthetic Hospital Data (~5,200 Patients)]
                   │
                   ▼
     [Data Cleaning Pipeline (src/data_cleaning.py)]
                   │
                   ▼
     [Clean Data Repository (data/clean/)]
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
[Workload & Staffing]   [Skill Matching Engine]
(src/workload.py &      (src/skill_matching.py)
 src/staffing.py)              │
       │                       ▼
       │            [Transfer Decision Logic]
       │            (src/transfer_logic.py)
       └───────────┬───────────┘
                   ▼
       [Scenario Simulator Engine]
           (src/simulator.py)
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
[7-Page App] [Pytest Suite] [Audit & Escalation]
(dashboard/)   (tests/)     (src/escalation.py)
```

---

## 3. Data Dictionary & Schemas

### A. Patients Dataset (`data/clean/patients.csv`)
* `Patient_ID` (String): Unique patient identifier (`P00001` - `P05200`).
* `Age` (Integer): Patient age (1 - 92 years).
* `Gender` (String): Gender classification (`Male`, `Female`, `Non-Binary`).
* `Acuity_Level` (String): Acuity category (`Low`, `Medium`, `High`, `Critical`).
* `Diagnosis_Category` (String): Primary medical diagnosis.
* `Required_Nursing_Hours` (Float): Required nursing care hours per shift (1.5 - 14.0 hrs).
* `Required_Skill` (String): Required unit specialty (`ICU`, `Emergency`, `Med-Surg`, `Pediatrics`, `Oncology`).
* `Unit_ID` (String): Assigned hospital unit (`U001` - `U015`).
* `Facility_ID` (String): Assigned facility (`F01`, `F02`, `F03`).
* `Transfer_Status` (String): Status (`Admitted`, `Pending Transfer`, `Transfer Approved`, `Discharged`).

### B. Nurses Dataset (`data/clean/nurses.csv`)
* `Nurse_ID` (String): Unique nurse identifier (`N0001` - `N0400`).
* `Unit_ID` (String): Primary assigned unit (`U001` - `U015`).
* `Shift` (String): Shift roster (`Day`, `Evening`, `Night`).
* `Available_Hours` (Float): Hours available in current shift (0.0, 8.0, 12.0).
* `Nurse_Skill_Level` (Integer): Skill competency level (1=Basic to 4=Expert).
* `Specialty` (String): Primary qualification (`ICU`, `Emergency`, `Med-Surg`, `Pediatrics`, `Oncology`).
* `Availability_Status` (String): Status (`Available`, `On Shift`, `Off Duty`, `Reassigned`).

### C. Units Dataset (`data/clean/units.csv`)
* `Unit_ID` (String): Unit identifier (`U001` - `U015`).
* `Facility_ID` (String): Hospital facility ID (`F01`, `F02`, `F03`).
* `Unit_Type` (String): Unit specialty category.
* `Bed_Capacity` (Integer): Total licensed beds (25 - 60).
* `Occupied_Beds` (Integer): Currently occupied beds (15 - 55).
* `Minimum_Staff` (Integer): Minimum safe staffing requirement (6 - 12).
* `Maximum_Staff` (Integer): Maximum nurse physical capacity (14 - 27).
* `Current_Staff` (Integer): Active nurses assigned (4 - 22).

---

## 4. Mathematical Models & Formulas

### Workload Calculation:

$$\text{Patient Workload} = \text{Required Nursing Hours} \times \text{Acuity Weight}$$

**Acuity Weights**: Low = 1.0, Medium = 1.25, High = 1.5, Critical = 2.0.

$$\text{Total Unit Workload} = \sum_{p \in \text{Active Patients}} \text{Patient Workload}_p$$

### Staffing Metrics:

$$\text{Required Nurses} = \left\lceil \frac{\text{Total Unit Workload}}{\text{Shift Hours}} \right\rceil$$

$$\text{Target Nurses} = \max(\text{Minimum Staff}, \text{Required Nurses})$$

$$\text{Staffing Gap} = \max(0, \text{Target Nurses} - \text{Active Nurses})$$

$$\text{Staffing Surplus} = \max(0, \text{Active Nurses} - \text{Target Nurses})$$

$$\text{Workload Per Nurse} = \frac{\text{Total Unit Workload}}{\text{Active Nurses}}$$

### Imbalance Reduction %:

$$\text{Workload Imbalance Reduction \%} = \frac{\sigma_{\text{pre}} - \sigma_{\text{post}}}{\sigma_{\text{pre}}} \times 100$$

where $\sigma$ is the standard deviation of workload per nurse across units.

---

## 5. Safe Skill-Matching Rules & `validate_safe_reassignment()`
Validates 8 core safety criteria:
1. Nurse availability status.
2. Double-assignment prevention.
3. Donor unit minimum staffing protection (`Active - 1 >= Minimum_Staff`).
4. Receiving unit physical bed capacity (`Occupied < Capacity`).
5. Specialty and skill level compatibility.
6. Shift window alignment.
7. No creation of new critical gaps.
8. Patient/unit requirement compatibility.

---

## 6. 8 Operating Scenarios Summary
1. **Scenario 1 – Baseline**: Normal acuity (1.0), normal staff (1.0).
2. **Scenario 2 – High Acuity (+25%)**: Acuity multiplier = 1.25.
3. **Scenario 3 – Staff Shortage (-20%)**: Staff availability = 0.80.
4. **Scenario 4 – Combined Stress**: Acuity = 1.25, Staff = 0.80.
5. **Scenario 5 – Surge in Transfers**: Patient volume = 1.35 (+35%).
6. **Scenario 6 – Specialist Shortage**: -50% ICU/ER specialists available.
7. **Scenario 7 – Unit Capacity Constraint**: Bed capacity = 0.75 (-25%).
8. **Scenario 8 – Multi-Unit Stress**: Combined multi-unit overload.

---

## 7. Multi-Seed Reproducible Experiment Results
Averaged across 10 random dataset seeds (`seed=1` to `10`):
* **Baseline Staffing Gap (Pre)**: 24.3 (Std: 1.2)
* **Baseline Staffing Gap (Post)**: 24.3 (Std: 1.2)
* **Workload Imbalance Std (Pre)**: 7.62 (Std: 0.45)
* **Workload Imbalance Std (Post)**: 7.30 (Std: 0.42)
* **Imbalance Reduction %**: **4.31%** (Std: 0.25%)
* **Safe Reassignment Capacity**: 15.1 (Std: 0.8)
* **Unsafe Attempts Blocked**: 268.4 (Std: 5.2)

---

## 8. Limitations & Future Roadmap
* **Synthetic Data**: Prototype built using synthetic hospital data.
* **Heuristic Matching**: Rule-based matching engine; future roadmap includes Integer Linear Programming (ILP) optimization via `SciPy` or `PuLP`.
* **Multi-Shift Forecasting**: Currently single-shift snapshot; future work includes 24h/48h predictive scheduling.
