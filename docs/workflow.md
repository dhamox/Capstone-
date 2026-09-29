# Operational Field Workflow Map - Hospital Workload Balancing

This document details the step-by-step operational field workflow mapping patient transfer requests, acuity collection, workload calculation, safety validation, human clinical manager approval, monitoring, and escalation.

---

## 1. Field Operational Workflow Diagram

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
                   [ Check Nurse Skill Mix Rules ]
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
                   [ Run Safety Rule Validation ]
             (validate_safe_reassignment - 8 Rules)
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
       [ Execute Transfer / ]            [ Log Audit Reason / ]
       [ Reassign Nurse    ]            [ Seek Alternative   ]
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                    [ Monitor Patient Outcome & ]
                    [ Post-Balance Workload    ]
                                  │
                                  ▼
                    [ Action Item & Overdue Log ]
                     (Auto-Escalation L0 -> L3)
```

---

## 2. Phase-by-Phase Process Description

1. **Transfer Request**: Initiated by unit charge nurse or transfer center.
2. **Acuity Assessment**: Patient acuity classified (Low=1.0, Medium=1.25, High=1.5, Critical=2.0).
3. **Workload Computation**: Unit workload score updated based on active census.
4. **Capacity Validation**: Physical bed availability verified (`Occupied < Capacity`).
5. **Staffing Check**: Active staff compared against target staffing bounds.
6. **Skill-Mix Evaluation**: Nurse specialty matched against unit requirements.
7. **Simulation Execution**: Candidate donor-receiving unit pairs evaluated.
8. **Safety Validation**: `validate_safe_reassignment()` verifies 8 hard safety rules.
9. **Recommendation Generation**: System outputs explainable recommendation rationale.
10. **Human Clinical Manager Gate**: Shift manager approves/rejects recommendation (**Human-in-the-Loop Gateway**).
11. **Audit Logging**: Manager decision recorded in `data/audit_log.csv`.
12. **Execution & Monitoring**: Post-balancing workload per nurse monitored.
13. **Auto-Escalation**: Unresolved overdue action items trigger auto-escalation (Level 0 to Level 3).
