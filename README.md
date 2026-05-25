# Institutional Analytics Dashboard v3

A Streamlit application for institutional analytics, forecasting, and executive reporting. Built for the Senior Manager: Institutional Analytics assessment in May 2026.

## What this dashboard does

The application supports strategic decision-making by the executive management and cascades down to the faculty. It links enrolment, student success, staff, and financial data to the funding instruments and targets.

## Pages

1. **Institutional Performance** — Enrolment (UG/PG breakdown, summary table with colour-coded variances, detailed statistical analysis), Student Success (against DHET 80% sector benchmark with faculty x level disaggregation), Efficiency, and Financial indicators.
2. **Subsidy and Strategic Risk** — TIU, TOU, graduate conversion, output per FTE, and rand-value exposure under the DHET penalty regime.
3. **Data Governance** — Eight principles with executive evidence, status, owners, and key risks. Plus four data quality dimensions: completeness, accuracy, consistency, and reliability by faculty.
4. **Enrolment Forecasting** — Five-year projection anchored to the approved plan with 2% YoY growth cap. UG/PG mix converging to 70/30 research-led target. SET vs Business/General forecast.
5. **What-If Scenarios** — Three tabs: comprehensive scenario (8 inputs including penalty trigger and funding pool), shape-and-size simulator, faculty and funding group view.
6. **Data Definition** — Complete data dictionary with sources and calculation rules.

## Shared filters

Every page reads from a shared sidebar filter panel. Filter by Faculty, Programme Cluster, Level (UG/PG), Funding Group (SET/Business-General), Mode (Contact/Distance), and Year range.

## Setup

Requirements: Python 3.10 or higher.

```bash
git clone <repository-url>
cd up_analytics
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
streamlit run app.py
```

The application opens at `http://localhost:8501`.

## Deployment to Streamlit Community Cloud

1. Push the repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect to your GitHub repository.
4. Set the main file to `app.py`.
5. Deploy.

## Project structure

```
up_analytics/
├── app.py
├── requirements.txt
├── README.md
├── TECHNICAL_DOCUMENTATION.md
├── .gitignore
├── data/
│   └── Faculty_Enrolment.xlsx
├── assets/
│   └── up_logo.png
├── utils/
│   ├── __init__.py
│   ├── constants.py
│   ├── data_loader.py
│   ├── calculations.py
│   ├── data_quality.py
│   ├── filters.py
│   ├── forecasting.py
│   ├── statistics.py
│   └── theme.py
└── pages/
    ├── 1_Institutional_Performance.py
    ├── 2_Subsidy_Strategic_Risk.py
    ├── 3_Data_Governance.py
    ├── 4_Enrolment_Forecasting.py
    ├── 5_What_If_Scenarios.py
    └── 6_Data_Definition.py
```

## Colour conventions

- **UP Blue** for headings and primary elements
- **Red** for strategic risks and alerts
- **Gold** for highlights, evidence points, and dividers
- **White / Light Grey** for spacing and readability

Status colour coding: Green for compliant, Amber for watch, Red for breach.

## Data caveat

The application uses a dummy enrolment dataset for demonstration. The teaching input unit totals are smaller than UP's actual Ministerial-approved allocations because the dataset is at the sub-institutional scale. All DHET threshold and penalty calculations use the actual figures from the 2025 Ministerial Statement.
