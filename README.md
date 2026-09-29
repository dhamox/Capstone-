# 🏥 Shift Workload-Balancing Simulator for Hospital Patient Transfers

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Pytest-Passing%20(8%2F8)-brightgreen.svg)]()
[![Status](https://img.shields.io/badge/Project-100%25%20Submission--Ready-green.svg)]()

A quantitative decision-support software prototype that simulates patient acuity-weighted nursing workload, calculates unit staffing gaps/surpluses, evaluates patient transfer requests across 7 outcome states, and recommends **safe, skill-matched nurse reassignments** without breaching donor unit minimum staffing bounds or physical bed capacities.

---

## 1. Project Overview
Hospital shift managers routinely lack real-time visibility into cross-unit nursing workload imbalances during patient transfers. Uncoordinated reassignments can cause nurse burnout, high workload variance, or dangerous staffing breaches. This project delivers an end-to-end, multi-page web simulator that balances workload intensity while strictly enforcing **8 hard safety rules**.

---

## 2. Problem Statement
Hospital networks transfer patients across facilities continuously. Current shift management lacks explainable quantitative workload models to determine whether a receiving unit has sufficient staffing and skill mix, or whether a donor unit can safely spare a nurse without compromising patient care.

---

## 3. Core Objectives
1. Model hospital patient acuity and nursing workload dynamically across multiple facilities and specialized units.
2. Evaluate patient transfer requests across 7 explicit outcome states.
3. Enforce strict safe reassignment rules via `validate_safe_reassignment()` to block 100% of unsafe transfers.
4. Simulate 8 operating scenarios under severe stress conditions.
5. Provide interactive, explainable visual decision support for shift managers via a 7-Page Streamlit App.

---

## 4. System Architecture
```
[Synthetic Hospital Dataset (~5,200 Patients)]
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

## 5. Key Technologies
* **Python 3.10+**: Core simulation logic, workload math, and data processing.
* **Pandas & NumPy**: High-performance dataset aggregation, cleaning, and multi-seed experiment execution.
* **Streamlit**: Multi-page interactive web application and human approval gateway.
* **Plotly Express & Graph Objects**: Dynamic dark-themed data visualizations and sensitivity heatmaps.
* **Pytest**: Automated unit testing suite.

---

## 6. Dataset Summary
* **Patients Table**: 5,200 synthetic patient records across 3 facilities and 15 units.
* **Nurses Table**: 271 nurse roster records with specialties, skill levels (1-4), and shift assignments.
* **Units Table**: 15 hospital units with bed capacities, occupied beds, minimum staff, and maximum staff bounds.

---

## 7. Data Dictionary
* `Patient_ID` (String): Unique patient ID (`P00001` - `P05200`).
* `Acuity_Level` (String): Acuity category (`Low`, `Medium`, `High`, `Critical`).
* `Required_Nursing_Hours` (Float): Nursing care hours required per shift (1.5 - 14.0 hrs).
* `Required_Skill` (String): Required unit specialty (`ICU`, `Emergency`, `Med-Surg`, `Pediatrics`, `Oncology`).
* `Nurse_Skill_Level` (Integer): Nurse competency rating (1=Basic to 4=Expert).
* `Bed_Capacity` (Integer): Licensed bed capacity (25 - 60).
* `Minimum_Staff` (Integer): Minimum safe nurse staffing threshold.

---

## 8. Installation Guide

### Prerequisites
Ensure Python 3.10+ is installed on your system.

```bash
git clone https://github.com/dhamox/Capstone-.git
cd Capstone-
pip install -r requirements.txt
```

---

## 9. How to Run

### 1. Data Cleaning Pipeline
```bash
python src/data_cleaning.py
```

### 2. Operating Scenario Simulator
```bash
python src/simulator.py
```

### 3. Automated Pytest Suite
```bash
pytest tests/
```

### 4. Interactive Streamlit Dashboard (7 Pages)
```bash
streamlit run dashboard/app.py
```

---

## 10. Dashboard Pages Structure
1. **Page 1: Executive Overview**: Network KPIs, patient census, staffing gap vs surplus.
2. **Page 2: Unit Workload & Capacity**: Bed occupancy vs capacity, staffing bounds.
3. **Page 3: Operating Scenario Simulator**: Interactive sliders for 8 operating scenarios.
4. **Page 4: Reassignments & Transfer Decision**: Patient transfer outcomes (7 states), explainable recommendation rationale, and interactive Manager Approval buttons.
5. **Page 5: Failure Modes & Safety Sandbox**: 8 failure modes inspection and safety validation logs.
6. **Page 6: Advanced Sensitivity Analysis**: Interactive heatmaps across Acuity, Staffing, and Bed Capacity.
7. **Page 7: Action Tracking & Auto-Escalation**: Action items table with automatic overdue escalation (Level 0 to Level 3).

---

## 11. Operating Scenarios
* **Scenario 1 – Baseline**: Normal acuity and staffing.
* **Scenario 2 – High Acuity (+25%)**: Acuity multiplier = 1.25.
* **Scenario 3 – Staff Shortage (-20%)**: Staff availability = 0.80.
* **Scenario 4 – Combined Stress**: Acuity = 1.25, Staff = 0.80.
* **Scenario 5 – Surge in Transfers**: Patient volume = 1.35 (+35%).
* **Scenario 6 – Specialist Shortage**: -50% ICU/ER specialists available.
* **Scenario 7 – Unit Capacity Constraint**: Bed capacity = 0.75 (-25%).
* **Scenario 8 – Multi-Unit Stress**: Combined multi-unit overload.

---

## 12. Simulation Methodology
Calculates patient workload ($\text{Hours} \times \text{Acuity Weight}$), determines unit required nurses, identifies donor unit surplus above minimum staffing, evaluates candidate reassignments, and validates 8 hard safety rules.

---

## 13. Safety Validation Rules
A nurse is only eligible for safe reassignment if:
1. Nurse status is Available / On Shift.
2. Double-assignment lock is clear.
3. Donor unit active staff remains $\ge \text{Minimum Staff}$.
4. Receiving unit occupied beds $< \text{Bed Capacity}$.
5. Specialty qualification matches receiving unit requirement.
6. Shift window alignment is valid.
7. No new critical staffing gap created.
8. Patient/unit requirements compatible.

---

## 14. Failure Analysis (8 Failure Modes)
Detailed breakdown of 8 failure modes including skill mismatches, donor unit minimum staffing breaches, physical bed capacity bottlenecks, and off-duty nurse selections documented in `docs/failure_analysis.md`.

---

## 15. Experimental Results Summary
| Scenario | Pre Gap | Post Gap | Pre Imbalance ($\sigma$) | Post Imbalance ($\sigma$) | Improvement % | Safe Transfers | Unsafe Blocked |
|---|---|---|---|---|---|---|---|
| **Scenario 1 – Baseline** | 24 | 24 | 7.65 | 7.32 | **4.31%** | 15 | 269 |
| **Scenario 2 – High Acuity (+25%)** | 40 | 40 | 9.56 | 9.15 | **4.29%** | 15 | 37 |
| **Scenario 3 – Staff Shortage (-20%)** | 34 | 34 | 9.28 | 8.81 | **5.06%** | 14 | 30 |
| **Scenario 4 – Combined Stress** | 66 | 66 | 13.64 | 13.58 | **0.44%** | 2 | 6 |
| **Scenario 5 – Transfer Surge (+35%)** | 53 | 53 | 10.29 | 9.98 | **3.01%** | 11 | 24 |
| **Scenario 6 – Specialist Shortage** | 47 | 47 | 11.10 | 10.26 | **7.57%** | 23 | 48 |
| **Scenario 7 – Bed Capacity Constraint**| 24 | 24 | 7.65 | 7.37 | **3.66%** | 13 | 269 |
| **Scenario 8 – Multi-Unit Stress** | 161 | 161 | 13.59 | 13.59 | **0.00%** | 0 | 0 |

---

## 16. Sensitivity Analysis
Multi-axis sensitivity testing demonstrates that safe reassignment capacity degrades under combined severe stress (+40% Acuity & -30% Staff), triggering administrative escalation alerts.

---

## 17. User & Stakeholder Validation
Feedback collected from 4 simulated shift managers and project mentor praised the visual clarity, explainable recommendation rationale, and strict minimum staffing protections.

---

## 18. Main Results
Achieved **4.31% average workload imbalance reduction** in Baseline scenario while blocking **100% of unsafe transfers** (269 unsafe attempts prevented).

---

## 19. Prototype Limitations
1. Software prototype built using synthetic hospital data.
2. Workload weights are prototype parameters, not validated clinical standards.
3. Simulation operates on static shift snapshots rather than continuous real-time telemetry.

---

## 20. Future Work Roadmap
1. Mathematical optimization engine using Integer Linear Programming (ILP) via `SciPy` or `PuLP`.
2. Multi-shift lookahead predictive scheduling (24h/48h).
3. Data interoperability adapter for HL7/FHIR hospital data feeds.
