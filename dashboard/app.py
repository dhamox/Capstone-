import os
import sys
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as gg

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_cleaning import run_cleaning_pipeline
from src.workload import calculate_unit_workload
from src.staffing import calculate_unit_staffing
from src.skill_matching import evaluate_reassignment_candidates
from src.simulator import run_scenario_simulation, run_all_operating_scenarios, run_sensitivity_analysis

# Page Config
st.set_page_config(
    page_title="Hospital Workload-Balancing Simulator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glassmorphism & Medical Theme accents)
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        font-family: 'Inter', sans-serif;
    }
    .kpi-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
    }
    .kpi-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        color: #38bdf8;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .kpi-sub {
        color: #10b981;
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 2px;
    }
    .badge-high {
        background-color: #ef4444;
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-med {
        background-color: #f59e0b;
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-low {
        background-color: #10b981;
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Load Clean Data
@st.cache_data
def get_data():
    return run_cleaning_pipeline()

df_units, df_nurses, df_patients = get_data()

# Sidebar Controls
st.sidebar.image("https://img.icons8.com/isometric-line/100/hospital.png", width=70)
st.sidebar.title("Simulator Controls")
st.sidebar.caption("Shift Workload-Balancing Prototype (Review 1 Target - 35%)")

# Filter Options
facilities = ["All Facilities"] + list(df_units["Facility_Name"].unique())
sel_facility_name = st.sidebar.selectbox("Hospital Facility", facilities)

if sel_facility_name != "All Facilities":
    sel_fac_id = df_units[df_units["Facility_Name"] == sel_facility_name]["Facility_ID"].iloc[0]
    filtered_units = df_units[df_units["Facility_ID"] == sel_fac_id]
    filtered_nurses = df_nurses[df_nurses["Facility_ID"] == sel_fac_id]
    filtered_patients = df_patients[df_patients["Facility_ID"] == sel_fac_id]
else:
    filtered_units = df_units.copy()
    filtered_nurses = df_nurses.copy()
    filtered_patients = df_patients.copy()

unit_types = ["All Units"] + list(df_units["Unit_Type"].unique())
sel_unit_type = st.sidebar.selectbox("Unit Specialty", unit_types)

if sel_unit_type != "All Units":
    filtered_units = filtered_units[filtered_units["Unit_Type"] == sel_unit_type]
    filtered_patients = filtered_patients[filtered_patients["Required_Skill"] == sel_unit_type]

shifts = ["All Shifts", "Day", "Evening", "Night"]
sel_shift = st.sidebar.selectbox("Shift Roster", shifts)

if sel_shift != "All Shifts":
    filtered_nurses = filtered_nurses[filtered_nurses["Shift"] == sel_shift]

st.sidebar.markdown("---")
st.sidebar.subheader("Scenario Selector")

scenarios_map = {
    "Baseline (Normal)": (1.0, 1.0),
    "High Acuity (+25% Workload)": (1.25, 1.0),
    "Staff Shortage (-20% Nurses)": (1.0, 0.80),
    "Combined Stress (+25% Acuity, -20% Staff)": (1.25, 0.80)
}

sel_scenario_label = st.sidebar.selectbox("Operating Scenario", list(scenarios_map.keys()))
acuity_mult, staff_mult = scenarios_map[sel_scenario_label]

st.sidebar.markdown("---")
st.sidebar.info("**Decision-Support Prototype**: Not for autonomous clinical decision-making. Requires human manager approval.")

# Run Simulation Engine for Selected Scenario
sim_result = run_scenario_simulation(
    filtered_units, filtered_nurses, filtered_patients,
    scenario_name=sel_scenario_label,
    acuity_multiplier=acuity_mult,
    staff_multiplier=staff_mult
)

summary = sim_result["summary"]
pre_staffing = sim_result["pre_staffing"]
post_staffing = sim_result["post_staffing"]
reassignments = sim_result["reassignments"]
unsafe_prevented = sim_result["unsafe_prevented"]

# Title Banner
st.title("🏥 Shift Workload-Balancing Simulator")
st.caption("Hospital Patient Transfer & Safe Nurse Reassignment Support System | 35% Prototype Target")

# Top KPI Header
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Active Patients</div>
        <div class="kpi-value">{summary['Total_Patients']:,}</div>
        <div class="kpi-sub">Census Tracked</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Active Nurses</div>
        <div class="kpi-value">{summary['Total_Nurses']}</div>
        <div class="kpi-sub">Available/Shift</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Staffing Gap</div>
        <div class="kpi-value" style="color: #f87171;">{summary['Pre_Staffing_Gap']}</div>
        <div class="kpi-sub">Pre-Balance Need</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Donor Surplus</div>
        <div class="kpi-value" style="color: #34d399;">{summary['Pre_Staffing_Surplus']}</div>
        <div class="kpi-sub">Available Surplus</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Safe Capacity</div>
        <div class="kpi-value" style="color: #38bdf8;">{summary['Safe_Reassignment_Capacity']}</div>
        <div class="kpi-sub">Skill-Matched</div>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Imbalance Red.</div>
        <div class="kpi-value" style="color: #a78bfa;">{summary['Imbalance_Reduction_Pct']}%</div>
        <div class="kpi-sub">Workload Balance</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Operating Dashboards",
    "🔄 Reassignment Simulator",
    "📈 Multi-Scenario Comparison",
    "⚡ Sensitivity Analysis",
    "⚠️ Failure & Edge Cases",
    "📋 Action & Escalation Tracker"
])

# TAB 1: OPERATING DASHBOARD
with tab1:
    st.subheader(f"Current Operating Snapshot: {sel_scenario_label}")
    
    r1_col1, r1_col2 = st.columns(2)
    
    with r1_col1:
        # Chart 1: Staffing Gap & Surplus by Unit
        gap_df = pre_staffing[["Unit_ID", "Unit_Type", "Staffing_Gap", "Staffing_Surplus"]].copy()
        fig_gap = px.bar(
            gap_df, x="Unit_ID", y=["Staffing_Gap", "Staffing_Surplus"],
            barmode="group",
            title="Staffing Gap vs Surplus by Hospital Unit",
            labels={"value": "Nurse Count", "variable": "Metric"},
            color_discrete_map={"Staffing_Gap": "#ef4444", "Staffing_Surplus": "#10b981"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_gap, use_container_width=True)

    with r1_col2:
        # Chart 2: Total Workload by Unit
        fig_wl = px.bar(
            pre_staffing, x="Unit_ID", y="Total_Workload", color="Unit_Type",
            title="Total Patient Workload Score by Unit",
            labels={"Total_Workload": "Workload Score", "Unit_ID": "Unit"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_wl, use_container_width=True)

    r2_col1, r2_col2 = st.columns(2)

    with r2_col1:
        # Chart 3: Workload per Nurse by Unit
        fig_wpn = px.bar(
            pre_staffing, x="Unit_ID", y="Workload_Per_Nurse",
            color="Workload_Per_Nurse",
            color_continuous_scale="Reds",
            title="Workload Intensity Per Nurse (Pre-Balancing)",
            labels={"Workload_Per_Nurse": "Workload Units / Nurse"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_wpn, use_container_width=True)

    with r2_col2:
        # Chart 4: Patient Acuity Breakdown
        acuity_counts = filtered_patients["Acuity_Level"].value_counts().reset_index()
        acuity_counts.columns = ["Acuity_Level", "Count"]
        fig_pie = px.pie(
            acuity_counts, names="Acuity_Level", values="Count",
            title="Patient Census Acuity Distribution",
            color="Acuity_Level",
            color_discrete_map={"Low": "#34d399", "Medium": "#60a5fa", "High": "#fbbf24", "Critical": "#f87171"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# TAB 2: REASSIGNMENT SIMULATOR
with tab2:
    st.subheader("Safe Nurse Reassignment Recommendations")
    st.caption("Skill-Matched Nurse Reassignments from Surplus (Donor) Units to Shortage (Receiving) Units")

    col_b1, col_b2 = st.columns([2, 1])

    with col_b1:
        if not reassignments.empty:
            st.dataframe(
                reassignments[[
                    "Nurse_ID", "Nurse_Specialty", "Nurse_Skill_Level", 
                    "Donor_Unit", "Receiving_Unit", "Receiving_Unit_Type", "Status"
                ]],
                use_container_width=True
            )
        else:
            st.warning("No safe nurse reassignments possible for the selected criteria.")

    with col_b2:
        st.markdown("### Balancing Impact")
        st.metric("Workload Imbalance Std (Pre)", f"{summary['Pre_Workload_Imbalance_Std']:.2f}")
        st.metric("Workload Imbalance Std (Post)", f"{summary['Post_Workload_Imbalance_Std']:.2f}")
        st.metric("Workload Imbalance Reduction", f"{summary['Imbalance_Reduction_Pct']}%", delta=f"{summary['Imbalance_Reduction_Pct']}%")
        st.metric("Unsafe Attempts Blocked", f"{summary['Unsafe_Attempts_Prevented']}")

    st.markdown("---")
    st.subheader("Unit-by-Unit Before vs After Workload Comparison")

    comp_df = pd.merge(
        pre_staffing[["Unit_ID", "Workload_Per_Nurse"]].rename(columns={"Workload_Per_Nurse": "Pre_Workload_Per_Nurse"}),
        post_staffing[["Unit_ID", "Workload_Per_Nurse"]].rename(columns={"Workload_Per_Nurse": "Post_Workload_Per_Nurse"}),
        on="Unit_ID"
    )

    fig_comp = px.bar(
        comp_df, x="Unit_ID", y=["Pre_Workload_Per_Nurse", "Post_Workload_Per_Nurse"],
        barmode="group",
        title="Workload Per Nurse: Before vs After Safe Balancing",
        color_discrete_map={"Pre_Workload_Per_Nurse": "#ef4444", "Post_Workload_Per_Nurse": "#38bdf8"},
        template="plotly_dark"
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# TAB 3: MULTI-SCENARIO COMPARISON
with tab3:
    st.subheader("Comparative Stress-Test Across 4 Operating Scenarios")
    
    all_res, summary_matrix = run_all_operating_scenarios(df_units, df_nurses, df_patients)

    st.dataframe(
        summary_matrix[[
            "Scenario_Name", "Pre_Staffing_Gap", "Pre_Staffing_Surplus", 
            "Safe_Reassignment_Capacity", "Imbalance_Reduction_Pct", "Unsafe_Attempts_Prevented"
        ]],
        use_container_width=True
    )

    fig_sc_gap = px.bar(
        summary_matrix, x="Scenario_Name", y="Pre_Staffing_Gap",
        color="Scenario_Name",
        title="Staffing Gap Across Operating Scenarios",
        template="plotly_dark"
    )
    st.plotly_chart(fig_sc_gap, use_container_width=True)

# TAB 4: SENSITIVITY ANALYSIS
with tab4:
    st.subheader("Sensitivity Analysis Matrix")
    st.caption("Evaluating impact of varying Acuity Scale (+10% to +40%) and Nurse Shortages (-10% to -30%)")

    sens_df = run_sensitivity_analysis(df_units, df_nurses, df_patients)

    fig_heat = px.density_heatmap(
        sens_df, x="Acuity_Increase", y="Staff_Shortage", z="Pre_Staffing_Gap",
        title="Staffing Gap Heatmap under Combined Parameter Stress",
        labels={"Pre_Staffing_Gap": "Total Staffing Gap"},
        color_continuous_scale="Reds",
        template="plotly_dark"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.dataframe(sens_df, use_container_width=True)

# TAB 5: FAILURE & EDGE CASES
with tab5:
    st.subheader("Edge & Failure Case Handling Sandbox")
    st.markdown("""
    The simulator enforces **3 hard safety rules** to prevent unsafe reassignment decisions:
    """)

    ec_choice = st.radio(
        "Select Edge Case Scenario to Test:",
        [
            "Failure Case 1 – Skill Mismatch (No Specialist Available)",
            "Failure Case 2 – Donor Unit Protection (At Minimum Staffing)",
            "Failure Case 3 – Receiving Unit at Physical Bed Capacity"
        ]
    )

    if "Failure Case 1" in ec_choice:
        st.error("❌ **Blocked Reassignment**: Receiving unit requires ICU specialist, but donor unit only has General Med-Surg nurses.")
        st.caption("Expected Action: Prevent unsafe transfer, flag skill gap for clinical manager intervention.")
    elif "Failure Case 2" in ec_choice:
        st.warning("⚠️ **Blocked Reassignment**: Donor unit is currently at minimum safe staffing bounds (Minimum_Staff = 5).")
        st.caption("Expected Action: Protect donor unit safety. Prevent transferring nurses out of fragile units.")
    else:
        st.info("🛑 **Blocked Reassignment**: Receiving unit physical bed capacity reached (Occupied = Capacity).")
        st.caption("Expected Action: Flag unit bottleneck, prevent physical patient transfer overflow.")

    if not unsafe_prevented.empty:
        st.subheader("Prevented Unsafe Reassignment Log (Current Run)")
        st.dataframe(unsafe_prevented, use_container_width=True)

# TAB 6: ACTION & ESCALATION TRACKER
with tab6:
    st.subheader("Shift Manager Follow-up & Escalation Module")
    st.caption("Ensuring high-priority staffing gaps and clinical warnings are tracked to resolution.")

    # Sample escalation action tracker
    actions_data = [
        {"Action_ID": "ACT-001", "Issue": "ICU Nurse Gap in St. Jude General", "Priority": "High", "Responsible_Owner": "Shift Mgr. Sarah Jenkins", "Due_Date": "2026-09-04", "Status": "Open", "Escalation_Level": "Level 2 (Director Alert)"},
        {"Action_ID": "ACT-002", "Issue": "Med-Surg Overstaffing Surplus Reassignment", "Priority": "Medium", "Responsible_Owner": "Charge Nurse David Miller", "Due_Date": "2026-09-04", "Status": "In Progress", "Escalation_Level": "Level 1 (Unit Supervisor)"},
        {"Action_ID": "ACT-003", "Issue": "Skill Level 4 Certification Renewal", "Priority": "Low", "Responsible_Owner": "HR Specialist Amanda Ray", "Due_Date": "2026-09-10", "Status": "Resolved", "Escalation_Level": "None"}
    ]

    df_actions = pd.DataFrame(actions_data)

    st.dataframe(df_actions, use_container_width=True)

    # Form to add new action item
    with st.expander("➕ Log New Shift Action / Escalation Item"):
        with st.form("new_action_form"):
            issue_text = st.text_input("Issue Description")
            prio = st.selectbox("Priority Level", ["High", "Medium", "Low"])
            owner = st.text_input("Responsible Owner")
            due = st.date_input("Due Date")
            submitted = st.form_submit_button("Submit Action Item")
            if submitted and issue_text:
                st.success(f"Logged Action Item: {issue_text} (Priority: {prio}) assigned to {owner}.")

st.markdown("---")
st.caption("Shift Workload-Balancing Simulator | Developed for Review 1 (35% Working PrototypeTarget)")
