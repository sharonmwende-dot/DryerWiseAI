
import io
import os
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DryerWise AI",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# FILES AND CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HISTORY_FILE = os.path.join(BASE_DIR, "dryerwise_history.csv")
MAINTENANCE_FILE = os.path.join(BASE_DIR, "dryerwise_maintenance.csv")

HISTORY_COLUMNS = [
    "Timestamp",
    "Operator",
    "Mode",
    "Temperature_C",
    "Moisture_Percent",
    "Energy_kWh",
    "Notes",
]

MAINTENANCE_COLUMNS = [
    "Date_Logged",
    "Equipment",
    "Issue",
    "Action_Taken",
    "Responsible_Person",
    "Due_Date",
    "Status",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_csv(path, columns):
    """Load a CSV file or return an empty dataframe."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=columns)

    try:
        df = pd.read_csv(path)
        for column in columns:
            if column not in df.columns:
                df[column] = ""
        return df[columns]
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return pd.DataFrame(columns=columns)


def save_csv(df, path):
    """Save a dataframe to CSV."""
    df.to_csv(path, index=False, encoding="utf-8")


def make_excel(history, maintenance):
    """Create an Excel workbook in memory."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        history.to_excel(writer, sheet_name="Operating History", index=False)
        maintenance.to_excel(
            writer, sheet_name="Maintenance", index=False
        )

    output.seek(0)
    return output.getvalue()


def maintenance_status(due_date, current_status):
    """Calculate whether a maintenance task is overdue."""
    if current_status in ["Completed", "Cancelled"]:
        return current_status

    try:
        due = pd.to_datetime(due_date).date()
    except (ValueError, TypeError):
        return current_status

    if due < date.today():
        return "Overdue"

    return "Open"


# ============================================================
# SESSION STATE
# ============================================================

if "saved_message" not in st.session_state:
    st.session_state.saved_message = ""


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("⚙️ DryerWise AI")
    st.caption("Industrial Dryer Monitoring")

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Operating History",
            "Maintenance",
            "Reports & Export",
        ],
    )

    st.divider()

    st.subheader("Prototype settings")
    st.warning(
        "The thresholds below are demonstration values only. "
        "They are not verified safety limits for your equipment."
    )

    temp_limit = st.number_input(
        "Example high-temperature threshold (°C)",
        min_value=1.0,
        max_value=1500.0,
        value=300.0,
        step=5.0,
    )

    moisture_limit = st.number_input(
        "Example high-moisture threshold (%)",
        min_value=0.0,
        max_value=100.0,
        value=30.0,
        step=1.0,
    )

    energy_limit = st.number_input(
        "Example high-energy threshold (kWh)",
        min_value=1.0,
        value=140.0,
        step=5.0,
    )

    st.divider()
    st.caption("Local prototype • No live machine connection")


# ============================================================
# LOAD DATA
# ============================================================

history = load_csv(HISTORY_FILE, HISTORY_COLUMNS)
maintenance = load_csv(MAINTENANCE_FILE, MAINTENANCE_COLUMNS)


# ============================================================
# HEADER
# ============================================================

st.title("⚙️ DryerWise AI")
st.write("Dryer operations, performance tracking and maintenance.")

header_left, header_right = st.columns([3, 1])

with header_left:
    st.caption(
        f"Current date: {date.today().strftime('%d %B %Y')}"
    )

with header_right:
    st.metric("Saved operating records", len(history))


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.header("Live Reading Entry")
    st.info(
        "Enter readings taken by the operator. "
        "These values are manual inputs, not live sensor readings."
    )

    with st.form("operating_readings_form"):

        operator = st.text_input("Operator name")

        mode = st.selectbox(
            "Operating mode",
            [
                "Stopped",
                "Starting",
                "Running",
                "Cooling",
                "Maintenance",
            ],
            index=2,
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            temperature = st.number_input(
                "Temperature (°C)",
                min_value=0.0,
                max_value=1500.0,
                value=150.0,
                step=1.0,
            )

        with col2:
            moisture = st.number_input(
                "Material moisture (%)",
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                step=0.5,
            )

        with col3:
            energy = st.number_input(
                "Energy consumption (kWh)",
                min_value=0.0,
                value=50.0,
                step=1.0,
            )

        notes = st.text_area(
            "Operator observations",
            placeholder="Describe material condition, smoke, vibration, "
                        "noise or other observations...",
        )

        submitted = st.form_submit_button(
            "Save Operating Reading",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            new_record = pd.DataFrame(
                [
                    {
                        "Timestamp": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "Operator": operator.strip() or "Not specified",
                        "Mode": mode,
                        "Temperature_C": temperature,
                        "Moisture_Percent": moisture,
                        "Energy_kWh": energy,
                        "Notes": notes.strip(),
                    }
                ]
            )

            history = pd.concat(
                [history, new_record], ignore_index=True
            )
            save_csv(history, HISTORY_FILE)

            st.session_state.saved_message = (
                "Operating reading saved successfully."
            )

    if st.session_state.saved_message:
        st.success(st.session_state.saved_message)

    st.divider()
    st.header("Current Reading Summary")

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric("Temperature", f"{temperature:.1f} °C")
    metric2.metric("Moisture", f"{moisture:.1f}%")
    metric3.metric("Energy", f"{energy:.1f} kWh")
    metric4.metric("Mode", mode)

    st.subheader("Rule-Based Alerts")

    alerts = []

    if temperature > temp_limit:
        alerts.append(
            f"Temperature is above the example threshold of "
            f"{temp_limit:.1f} °C."
        )

    if moisture > moisture_limit:
        alerts.append(
            f"Moisture is above the example threshold of "
            f"{moisture_limit:.1f}%."
        )

    if energy > energy_limit:
        alerts.append(
            f"Energy consumption is above the example threshold of "
            f"{energy_limit:.1f} kWh."
        )

    if mode == "Stopped":
        st.info("The selected operating mode is Stopped.")
    elif mode == "Maintenance":
        st.info("The selected operating mode is Maintenance.")
    elif mode == "Starting":
        st.info("Starting mode selected. Follow the approved start-up procedure.")
    elif mode == "Cooling":
        st.info("Cooling mode selected. Follow the approved cooling procedure.")

    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success(
            "No example threshold alerts from the values entered."
        )

    st.subheader("Suggested Checks")

    if temperature > temp_limit:
        st.write(
            "- Verify the reading and follow the approved temperature "
            "response procedure."
        )

    if moisture > moisture_limit:
        st.write(
            "- Check the moisture measurement, incoming material and "
            "drying conditions."
        )

    if energy > energy_limit:
        st.write(
            "- Review energy readings, load conditions and equipment "
            "performance."
        )

    if not alerts:
        st.write(
            "- Continue routine inspections and record any unusual "
            "noise, vibration, smoke or material changes."
        )

    st.caption(
        "These alerts are illustrative only. Use the manufacturer's "
        "limits and your site's approved operating procedures."
    )


# ============================================================
# OPERATING HISTORY
# ============================================================

elif page == "Operating History":

    st.header("Operating History")

    if history.empty:
        st.info(
            "No operating records yet. Save a reading from the Dashboard "
            "to start building your history."
        )

    else:
        history_display = history.copy()

        history_display["Timestamp"] = pd.to_datetime(
            history_display["Timestamp"], errors="coerce"
        )

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "From date",
                value=date.today() - timedelta(days=30),
            )

        with col2:
            end_date = st.date_input(
                "To date",
                value=date.today(),
            )

        filtered = history_display[
            history_display["Timestamp"].notna()
            & (
                history_display["Timestamp"].dt.date
                >= start_date
            )
            & (
                history_display["Timestamp"].dt.date
                <= end_date
            )
        ].copy()

        st.metric("Records in selected period", len(filtered))

        st.dataframe(
            filtered.sort_values("Timestamp", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        if not filtered.empty:
            chart_data = filtered.sort_values("Timestamp").set_index(
                "Timestamp"
            )

            st.subheader("Temperature Trend")
            st.line_chart(chart_data["Temperature_C"])

            st.subheader("Moisture Trend")
            st.line_chart(chart_data["Moisture_Percent"])

            st.subheader("Energy Trend")
            st.line_chart(chart_data["Energy_kWh"])

            st.subheader("Average Readings")

            avg1, avg2, avg3 = st.columns(3)

            avg1.metric(
                "Average temperature",
                f"{filtered['Temperature_C'].mean():.1f} °C",
            )

            avg2.metric(
                "Average moisture",
                f"{filtered['Moisture_Percent'].mean():.1f}%",
            )

            avg3.metric(
                "Average energy",
                f"{filtered['Energy_kWh'].mean():.1f} kWh",
            )


# ============================================================
# MAINTENANCE MANAGEMENT
# ============================================================

elif page == "Maintenance":

    st.header("Maintenance Management")

    with st.form("maintenance_form", clear_on_submit=True):

        equipment = st.text_input(
            "Equipment or component",
            placeholder="e.g. Rotary dryer, blower, auger",
        )

        issue = st.text_area(
            "Fault or maintenance requirement",
            placeholder="Describe the fault or service requirement",
        )

        action_taken = st.text_area(
            "Action taken or planned",
            placeholder="Inspection, cleaning, repair or replacement",
        )

        responsible = st.text_input("Responsible person")

        due_date = st.date_input(
            "Due date",
            value=date.today() + timedelta(days=7),
        )

        status = st.selectbox(
            "Status",
            ["Open", "In Progress", "Completed", "Cancelled"],
        )

        maintenance_submitted = st.form_submit_button(
            "Save Maintenance Record",
            type="primary",
            use_container_width=True,
        )

        if maintenance_submitted:

            if not equipment.strip() or not issue.strip():
                st.error(
                    "Enter both the equipment name and the issue."
                )

            else:
                new_maintenance = pd.DataFrame(
                    [
                        {
                            "Date_Logged": date.today().isoformat(),
                            "Equipment": equipment.strip(),
                            "Issue": issue.strip(),
                            "Action_Taken": action_taken.strip(),
                            "Responsible_Person": responsible.strip(),
                            "Due_Date": due_date.isoformat(),
                            "Status": status,
                        }
                    ]
                )

                maintenance = pd.concat(
                    [maintenance, new_maintenance],
                    ignore_index=True,
                )

                save_csv(maintenance, MAINTENANCE_FILE)
                st.success("Maintenance record saved.")

    st.divider()
    st.subheader("Maintenance Register")

    if maintenance.empty:
        st.info("No maintenance records have been entered yet.")

    else:
        maintenance_display = maintenance.copy()

        maintenance_display["Status"] = maintenance_display.apply(
            lambda row: maintenance_status(
                row["Due_Date"], row["Status"]
            ),
            axis=1,
        )

        overdue_count = (
            maintenance_display["Status"] == "Overdue"
        ).sum()

        open_count = maintenance_display["Status"].isin(
            ["Open", "In Progress", "Overdue"]
        ).sum()

        m1, m2, m3 = st.columns(3)

        m1.metric("Total tasks", len(maintenance_display))
        m2.metric("Open tasks", int(open_count))
        m3.metric("Overdue tasks", int(overdue_count))

        st.dataframe(
            maintenance_display.sort_values(
                "Due_Date", ascending=True
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "To update a task's status, edit its record in "
            "dryerwise_maintenance.csv and refresh the app."
        )


# ============================================================
# REPORTS AND EXPORT
# ============================================================

elif page == "Reports & Export":

    st.header("Reports & Export")

    history = load_csv(HISTORY_FILE, HISTORY_COLUMNS)
    maintenance = load_csv(
        MAINTENANCE_FILE, MAINTENANCE_COLUMNS
    )

    report1, report2 = st.columns(2)

    with report1:
        st.subheader("Operating Records")
        st.metric("Total saved readings", len(history))

        if not history.empty:
            st.download_button(
                "Download Operating History (CSV)",
                data=history.to_csv(index=False).encode("utf-8"),
                file_name="dryerwise_history.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with report2:
        st.subheader("Maintenance Records")
        st.metric("Total maintenance tasks", len(maintenance))

        if not maintenance.empty:
            st.download_button(
                "Download Maintenance Register (CSV)",
                data=maintenance.to_csv(index=False).encode("utf-8"),
                file_name="dryerwise_maintenance.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.divider()
    st.subheader("Excel Workbook")

    st.write(
        "Export operating history and maintenance records into "
        "one Excel workbook with separate worksheets."
    )

    try:
        excel_data = make_excel(history, maintenance)

        st.download_button(
            "Download Complete Excel Report",
            data=excel_data,
            file_name="DryerWise_AI_Report.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    except (ImportError, ModuleNotFoundError):
        st.error(
            "Excel export requires openpyxl. Install it with: "
            "python -m pip install openpyxl"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "DryerWise AI | Local demonstration prototype | "
    "Not connected to plant sensors or control systems. "
    "Do not use demonstration thresholds as safety limits."
)
