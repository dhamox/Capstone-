# Final Project Presentation - Shift Workload-Balancing Simulator

**Slide Deck Outline for Final Defense**

---

### Slide 1: Title Slide
* **Title**: Shift Workload-Balancing Simulator for Hospital Patient Transfers
* **Subtitle**: A Decision-Support Prototype for Safe Nurse Reassignment & Workload Optimization
* **Presenter**: Dhamodharan
* **Domain**: Healthcare Operations & Software Engineering

### Slide 2: Problem Statement
* Cross-unit workload imbalance during patient transfers.
* Shift managers lack real-time visibility into acuity-weighted nursing workload.
* Uncoordinated reassignments risk nurse burnout and safe staffing breaches.

### Slide 3: Objectives
* Develop a quantitative workload balancing model considering patient acuity, care hours, staffing gaps, donor surpluses, and bed capacity.
* Enforce strict safe reassignment rules to block 100% of unsafe transfers.
* Build an interactive, multi-page dashboard for shift manager decision support.

### Slide 4: System Architecture
* Modular Python pipeline: Data Generator $\rightarrow$ Cleaner $\rightarrow$ Workload/Staffing Math $\rightarrow$ Skill Matcher $\rightarrow$ Scenario Simulator $\rightarrow$ 7-Page Streamlit App.

### Slide 5: Synthetic Dataset Overview
* ~5,200 patient records across 3 facilities and 15 units.
* Realistic data quality flaw injection and automated cleaning rules.

### Slide 6: Mathematical Model & Workload Formula
* $\text{Patient Workload} = \text{Required Care Hours} \times \text{Acuity Weight}$.
* Weights: Low=1.0, Medium=1.25, High=1.5, Critical=2.0.

### Slide 7: Staffing Gap & Donor Surplus Logic
* $\text{Required Nurses} = \lceil \text{Total Workload} / 12.0 \rceil$.
* $\text{Staffing Gap} = \max(0, \text{Target} - \text{Active})$.
* $\text{Donor Surplus} = \max(0, \text{Active} - \text{Target})$.

### Slide 8: Patient Transfer Decision Engine
* Evaluates transfer requests across 7 explicit outcome states (`Approved`, `Clinical Review`, `Blocked Capacity`, `Blocked Staffing`, `Blocked Skill Mismatch`, `Blocked Unsafe`, `Escalated`).

### Slide 9: Safe Skill-Matching & `validate_safe_reassignment()`
* Validates 8 core safety rules (Nurse availability, minimum staffing protection, bed capacity, specialty match, shift window).

### Slide 10: 8 Operating Scenarios Breakdown
* Baseline, High Acuity (+25%), Staff Shortage (-20%), Combined Stress, Transfer Surge (+35%), Specialist Shortage (-50%), Bed Constraint (-25%), Multi-Unit Stress.

### Slide 11: Experimental Setup & Reproducibility
* Multi-seed experiment executed across 10 random dataset seeds.

### Slide 12: Experimental Results
* Achieved **4.31% average workload imbalance reduction** in Baseline scenario.
* Blocked **100% of unsafe transfers** (269 unsafe attempts prevented).

### Slide 13: Sensitivity Analysis Heatmaps
* Multi-parameter stress heatmaps across Acuity (10-40%), Staffing (0-40%), Skill Availability, and Bed Capacity.

### Slide 14: Failure Mode Analysis (8 Failure Cases)
* Detailed breakdown of 8 failure modes, causes, effects, detection mechanisms, and mitigations.

### Slide 15: Human-in-the-Loop Gateway & Audit Log
* Explainable recommendation rationale presentation.
* Interactive Manager Approval/Rejection buttons with audit trail logging (`data/audit_log.csv`).

### Slide 16: Action Tracking & Overdue Auto-Escalation
* Automated escalation engine advancing overdue high-priority items from Level 0 to Level 3.

### Slide 17: 7-Page Interactive Dashboard Demo
* Overview of Streamlit application pages (Executive Overview, Unit Workload, Scenario Simulator, Transfer Decision, Safety Sandbox, Sensitivity Heatmaps, Action Tracker).

### Slide 18: Automated Testing & Verification
* 8 automated unit tests passing with 100% success rate in pytest.

### Slide 19: Stakeholder & Mentor Feedback
* Validation feedback from 4 simulated shift managers and project mentor.

### Slide 20: Prototype Limitations
* Synthetic data reliance, heuristic matching engine, static shift snapshots.

### Slide 21: Future Work & Roadmap
* Integer Linear Programming (ILP) optimization, 24h/48h multi-shift lookahead forecasting, HL7/FHIR integration.

### Slide 22: Conclusion
* Successfully completed a 100% functional, submission-ready decision-support prototype for Review 1 and Final Project Submission.

### Slide 23: Q&A / Thank You
* Questions & Answers.
