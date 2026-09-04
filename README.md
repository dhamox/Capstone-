# 🏥 Shift Workload-Balancing Simulator for Hospital Patient Transfers

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Pytest-Passing-brightgreen.svg)]()
[![Milestone](https://img.shields.io/badge/Review%201-35%25%20Prototype%20Target-orange.svg)]()

A decision-support prototype that simulates patient acuity-weighted nursing workload, calculates unit staffing gaps/surpluses, and recommends **safe, skill-matched nurse reassignments** without compromising donor unit safety or breaching physical bed capacity.

---

## 📌 Project Overview (Review 1 Target - 35% Prototype)

Hospital shift managers routinely lack a real-time, cross-unit view of nursing workload imbalance during patient transfers. This repository contains a **35% working functional prototype** developed for Review 1.

### Key Functional Features
* **Synthetic Hospital Group Dataset**: ~5,200 patient records across 3 facilities and 15 specialized units with realistic data quality flaws (missing values, duplicates, dirty types, outliers).
* **Data Cleaning Pipeline**: Automated deduplication, missing value imputation, type casting, category normalization, and outlier capping (`src/data_cleaning.py`).
* **Workload & Staffing Engine**: Acuity-weighted workload formulas and staffing gap/surplus metrics (`src/workload.py`, `src/staffing.py`).
* **Safe Skill-Matching Engine**: Rule engine validating nurse availability, donor unit minimum staffing protection, receiving unit bed capacity, and specialty skill compatibility (`src/skill_matching.py`).
* **Operating Scenario Simulator**: Executes 4 scenarios (Baseline, High Acuity +25%, Staff Shortage -20%, Combined Stress) and calculates **Workload Imbalance Reduction %** (`src/simulator.py`).
* **Interactive Streamlit Dashboard**: Web app featuring KPI cards, Plotly charts, scenario controls, sensitivity heatmap, edge-case sandbox, and escalation action tracker (`dashboard/app.py`).
* **Automated Pytest Suite**: Full unit tests covering cleaning rules, workload math, skill matching, and failure cases (`tests/test_simulator.py`).

---

## 📂 Repository Structure

```
hospital-workload-balancing-simulator/
│
├── data/
│   ├── raw/                  # Generated raw CSVs with intentional flaws
│   └── clean/                # Cleaned CSV datasets (patients.csv, nurses.csv, units.csv)
│
├── src/
│   ├── data_generator.py     # Generates synthetic hospital dataset (~5,200 patients)
│   ├── data_cleaning.py      # Cleans raw dataset according to documented rules
│   ├── workload.py           # Patient acuity & unit workload calculations
│   ├── staffing.py           # Available/required capacity, staffing gap & surplus
│   ├── skill_matching.py     # Safe skill-matching rule engine
│   └── simulator.py          # Scenario simulation engine & sensitivity analysis
│
├── dashboard/
│   └── app.py                # Interactive Streamlit & Plotly dashboard
│
├── notebooks/
│   └── experiment.ipynb      # Measurable experiment & sensitivity analysis notebook
│
├── docs/
│   ├── technical_documentation.md  # 19-section technical architecture & documentation
│   ├── failure_analysis.md         # Detailed edge case & safety analysis
│   └── workflow.md                 # Field operational workflow diagram
│
├── tests/
│   └── test_simulator.py     # Pytest unit test suite
│
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Installation
Clone the repository and install required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Generate & Clean Dataset
Run the data cleaning pipeline to generate raw synthetic data and produce clean CSVs in `data/clean`:
```bash
python src/data_cleaning.py
```

### 4. Run Operating Scenario Simulation
Execute the operating scenario simulator from terminal:
```bash
python src/simulator.py
```

### 5. Launch Interactive Dashboard
Run the Streamlit web application:
```bash
streamlit run dashboard/app.py
```

### 6. Run Automated Tests
Execute pytest suite:
```bash
pytest tests/
```

---

## 📊 Summary of Experimental Results

| Scenario | Gap (Pre) | Gap (Post) | Imbalance Std (Pre) | Imbalance Std (Post) | Imbalance Reduction % | Safe Transfers | Unsafe Blocked |
|---|---|---|---|---|---|---|---|
| **Scenario 1 – Baseline** | 24 | 24 | 7.65 | 7.32 | 4.29% | 15 | 269 |
| **Scenario 2 – High Acuity (+25%)** | 40 | 40 | 9.56 | 9.15 | 4.26% | 15 | 37 |
| **Scenario 3 – Staff Shortage (-20%)** | 32 | 32 | 16.52 | 16.16 | 2.15% | 13 | 30 |
| **Scenario 4 – Combined Stress** | 69 | 69 | 11.46 | 11.27 | 1.60% | 5 | 6 |

---

## ⚠️ Prototype Assumptions & Safety Disclaimer
* **Decision Support Prototype**: This software is developed for Review 1 evaluation using synthetic data. It is a decision-support tool and **not** an autonomous clinical decision maker.
* **Clinical Approval Required**: All nurse reassignment recommendations must be validated by a clinical shift manager prior to execution.
* **Synthetic Parameters**: Workload weights and capacity formulas are prototype assumptions and do not represent validated clinical standards.
