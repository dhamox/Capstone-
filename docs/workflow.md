# Field Workflow Map - Hospital Workload Balancing & Patient Transfer

This document outlines the operational field workflow mapping patient acuity collection, workload calculation, automated safety checks, manager review, and outcome monitoring.

---

## Operational Workflow Diagram

```
                 [ Patient Transfer / Shift Change Request ]
                                    │
                                    ▼
                      [ Collect Patient Acuity Data ]
                     (Acuity Levels: Low to Critical)
                                    │
                                    ▼
                     [ Calculate Nursing Workload ]
            (Workload = Required Hours × Acuity Weight)
                                    │
                                    ▼
                      [ Check Unit Bed Capacity ]
                    (Occupied Beds vs Bed Capacity)
                                    │
                                    ▼
                    [ Check Staffing Availability ]
                    (Active Staff vs Target Staff)
                                    │
                                    ▼
                   [ Check Nurse Skill Match Rules ]
               (Specialty, Skill Level 1-4, Experience)
                                    │
                                    ▼
                [ Identify Unit Staffing Gaps & Surpluses ]
                                    │
                                    ▼
                  [ Run Workload Balancing Simulator ]
            (Generate Safe Skill-Matched Recommendations)
                                    │
                                    ▼
               [ Generate Safe Recommendation Report ]
                                    │
                                    ▼
                ┌───────────────────────────────────┐
                │ 🧑‍⚕️ HUMAN CLINICAL APPROVAL POINT │
                │ Shift Manager / Supervisor Review │
                └─────────────────┬─────────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
            [ Approved ]                    [ Rejected ]
                  │                               │
                  ▼                               ▼
       [ Execute Transfer / ]            [ Log Escalation / ]
       [ Reassign Nurse    ]            [ Seek Alternative ]
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                    [ Monitor Patient Outcome & ]
                    [ Post-Balance Workload    ]
```

---

## Step-by-Step Step Breakdown

1. **Patient Transfer Request**: A facility or unit requests patient admission or inter-unit transfer.
2. **Collect Patient Acuity**: System retrieves patient acuity level (Low = 1.0, Medium = 1.25, High = 1.5, Critical = 2.0) and required nursing hours.
3. **Calculate Nursing Workload**: Total unit workload score is updated.
4. **Check Unit Capacity**: Verifies receiving unit has available beds (`Occupied_Beds < Bed_Capacity`).
5. **Check Staffing Availability**: Calculates active nurses vs target nurses.
6. **Check Nurse Skill Match**: Evaluates candidate nurse specialties against receiving unit requirements.
7. **Identify Gaps & Surpluses**: Categorizes units as Donor (Surplus) or Receiving (Gap).
8. **Run Balancing Simulator**: Evaluates candidate pairs and computes optimal safe reassignments.
9. **Generate Safe Recommendation**: Outputs structured reassignment plan.
10. **Manager Review & Clinical Approval**: Shift manager verifies clinical suitability. **(Human-in-the-Loop Gateway)**.
11. **Transfer / Reassignment Execution**: Approved nurse reassignment or patient transfer takes place.
12. **Monitor Outcome**: System tracks post-balancing workload per nurse and unit stability.
