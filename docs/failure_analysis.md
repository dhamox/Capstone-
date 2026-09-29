# Failure & Edge Case Analysis - Hospital Workload Balancing Simulator

This document presents a comprehensive technical breakdown of **8 realistic failure modes and edge cases** evaluated by the Shift Workload-Balancing Simulator, detailing detection mechanisms, safety mitigations, and escalation procedures.

---

## 1. Failure Modes & Safety Matrix (8 Failure Modes)

| Failure Mode | Cause | Effect | Detection Mechanism | Mitigation Strategy | Escalation Protocol |
|---|---|---|---|---|---|
| **1. Skill Mismatch** | Receiving unit (e.g. ICU) needs coverage, but available donor nurses lack specialty certification | Unsafe patient care if assigned; skill gap | `validate_safe_reassignment()` skill compatibility check | Block reassignment; flag skill gap | Level 1: Shift Manager Alert to call in off-duty specialist |
| **2. Donor Unit Depletion** | Donor unit has excess workload capacity, but transfer drops staff below minimum bounds | Weakens donor unit safety; creates new gap | Donor active nurses check: `Active - 1 < Minimum_Staff` | Block transfer; enforce minimum staffing protection | Level 2: Clinical Ops Lead Alert for inter-facility pool |
| **3. Physical Bed Capacity Bottleneck** | Patient transfer requested to a unit currently at 100% bed occupancy | Overcrowding; physical bed shortage | Bed occupancy check: `Occupied_Beds >= Bed_Capacity` | Block transfer; redirect patient flow | Level 2: Ops Lead Alert for accelerated discharge |
| **4. Nurse Double-Assignment Conflict** | Same nurse selected concurrently for multiple unit transfers | Roster conflict; scheduling overlap | Active reassignment state locking check | Lock candidate nurse ID during evaluation queue | Level 1: Manager notification of concurrent request |
| **5. Off-Duty / Absent Nurse Selection** | Roster database lists nurse as available when call-out occurred | False surplus calculation | Nurse status validation: `Availability_Status == "Available"` | Filter out off-duty nurses; recalculate capacity | Level 1: Roster supervisor alert to update status |
| **6. Inter-Facility Shift Misalignment** | Reassignment attempted between facilities with mismatched shift schedules | Shift overlap; overtime violation | Shift roster alignment check (`Day`, `Evening`, `Night`) | Restrict reassignments to compatible shift windows | Level 1: Shift Manager approval required |
| **7. Multi-Unit Staffing Exhaustion** | Severe network-wide shortage where all units hit minimum staffing | Safe reassignment capacity drops to 0 | Global surplus tracking: `Total_Surplus == 0` | Issue network-wide capacity alert | Level 3: Senior Executive / Hospital VP Alert |
| **8. EHR Acuity Data Staleness & Latency** | Electronic Health Record updates lag behind rapid patient deterioration | Underestimated unit workload score | Real-time acuity refresh & scenario stress testing | Trigger High Acuity scenario simulation (+25%) | Level 2: Clinical Lead alert for manual acuity override |

---

## 2. Decision-Support Boundaries & Human-in-the-Loop Gateway

> **IMPORTANT CLINICAL DISCLAIMER**:
> This simulator functions strictly as a **decision-support software prototype**. It generates candidate nurse reassignment recommendations based on quantitative workload calculations and pre-defined safety rules. 
> 
> **All recommendations MUST be reviewed, validated, and approved by a qualified clinical shift manager or charge nurse before any physical staff reassignment or patient transfer takes place.**
