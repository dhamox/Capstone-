# Failure & Edge Case Analysis - Workload-Balancing Simulator

This document provides a detailed technical analysis of the 3 primary failure/edge cases enforced by the simulator, as well as real-world operational risks and decision-support safety boundaries.

---

## 1. Primary Failure Cases

### Failure Case 1: Skill Mismatch (No Specialist Available)
* **Scenario**: A receiving unit (e.g., ICU) experiences a staffing shortage and requests additional nurse coverage. However, the available surplus nurses in donor units only hold Med-Surg or General certifications.
* **Simulator Response**: The simulator flags a skill mismatch error and prevents the reassignment recommendation.
* **Clinical Rationale**: Reassigning a nurse without ICU competency to a critical unit compromises patient safety and violates nursing practice standards.
* **Mitigation / Recommendation**: Issue an alert to the shift manager to call in an off-duty ICU specialist or initiate inter-facility patient transfer.

---

### Failure Case 2: Donor Unit Depletion (Minimum Staffing Protection)
* **Scenario**: A receiving unit has a staffing gap, and a donor unit appears to have active nurses available. However, transferring a nurse out of the donor unit would cause its active staff count to drop below `Minimum_Staff`.
* **Simulator Response**: The simulator blocks the reassignment and logs a "Donor minimum staffing breach" protection alert.
* **Clinical Rationale**: Weakening one unit below minimum safe staffing bounds to solve a shortage in another unit spreads vulnerability and increases overall hospital risk.
* **Mitigation / Recommendation**: Preserve donor unit baseline staffing; seek alternative donor units or administrative escalation.

---

### Failure Case 3: Receiving Unit at Physical Capacity
* **Scenario**: A patient transfer request is submitted to balance workload, but the receiving unit is currently at 100% bed capacity (`Occupied_Beds == Bed_Capacity`).
* **Simulator Response**: The simulator flags the physical bed capacity bottleneck and blocks the transfer recommendation.
* **Clinical Rationale**: Transferring patients or assigning staff to a physically saturated unit creates severe overcrowding and delays emergency care.
* **Mitigation / Recommendation**: Prioritize discharge processing or redirect patient transfers to secondary network facilities.

---

## 2. Real-World Operational Risks & Mitigation

| Risk Factor | Description | Simulator Defense / Handling |
|---|---|---|
| **Incorrect Roster Data** | Nurse availability status incorrectly logged as available when off-duty | Data cleaning & validation checks; human manager confirmation requirement |
| **Delayed Data Updates** | Electronic Health Record (EHR) acuity updates lag behind sudden patient deterioration | Dynamic scenario re-simulation with parameter sliders (+25% acuity) |
| **Unexpected Absenteeism** | Sudden nurse call-outs during shift change | Staff shortage scenario simulation (-20% staff multiplier) |
| **Multiple Simultaneous Transfers** | Race conditions during peak transfer hours | Queue-based reassignment evaluation with lock checks |
| **Automation Bias** | Managers blindly executing AI recommendations without clinical review | Explicit system disclaimers requiring clinical sign-off before transfer |

---

## 3. Decision-Support Boundary Statement
> **IMPORTANT**: This simulator operates strictly as a **decision-support prototype**. It generates candidate reassignment recommendations based on quantitative workload metrics and pre-defined skill matching rules. All recommendations **MUST** be reviewed and approved by a qualified clinical shift manager prior to execution.
