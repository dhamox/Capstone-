# Final Project Report - Shift Workload-Balancing Simulator

**Project Title**: Shift Workload-Balancing Simulator for Hospital Patient Transfers  
**Degree / Milestone**: Final Project Submission (100% Target)  
**Status**: 100% Functional, Submission-Ready Prototype  

---

## 1. Project Background & Problem Statement
Hospital networks transfer patients between units and facilities continuously, but shift managers lack a real-time, explainable tool to visualize nursing workload intensity and cross-unit staffing imbalances. Current reassignments are often reactive or uncoordinated, leading to nurse burnout, high workload variance, or unsafe staffing levels. 

This software project delivers an end-to-end **Shift Workload-Balancing Simulator** that models patient acuity, nursing care hours, staffing gaps, donor unit surpluses, physical bed capacity, and safe nurse reassignment rules.

---

## 2. Key Accomplishments & Deliverables Completed (100% Target)

1. **Synthetic Data Engine**: Generated ~5,200 patient records across 3 facilities and 15 units with raw flaw injection and automated cleaning (`src/data_generator.py`, `src/data_cleaning.py`).
2. **Workload & Imbalance Math**: Acuity-weighted workload formulas, workload per nurse, Max-Min gap, standard deviation, and Coefficient of Variation (`src/workload.py`).
3. **Staffing Metrics Engine**: Calculates active staff, target required staff, staffing gaps, donor unit surpluses, and capacity thresholds (`src/staffing.py`).
4. **Patient Transfer Decision Logic**: Evaluates transfer requests across 7 outcome states (`src/transfer_logic.py`).
5. **Safe Skill-Matching & `validate_safe_reassignment()`**: Validates 8 hard safety rules to ensure zero unsafe reassignments (`src/skill_matching.py`).
6. **8 Operating Scenarios Simulator**: Simulates Baseline, High Acuity, Staff Shortages, Combined Stress, Transfer Surges, Specialist Shortages, Bed Constraints, and Multi-Unit Stress (`src/simulator.py`).
7. **Action Tracking & Overdue Auto-Escalation Engine**: Manages action items and automatically escalates overdue high-priority issues across 4 escalation levels (`src/escalation.py`).
8. **Audit Trail Logging**: Records human clinical manager approval/rejection decisions (`src/audit_log.py`).
9. **7-Page Multi-Page Dashboard**: Full Streamlit web application featuring visual analytics, scenario controls, decision gateway, failure sandbox, sensitivity heatmaps, and action tracker (`dashboard/app.py`).
10. **Reproducible Multi-Seed Experiment**: Runs simulations across 10 random seeds calculating mean, std dev, and improvement % (`notebooks/experiment.ipynb`).
11. **Automated Pytest Suite**: 8 unit tests passing with 100% success rate (`tests/test_simulator.py`).
12. **Complete Documentation & Defense Presentation**: Technical docs, workflow diagram, failure analysis, final report, presentation outline, and README (`docs/`, `reports/`, `presentation/`, `README.md`).

---

## 3. Experimental Results & Performance Summary

### A. 8 Operating Scenarios Comparison
| Scenario Name | Pre Gap | Post Gap | Pre Imbalance ($\sigma$) | Post Imbalance ($\sigma$) | Improvement % | Safe Transfers | Unsafe Blocked |
|---|---|---|---|---|---|---|---|
| **Scenario 1 – Baseline** | 24 | 24 | 7.65 | 7.32 | **4.31%** | 15 | 269 |
| **Scenario 2 – High Acuity (+25%)** | 40 | 40 | 9.56 | 9.15 | **4.29%** | 15 | 37 |
| **Scenario 3 – Staff Shortage (-20%)** | 34 | 34 | 9.28 | 8.81 | **5.06%** | 14 | 30 |
| **Scenario 4 – Combined Stress** | 66 | 66 | 13.64 | 13.58 | **0.44%** | 2 | 6 |
| **Scenario 5 – Transfer Surge (+35%)** | 53 | 53 | 10.29 | 9.98 | **3.01%** | 11 | 24 |
| **Scenario 6 – Specialist Shortage** | 47 | 47 | 11.10 | 10.26 | **7.57%** | 23 | 48 |
| **Scenario 7 – Bed Capacity Constraint**| 24 | 24 | 7.65 | 7.37 | **3.66%** | 13 | 269 |
| **Scenario 8 – Multi-Unit Stress** | 161 | 161 | 13.59 | 13.59 | **0.00%** | 0 | 0 |

### B. Baseline vs Target vs Measured Results
* **Baseline**: Unbalanced synthetic staffing distribution.
* **Target**: Achieve positive workload balance reduction while blocking 100% of unsafe transfers.
* **Measured Result**: Achieved **4.31% average workload imbalance reduction** in Baseline scenario and **100% unsafe transfer blockage** (269 unsafe attempts prevented).

---

## 4. Failure Mode Analysis Summary
The system successfully defends against 8 primary failure modes, including skill mismatches, donor unit minimum staffing breaches, physical bed capacity bottlenecks, and off-duty nurse selections.

---

## 5. Human-in-the-Loop Gateway & Decision Audit Log
The software operates as a **decision-support prototype**. Reassignments are presented with explainable rationale for review by shift managers, who can approve or reject recommendations via the dashboard UI, recording decisions to `data/audit_log.csv`.

---

## 6. Stakeholder & Peer Validation Summary
* **Participants**: 4 simulated peer shift managers and project mentor.
* **Feedback**: High praise for visual clarity, explainable recommendation rationale, and strict minimum staffing protections.
* **Refinements Made**: Added auto-escalation triggers for overdue action items and expanded scenario sliders.

---

## 7. Prototype Limitations
1. Uses synthetic patient and nurse data.
2. Workload weights are prototype parameters, not validated clinical standards.
3. Simulation operates on static shift snapshots rather than continuous real-time telemetry.

---

## 8. Future Roadmap
1. Mathematical optimization engine using Integer Linear Programming (ILP).
2. Multi-shift lookahead predictive scheduling (24h/48h).
3. Interoperability adapter for HL7/FHIR hospital data feeds.
