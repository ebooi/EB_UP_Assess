# Technical Documentation

University of Pretoria Institutional Analytics Dashboard, Version 3.0.

## Architecture

Streamlit multi-page application. The entry point (`app.py`) presents the landing page. Each subsequent page lives in `pages/` and is auto-discovered. Shared logic sits in `utils/`. A unified filter panel is rendered on every page through `utils/filters.py`.

## Module responsibilities

**utils/constants.py** holds brand colours, DHET thresholds and removal rates, UP 2025 targets, and the DHET 2025 sector student success benchmark (80%). A single edit propagates institution-wide.

**utils/data_loader.py** loads the Excel file once per session using `@st.cache_data`. Derived columns are computed at load time. A generic `aggregate(df, by)` function produces consistent aggregations at any grouping level. Specialised helpers exist for Level (UG vs PG) and FundingGroup (SET vs Business/General).

**utils/filters.py** renders the shared sidebar filter panel. Filters cover Faculty, Programme Cluster, Level, Funding Group, Mode, and Year range. Every page calls `apply_filters(df)` at the top to receive a filtered DataFrame.

**utils/calculations.py** implements compliance status (UP 2025 ±2%, DHET -2%/+3%), subsidy exposure, CAGR.

**utils/data_quality.py** implements four quality dimensions: Completeness (missing cells), Accuracy (range validity), Consistency (cross-field rules), Reliability (year-on-year stability). Each scores 0-1 per faculty per year. An aggregate scorecard combines them.

**utils/forecasting.py** provides:
- `constrained_institutional_forecast` — plan-anchored 5-year projection with 2% YoY growth cap. This replaces the v2 actuals-based forecast that was inflated by the 2023 outlier.
- `ug_pg_mix_forecast` — Total grows at the cap, UG share converges linearly to 70% over a user-specified number of years.
- `funding_group_forecast` — SET and Business/General projected separately at the institutional cap rate.
- `shape_size_simulation` — Static simulation comparing current mix to a new mix.

**utils/statistics.py** provides executive-grade statistical analysis: trend regression with significance test, year-on-year growth statistics with confidence intervals, distribution analysis with IQR-based outlier detection, correlation analysis between enrolment and graduate growth (the throughput gap signal), and forecast accuracy (MAPE between plan and actual).

**utils/theme.py** applies the UP brand CSS, renders the standard page header with the UP logo on every page, and exposes a `status_badge` helper.

## Page implementations

### Institutional Performance
Four tabs: Enrolment, Student Success, Efficiency, Financial.

The Enrolment tab is the most expanded. It shows the actual vs plan KPIs at the top with dual compliance status, a UG vs PG visualisation showing headcount and share by Level, a Year-Level summary table with Approved Plan, HC Actual, HC FTE, TIU Proxy, and Variance, colour-coded above and below the 2% threshold. Below that, the trend chart shows both UP 2025 and DHET thresholds, and the faculty variance chart shows the spread.

The Statistical analysis section then provides:
- Trend regression: slope, R-squared, p-value for both actual and plan series.
- Year-on-year growth analysis with 95% confidence intervals.
- Faculty variance distribution: mean, median, std, IQR, outliers.
- Throughput correlation analysis between enrolment and graduate growth.
- Forecast accuracy (MAPE) of actuals against approved plans historically.

The Student Success tab benchmarks against the DHET 80% sector rate explicitly. It includes a faculty x level heatmap showing success rate at the intersection of Faculty and UG/PG.

### Data Governance
Eight principles each shown as a card with:
- Definition
- Executive evidence tracked
- Owner
- Key risk and mitigation
- Status badge (Green/Amber/Red)

Below the principles, the page shows aggregate scores for the four quality dimensions, a heatmap by faculty for the latest year, and a trend chart showing dimension scores over time.

### Enrolment Forecasting
Three sections.

First, institutional headcount projection. The forecast starts from the latest approved plan, not the latest actual. This is the key fix. The 2025 actual exceeds plan by 14.2% because of the 2023 dummy data spike. Forecasting from actuals would inflate the projection. Forecasting from the plan baseline at 2% YoY produces a sustainable trajectory.

Second, UG/PG mix forecast. The total grows at the institutional cap. UG share converges from current (around 77%) to the 70% target over a user-specified number of years. The chart shows headcount and share side by side, with target reference lines.

Third, Funding Group forecast. SET and Business/General projected separately at the cap rate.

### What-If Scenarios
Three tabs:

The Comprehensive Scenario tab takes all eight inputs (headcount, graduate, research, debt, capacity, staff growth, penalty trigger, internal funding pool) and projects them forward year by year. It calculates the year-by-year DHET penalty exposure using the user-defined trigger threshold and the escalating removal rates. The cumulative penalty is compared to the internal funding pool to show shortfall or surplus.

The Shape and Size Simulator allows shifting PG share and SET share to see impact on TIU, graduates, and subsidy.

The Faculty and Funding Group View shows the latest-year disaggregation by faculty (headcount, TIU, graduate conversion) and by funding group (headcount, TIU, TIU per FTE, implicit subsidy).

## Visual design

The colour palette follows the brief:
- UP Blue (#0C2340) for headings and primary elements
- UP Red (#C8102E) for risks and alerts
- UP Gold (#C39B47) for highlights and dividers
- White and Light Grey (#F4F4F4) for spacing

Sidebar uses UP Blue background with white text. Every page begins with the UP logo and a gold accent bar. Executive commentary cards use coloured left borders.

## Forecasting methodology

The five-year forecast uses two methods, both subject to a YoY growth cap.

**Plan-anchored baseline**: Starts from the latest approved plan and compounds at the cap rate. Avoids extrapolating actual-vs-plan deviations into the future. This is the primary forecast shown in gold on the Enrolment Forecasting page.

**Statistical reference**: Linear regression on actuals with 95% confidence interval, shown in grey for context.

The UG/PG mix forecast uses a separate convergence model. Given a target share and a number of convergence years, the UG share moves linearly from current to target. The total grows at the cap. UG and PG are derived from total times the year-specific share.

The shape-and-size simulator applies simplified DHET teaching input weights: SET fields weighted 2.5x at undergraduate vs 1.5x for general; postgraduate qualifications weighted 2.5x to 5x undergraduate. Graduate rates differ between undergraduate (0.20) and postgraduate (0.45). These weights are illustrative; precise simulation requires programme-level CESM mapping.

## Data quality dimensions

**Completeness**: Share of non-missing cells across nine key fields (ActualHeadcount, FTE, Graduates, ResearchOutputUnits, AcademicStaffFTE, SuccessRate, TuitionRevenue_Rm, StudentDebt_Rm, CapacitySeats).

**Accuracy**: Share of records passing range-validity checks. SuccessRate and DropoutRate must be 0-1. Numeric fields must be non-negative.

**Consistency**: Share of records passing cross-field rules. FTE must be 0.1-1.3 times headcount. Graduates must not exceed headcount.

**Reliability**: Share of records with stable year-on-year change (under 50%).

The aggregate scorecard averages the four dimensions per faculty per year and produces an Overall score. Below 95% triggers an Amber alert; below 85% triggers a Red alert with explicit reference to the R5m HEMIS penalty and R20m audit opinion penalty.

## DHET formulae

Implicit rand value per TIU: R27,236,878,000 / 1,619,343 = R16,819.

Removal rates escalate by data year: 50% (2024), 60% (2025), 70% (2026).

UP 2025 internal threshold: ±2% variance from plan at faculty level.

DHET acceptable variance: -2% to +3%.

DHET 2025 sector student success benchmark: 80%.

## Caveats

The dataset is dummy data. Real UP figures would be approximately 2.5 times larger in headcount and TIU terms.

Forecasts use 8 years of annual data. The plan-anchored approach reduces the impact of the 2023 outlier but the statistical reference forecast still extrapolates from actuals.

The application does not include authentication or audit logging. These are required before production use.

The dummy dataset contains intentional data quality issues to demonstrate the integrity monitor.
