# Technical Documentation - Shift Workload-Balancing Simulator (35% Prototype Target)

**Project Title**: Shift Workload-Balancing Simulator for Hospital Patient Transfers  
**Target Milestone**: Review 1 (~35% Prototype Target)  
**Date**: September 2026  

---

## 1. Problem Statement
Hospital groups routinely transfer patients between facilities and units, but shift managers lack real-time visibility into cross-unit workload and staffing imbalances. Current reassignment methods often result in uncoordinated transfers or unsafe nurse reassignment without proper skill matching. This simulator provides a decision-support framework to balance nursing workload while strictly enforcing safe skill-matching rules.

---

## 2. System Objectives
1. Model hospital patient acuity and nursing workload dynamically across multiple facilities and specialized units.
2. Identify real-time staffing gaps and donor unit staffing surpluses.
3. Enforce strict safe reassignment rules (skill compatibility, donor minimum staffing protection, receiving unit bed capacity).
4. Simulate operating scenarios (Baseline, High Acuity, Staff Shortages, Combined Stress).
5. Provide interactive visual decision support for shift managers.

---

## 3. System Architecture
The prototype follows a modular Python data processing, simulation engine, and web presentation layer:

```
[Raw Synthetic Data (CSV)] 
       │
       ▼
[Data Cleaning Pipeline (src/data_cleaning.py)]
       │
       ▼
[Clean Data Repository (data/clean/)]
       │
       ├───────────────────────────┐
       ▼                           ▼
[Workload & Staffing Engine]  [Skill-Matching Engine]
(src/workload.py & staffing.py) (src/skill_matching.py)
       │                           │
       └─────────────┬─────────────┘
                     ▼
          [Scenario Simulator Engine]
              (src/simulator.py)
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
 [Interactive Dashboard] [Automated Pytest Suite]
   (dashboard/app.py)     (tests/test_simulator.py)
```

---

## 4. Dataset Description & Data Dictionary

The synthetic hospital dataset represents 3 hospital facilities (**St. Jude Memorial Hospital**, **Metro Health Medical Center**, **City General Hospital**) across 15 specialized units with **5,200 patient records**.

### A. Patients Table (`data/clean/patients.csv`)
| Field Name | Type | Description | Sample Values / Range |
|---|---|---|---|
| `Patient_ID` | String | Unique patient identifier | `P00001` - `P05200` |
| `Age` | Integer | Patient age in years | 1 - 92 |
| `Gender` | String | Patient gender | `Male`, `Female`, `Non-Binary` |
| `Acuity_Level` | String | Clinical acuity classification | `Low`, `Medium`, `High`, `Critical` |
| `Diagnosis_Category` | String | Primary diagnosis category | `Septic Shock`, `Pneumonia`, `Trauma` |
| `Required_Nursing_Hours`| Float | Required nursing care hours per shift | 1.5 - 14.0 hrs |
| `Required_Skill` | String | Required unit specialty skill | `ICU`, `Emergency`, `Med-Surg`, `Pediatrics`, `Oncology` |
| `Unit_ID` | String | Assigned hospital unit ID | `U001` - `U015` |
| `Facility_ID` | String | Assigned hospital facility ID | `F01`, `F02`, `F03` |
| `Admission_Date` | Timestamp| Date and time of admission | YYYY-MM-DD HH:MM:SS |
| `Transfer_Status` | String | Patient transfer state | `Admitted`, `Pending Transfer`, `Transfer Approved`, `Discharged` |

### B. Nurses Table (`data/clean/nurses.csv`)
| Field Name | Type | Description | Sample Values / Range |
|---|---|---|---|
| `Nurse_ID` | String | Unique nurse roster ID | `N0001` - `N0400` |
| `Unit_ID` | String | Primary assigned unit | `U001` - `U015` |
| `Facility_ID` | String | Assigned hospital facility | `F01`, `F02`, `F03` |
| `Shift` | String | Assigned shift roster | `Day`, `Evening`, `Night` |
| `Available_Hours` | Float | Hours available in current shift | 0.0, 8.0, 12.0 hrs |
| `Nurse_Skill_Level` | Integer | Competency level | 1 (Basic) to 4 (Expert/Specialist) |
| `Specialty` | String | Primary specialty qualification | `ICU`, `Emergency`, `Med-Surg`, `Pediatrics`, `Oncology` |
| `Experience_Level` | String | Years of experience bracket | `Junior`, `Mid`, `Senior`, `Specialist` |
| `Availability_Status` | String | Current status | `Available`, `On Shift`, `Off Duty`, `Reassigned` |

### C. Units Table (`data/clean/units.csv`)
| Field Name | Type | Description | Sample Values / Range |
|---|---|---|---|
| `Unit_ID` | String | Unique unit identifier | `U001` - `U015` |
| `Facility_ID` | String | Hospital facility ID | `F01`, `F02`, `F03` |
| `Unit_Type` | String | Unit specialty category | `ICU`, `Emergency`, `Med-Surg`, `Pediatrics`, `Oncology` |
| `Bed_Capacity` | Integer | Total licensed beds in unit | 25 - 60 beds |
| `Occupied_Beds` | Integer | Currently occupied beds | 15 - 55 beds |
| `Minimum_Staff` | Integer | Minimum safe staffing requirement | 6 - 12 nurses |
| `Maximum_Staff` | Integer | Maximum physical nurse capacity | 14 - 27 nurses |
| `Current_Staff` | Integer | Currently assigned nurses | 4 - 22 nurses |

---

## 5. Data Generation Rules (`src/data_generator.py`)
Generates raw synthetic records with intentional real-world data quality issues:
* **Missing Values**: ~3% missing acuity levels, nursing hours, and nurse specialties.
* **Duplicates**: ~1.5% duplicate patient and nurse records.
* **Dirty Data Types**: `Available_Hours` stored as strings with trailing text (e.g., `"12.0 hrs"`).
* **Inconsistent Categories**: Mixed casing (`"icu"`, `"ICU"`, `"night_shift"`, `"MedSurg"`).
* **Invalid Outliers**: Negative ages (e.g., `-5`), invalid acuity levels (`"Ultra-Critical"`), extreme nursing hours (e.g., `99.0` hrs).

---

## 6. Data Cleaning & Preprocessing (`src/data_cleaning.py`)
1. **Deduplication**: `drop_duplicates()` on unique primary keys (`Patient_ID`, `Nurse_ID`).
2. **Missing Value Imputation**: Missing `Acuity_Level` imputed with mode (`"Medium"`). Missing `Required_Nursing_Hours` imputed with median hours by acuity level.
3. **Category Standardization**: Standardizes string categories to upper-case/title-case standard dictionary.
4. **Outlier Capping**: Capping negative ages to median age and capping `Required_Nursing_Hours` > 16.0 hours to acuity group median.

---

## 7. Workload Calculation Model (`src/workload.py`)

$$\text{Patient Workload} = \text{Required Nursing Hours} \times \text{Acuity Weight}$$

**Prototype Acuity Weights**:
* Low Acuity: $1.0$
* Medium Acuity: $1.25$
* High Acuity: $1.5$
* Critical Acuity: $2.0$

*Note: These weights are synthetic prototype parameters for evaluation and do not represent validated clinical standards.*

$$\text{Total Unit Workload} = \sum_{p \in \text{Active Patients}} \text{Patient Workload}_p$$

---

## 8. Staffing Calculation Model (`src/staffing.py`)

$$\text{Required Nurses} = \left\lceil \frac{\text{Total Unit Workload}}{\text{Shift Hours}} \right\rceil$$

$$\text{Target Nurses} = \max(\text{Minimum Staff}, \text{Required Nurses})$$

$$\text{Staffing Gap} = \max(0, \text{Target Nurses} - \text{Active Nurses})$$

$$\text{Staffing Surplus} = \max(0, \text{Active Nurses} - \text{Target Nurses})$$

$$\text{Workload Per Nurse} = \frac{\text{Total Unit Workload}}{\text{Active Nurses}}$$

---

## 9. Skill-Matching Engine (`src/skill_matching.py`)

A nurse is only eligible for safe reassignment if:
1. Nurse `Availability_Status == "Available"`.
2. Donor unit `Active Nurses > Minimum Staff` (Protects donor unit safety).
3. Receiving unit `Staffing Gap > 0`.
4. Receiving unit `Occupied Beds < Bed Capacity` (Protects physical bed capacity).
5. Nurse specialty matches receiving unit type OR nurse possesses Level 4 expert certification.

---

## 10. Operating Scenarios & Simulator Engine (`src/simulator.py`)
* **Scenario 1 – Baseline**: Normal acuity multiplier (1.0), normal staff multiplier (1.0).
* **Scenario 2 – High Acuity (+25%)**: Acuity multiplier = 1.25.
* **Scenario 3 – Staff Shortage (-20%)**: Staff availability multiplier = 0.80.
* **Scenario 4 – Combined Stress**: Acuity multiplier = 1.25, Staff multiplier = 0.80.

$$\text{Workload Imbalance Reduction \%} = \frac{\sigma_{\text{pre}} - \sigma_{\text{post}}}{\sigma_{\text{pre}}} \times 100$$

where $\sigma$ is the standard deviation of workload per nurse across units.

---

## 11. Dashboard / UI Design (`dashboard/app.py`)
Built using Streamlit and Plotly with dark-mode aesthetic, KPI summary cards, interactive scenario switching, sensitivity heatmaps, failure sandbox, and action tracking.

---

## 12. Failure Cases & Safety Boundaries
1. **Failure Case 1 (Skill Mismatch)**: Prevents assigning non-ICU nurses to critical ICU beds.
2. **Failure Case 2 (Donor Minimum Staffing)**: Blocks transfers that would leave donor units below minimum safe staffing threshold.
3. **Failure Case 3 (Receiving Unit Capacity)**: Prevents patient transfers to units at 100% bed capacity.

---

## 13. Experimental Results Summary
| Scenario | Pre-Gap | Post-Gap | Pre-Imbalance ($\sigma$) | Post-Imbalance ($\sigma$) | Improvement % | Safe Transfers | Unsafe Blocked |
|---|---|---|---|---|---|---|---|
| **Baseline** | 24 | 24 | 7.65 | 7.32 | 4.29% | 15 | 269 |
| **High Acuity (+25%)** | 40 | 40 | 9.56 | 9.15 | 4.26% | 15 | 37 |
| **Staff Shortage (-20%)** | 32 | 32 | 16.52 | 16.16 | 2.15% | 13 | 30 |
| **Combined Stress** | 69 | 69 | 11.46 | 11.27 | 1.60% | 5 | 6 |

---

## 14. Sensitivity Analysis
Tested across Acuity Multipliers (+10%, +25%, +40%) and Staff Shortages (-10%, -20%, -30%). Demonstrates that safe reassignment capacity degrades under severe combined stress, signaling when managerial escalation is required.

---

## 15. Stakeholder Feedback (Review 1 Peer & Mentor Feedback)
* **Strengths**: Clear visualization of staffing gaps, strict skill-matching protection, interactive scenario stress-testing.
* **Improvement Suggestions**: Add real-time roster sync, include nurse fatigue/overtime indicators, expand to multi-shift lookahead.

---

## 16. Prototype Limitations
1. Uses synthetic patient and nurse data.
2. Workload weights are prototype parameters, not clinically validated scales.
3. Simulation operates on static shift snapshots rather than continuous real-time telemetry.

---

## 17. Pending Work (65% Remaining)
1. Integer Linear Programming (ILP) optimization engine.
2. Multi-shift lookahead forecasting.
3. Integration with HL7/FHIR hospital data standards.
4. Real-time nurse fatigue and union rule tracking.

---

## 18. Future Enhancements
1. Machine learning acuity prediction based on EHR vitals.
2. Mobile notification module for charge nurses.
3. Executive hospital network performance dashboard.
