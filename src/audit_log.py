import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def record_manager_decision(
    recommendation_id,
    nurse_id,
    source_unit,
    dest_unit,
    user_role,
    decision,
    reason="",
    audit_file="data/audit_log.csv"
):
    """
    Records a human clinical manager approval or rejection decision to the audit log.
    
    Fields:
    - Timestamp
    - Recommendation_ID
    - Nurse_ID
    - Source_Unit
    - Dest_Unit
    - User_Role
    - Decision (Approved, Rejected, Overridden)
    - Reason / Clinical Notes
    """
    os.makedirs(os.path.dirname(audit_file), exist_ok=True)
    
    log_entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Recommendation_ID": recommendation_id,
        "Nurse_ID": nurse_id,
        "Source_Unit": source_unit,
        "Dest_Unit": dest_unit,
        "User_Role": user_role,
        "Decision": decision,
        "Reason": reason
    }

    if os.path.exists(audit_file):
        df_log = pd.read_csv(audit_file)
        df_log = pd.concat([df_log, pd.DataFrame([log_entry])], ignore_index=True)
    else:
        df_log = pd.DataFrame([log_entry])

    df_log.to_csv(audit_file, index=False)
    return df_log

def load_audit_log(audit_file="data/audit_log.csv"):
    """Loads audit trail history."""
    if os.path.exists(audit_file):
        return pd.read_csv(audit_file)
    return pd.DataFrame(columns=[
        "Timestamp", "Recommendation_ID", "Nurse_ID", "Source_Unit", 
        "Dest_Unit", "User_Role", "Decision", "Reason"
    ])

if __name__ == "__main__":
    record_manager_decision("REC-101", "N0012", "U001", "U003", "Shift Manager", "Approved", "Skill match verified")
    print(load_audit_log())
