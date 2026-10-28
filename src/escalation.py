"""
Action Tracking and Automated Escalation Engine
===============================================
Project: Shift Workload-Balancing Simulator for Hospital Patient Transfers
Author: Hospital Operations Research & AI Engineering Team
Version: 3.0.0 (Review 3 Final Release)

Description:
    Manages operational follow-up items, staffing exception tracking, and
    automated escalation workflows. Ensures that unresolved high-priority
    staffing deficits and bed bottlenecks never get lost or ignored.

Escalation Hierarchy:
    - Level 0 (Normal):
      Issue logged and assigned to local unit charge nurse or shift supervisor.
    - Level 1 (Shift Manager Alert):
      Triggered when medium-priority issues exceed target resolution dates.
    - Level 2 (Clinical/Operations Lead Escalation):
      Triggered when high-priority staffing gaps or capacity bottlenecks become overdue.
    - Level 3 (Senior Hospital Executive Alert):
      Triggered for persistent, unmitigated critical shortages across multiple shifts.

Boundary Rules:
    - Status == 'Resolved' never triggers escalation regardless of due date.
    - Current date is compared against Due_Date strictly in YYYY-MM-DD format.
    - Malformed dates fallback gracefully to avoid unhandled runtime exceptions.
"""

import os
import sys
import pandas as pd
from datetime import datetime, date

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def evaluate_action_escalations(df_actions: pd.DataFrame, current_date=None) -> pd.DataFrame:
    """
    Evaluates action tracking items and triggers automatic escalation for 
    unresolved high-priority issues past their due date.

    Parameters:
    -----------
    df_actions : pd.DataFrame
        DataFrame of action items with columns:
        - 'Action_ID': Unique identifier (str)
        - 'Issue': Description of staffing/capacity issue (str)
        - 'Priority': 'High', 'Medium', or 'Low' (str)
        - 'Owner': Person accountable (str)
        - 'Due_Date': Target completion date (YYYY-MM-DD)
        - 'Status': 'Open', 'In Progress', or 'Resolved' (str)
        - 'Escalation_Level': Current level ('Level 0 – Normal', etc.)
        - 'Escalation_Date': Date of last escalation (str)
        - 'Comments': Audit notes (str)
    current_date : str or datetime.date, optional
        Reference evaluation date. Defaults to date.today().

    Returns:
    --------
    pd.DataFrame
        Updated DataFrame with modified Escalation_Level, Escalation_Date,
        and automated comment trails.

    Error Boundaries & Safeguards:
    ------------------------------
    - Handles malformed or missing dates gracefully without crashing.
    - Preserves existing resolution notes on already resolved items.
    - Does not downgrade previously escalated items.
    """
    if df_actions.empty:
        return df_actions.copy()

    if current_date is None:
        eval_date = date.today()
    elif isinstance(current_date, str):
        try:
            eval_date = datetime.strptime(current_date, "%Y-%m-%d").date()
        except ValueError:
            eval_date = date.today()
    elif isinstance(current_date, (datetime, date)):
        eval_date = current_date if isinstance(current_date, date) else current_date.date()
    else:
        eval_date = date.today()

    df = df_actions.copy()

    def apply_escalation(row):
        due_val = row.get("Due_Date", "")
        if isinstance(due_val, str):
            try:
                due = datetime.strptime(due_val, "%Y-%m-%d").date()
            except ValueError:
                # If date cannot be parsed, treat as not overdue to prevent accidental escalation
                due = eval_date
        elif isinstance(due_val, (datetime, date)):
            due = due_val if isinstance(due_val, date) else due_val.date()
        else:
            due = eval_date

        status = str(row.get("Status", "Open"))
        priority = str(row.get("Priority", "Medium"))
        esc_level = str(row.get("Escalation_Level", "Level 0 – Normal"))

        # Escalation criteria: unresolved and strictly overdue
        is_overdue = due < eval_date
        is_unresolved = status != "Resolved"

        if is_unresolved and is_overdue:
            if priority == "High":
                if esc_level in ["Level 0 – Normal", "None", ""]:
                    row["Escalation_Level"] = "Level 2 – Clinical/Ops Lead"
                    row["Escalation_Date"] = eval_date.strftime("%Y-%m-%d")
                    row["Comments"] = f"[SYSTEM AUTO-ESCALATION] Overdue high-priority staffing gap escalated to Clinical Ops Lead on {eval_date}."
                elif esc_level == "Level 1 – Shift Manager":
                    row["Escalation_Level"] = "Level 3 – Senior Executive"
                    row["Escalation_Date"] = eval_date.strftime("%Y-%m-%d")
                    row["Comments"] = f"[SYSTEM AUTO-ESCALATION] Critical overdue issue escalated to Senior Executive on {eval_date}."
            elif priority == "Medium":
                if esc_level in ["Level 0 – Normal", "None", ""]:
                    row["Escalation_Level"] = "Level 1 – Shift Manager"
                    row["Escalation_Date"] = eval_date.strftime("%Y-%m-%d")
                    row["Comments"] = f"[SYSTEM AUTO-ESCALATION] Overdue medium issue escalated to Shift Manager on {eval_date}."
        
        return row

    return df.apply(apply_escalation, axis=1)


def get_sample_action_items() -> pd.DataFrame:
    """
    Returns baseline sample shift action items for dashboard rendering and integration testing.

    Returns:
    --------
    pd.DataFrame
        Table of active shift action items across facilities.
    """
    return pd.DataFrame([
        {
            "Action_ID": "ACT-001",
            "Issue": "ICU Staffing Shortage in St. Jude General",
            "Priority": "High",
            "Owner": "Nurse Manager Sarah Jenkins",
            "Created_Date": "2026-08-28",
            "Due_Date": "2026-09-01",  # Overdue relative to operational date
            "Status": "Open",
            "Escalation_Level": "Level 0 – Normal",
            "Escalation_Date": "",
            "Resolution": "Pending Reassignment Approval",
            "Comments": "Awaiting ICU certified nurse availability"
        },
        {
            "Action_ID": "ACT-002",
            "Issue": "Emergency Bed Capacity Bottleneck",
            "Priority": "High",
            "Owner": "Ops Director Mark Vance",
            "Created_Date": "2026-08-30",
            "Due_Date": "2026-09-02",  # Overdue relative to operational date
            "Status": "In Progress",
            "Escalation_Level": "Level 1 – Shift Manager",
            "Escalation_Date": "2026-09-02",
            "Resolution": "Discharge Processing Accelerated",
            "Comments": "Coordinating with social work for patient discharge"
        },
        {
            "Action_ID": "ACT-003",
            "Issue": "Med-Surg Skill Certification Update",
            "Priority": "Medium",
            "Owner": "HR Specialist Amanda Ray",
            "Created_Date": "2026-08-25",
            "Due_Date": "2026-09-10",
            "Status": "Resolved",
            "Escalation_Level": "Level 0 – Normal",
            "Escalation_Date": "",
            "Resolution": "Certifications updated in roster database",
            "Comments": "All Level 3 nurses verified"
        }
    ])


if __name__ == "__main__":
    df_act = get_sample_action_items()
    esc_df = evaluate_action_escalations(df_act, current_date="2026-09-04")
    print("Action Item Escalation Results:")
    print(esc_df[["Action_ID", "Priority", "Status", "Due_Date", "Escalation_Level", "Comments"]])
