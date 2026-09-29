import os
import sys
import pandas as pd
from datetime import datetime, date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def evaluate_action_escalations(df_actions, current_date=None):
    """
    Evaluates action tracking items and triggers automatic escalation for 
    unresolved high-priority issues past their due date.
    
    Escalation Levels:
    Level 0 – Normal (Assigned to Owner)
    Level 1 – Manager Alert (Shift Manager Escalation)
    Level 2 – Clinical/Ops Lead Escalation (Operations Director Alert)
    Level 3 – Senior Executive Escalation (Hospital VP / Executive Alert)
    """
    if current_date is None:
        current_date = date.today()
    elif isinstance(current_date, str):
        current_date = datetime.strptime(current_date, "%Y-%m-%d").date()

    df = df_actions.copy()

    def apply_escalation(row):
        due = row["Due_Date"]
        if isinstance(due, str):
            due = datetime.strptime(due, "%Y-%m-%d").date()
        
        status = row["Status"]
        priority = row["Priority"]
        esc_level = row["Escalation_Level"]

        # Check if overdue and unresolved
        is_overdue = due < current_date
        is_unresolved = status != "Resolved"

        if is_unresolved and is_overdue:
            if priority == "High":
                if esc_level == "Level 0 – Normal" or esc_level == "None":
                    row["Escalation_Level"] = "Level 2 – Clinical/Ops Lead"
                    row["Escalation_Date"] = current_date.strftime("%Y-%m-%d")
                    row["Comments"] = f"[SYSTEM AUTO-ESCALATION] Overdue high-priority staffing gap escalated to Clinical Ops Lead on {current_date}."
                elif esc_level == "Level 1 – Shift Manager":
                    row["Escalation_Level"] = "Level 3 – Senior Executive"
                    row["Escalation_Date"] = current_date.strftime("%Y-%m-%d")
                    row["Comments"] = f"[SYSTEM AUTO-ESCALATION] Critical overdue issue escalated to Senior Executive on {current_date}."
            elif priority == "Medium":
                if esc_level == "Level 0 – Normal" or esc_level == "None":
                    row["Escalation_Level"] = "Level 1 – Shift Manager"
                    row["Escalation_Date"] = current_date.strftime("%Y-%m-%d")
                    row["Comments"] = f"[SYSTEM AUTO-ESCALATION] Overdue medium issue escalated to Shift Manager on {current_date}."
        
        return row

    return df.apply(apply_escalation, axis=1)

def get_sample_action_items():
    """Returns sample shift action items for testing and dashboard rendering."""
    return pd.DataFrame([
        {
            "Action_ID": "ACT-001",
            "Issue": "ICU Staffing Shortage in St. Jude General",
            "Priority": "High",
            "Owner": "Nurse Manager Sarah Jenkins",
            "Created_Date": "2026-08-28",
            "Due_Date": "2026-09-01", # Overdue
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
            "Due_Date": "2026-09-02", # Overdue
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
