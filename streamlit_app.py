import sys
print(f"Streamlit's Python executable: {sys.executable}")
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from streamlit_authenticator import Authenticate  #pip install streamlit-authenticator
import yaml
from yaml.loader import SafeLoader

# --- Configuration ---
APP_TITLE = "ISO 27001 & ISO 27002 Audit App"
AUDIT_LOG_DIR = "audit_logs"
if not os.path.exists(AUDIT_LOG_DIR):
    os.makedirs(AUDIT_LOG_DIR)

# --- Data ---

# Placeholder ISO 27001 controls (can be extended/loaded from file)
ISO_27001_CONTROLS = [
    ("A.5.1", "Policies for information security", "Information security policies should be defined and approved by management."),
    ("A.5.2", "Information security roles and responsibilities", "Information security roles and responsibilities should be defined and allocated."),
    ("A.5.3", "Segregation of duties", "Conflicting duties and areas of responsibility should be segregated."),
    ("A.5.4", "Contact with authorities", "Contact with relevant authorities should be maintained."),
    ("A.5.5", "Contact with special interest groups", "Contact with special interest groups should be maintained."),
    # Add more controls here...
    ("A.18.1", "Compliance with legal and contractual requirements", "All relevant statutory, regulatory and contractual requirements should be identified and documented."),
]

# Placeholder ISO 27002 controls (can be extended/loaded from file)
ISO_27002_CONTROLS = [
    ("5.1", "Policies for information security", "Information security policies should be defined and approved by management."),
    ("5.2", "Information security roles and responsibilities", "Information security roles and responsibilities should be defined and allocated."),
    ("5.3", "Segregation of duties", "Conflicting duties and areas of responsibility should be segregated."),
    ("5.4", "Contact with authorities", "Contact with relevant authorities should be maintained."),
    ("5.5", "Contact with special interest groups", "Contact with relevant authorities should be maintained."),
    # Add more controls here...
    ("18.1", "Compliance with legal and contractual requirements", "All relevant statutory, regulatory and contractual requirements should be identified and documented."),
]


# --- Helper Functions ---

def save_audit_log(audit_data, organization_name):
    """Saves the audit data to a CSV file."""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"{AUDIT_LOG_DIR}/{organization_name}_audit_{timestamp}.csv"

    # Check if file exists, if so, rename it (basic version control)
    if os.path.exists(filename):
        old_filename = filename.replace(".csv", f"_v{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        os.rename(filename, old_filename)
        st.info(f"Previous version saved as: {old_filename}")

    df = pd.DataFrame(audit_data)
    df.to_csv(filename, index=False)
    st.success(f"Audit log saved to: {filename}")


def generate_report(audit_data, organization_name):
    """Generates a detailed report from the audit data with charts and gap analysis."""
    st.subheader("Audit Report")
    st.write(f"Organization: {organization_name}")
    st.write("Date: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    df = pd.DataFrame(audit_data)
    st.dataframe(df)

    # Compliance Chart
    compliance_counts = df['Compliance'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(compliance_counts, labels=compliance_counts.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    st.pyplot(fig)  # Display the Matplotlib figure in Streamlit

    # Calculate compliance percentages (example)
    implemented_count = df[df['Compliance'] == 'Yes'].shape[0]
    total_controls = df.shape[0]
    compliance_percentage = (implemented_count / total_controls) * 100 if total_controls > 0 else 0
    st.write(f"Overall Compliance: {compliance_percentage:.2f}%")

    # Gap Analysis
    st.subheader("Gap Analysis")
    gaps = df[df['Compliance'] == 'No']
    if not gaps.empty:
        st.write("The following controls are not implemented:")
        for index, row in gaps.iterrows():
            st.write(f"- **{row['Standard']} - {row['Control ID']}:** {row['Control Name']}")
    else:
        st.write("No gaps found (all controls implemented).")


def conduct_audit(controls_list, standard_name, organization_name):
    """Conducts the audit for a given standard and returns the audit data."""
    audit_data = []
    for control_id, control_name, control_description in controls_list:
        st.subheader(f"{standard_name}: Control {control_id}")
        st.write(f"**Name:** {control_name}")
        st.write(f"**Description:** {control_description}")

        compliance = st.radio(f"Is this control implemented? (Control {control_id})", options=["Yes", "No", "Partially Implemented"], horizontal=True)

        risk_level = st.selectbox(f"Risk Level for Control {control_id}:", options=["Low", "Medium", "High"])  # Risk Assessment

        evidence = st.text_area(f"Evidence/Remarks for Control {control_id}:", "")

        remediation_plan = st.text_area(f"Remediation Plan (if not fully implemented) for Control {control_id}:", "") #Remediation Plan

        audit_data.append({
            "Organization": organization_name,
            "Standard": standard_name,
            "Control ID": control_id,
            "Control Name": control_name,
            "Compliance": compliance,
            "Risk Level": risk_level,
            "Evidence/Remarks": evidence,
            "Remediation Plan": remediation_plan,
            "Auditor": st.session_state.get("username", "N/A")
        })
        st.markdown("---")  # Separator

    return audit_data

# --- Main App ---
def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    organization_name = st.text_input("Organization Name:", "Example Organization")

    st.header("ISO 27001 Audit")
    audit_data_27001 = conduct_audit(ISO_27001_CONTROLS, "ISO 27001", organization_name)

    st.header("ISO 27002 Audit")
    audit_data_27002 = conduct_audit(ISO_27002_CONTROLS, "ISO 27002", organization_name)

    # Combine results if needed (optional)
    combined_audit_data = audit_data_27001 + audit_data_27002

    if st.button("Generate Report"):
        generate_report(combined_audit_data, organization_name)

    if st.button("Save Audit Log"):
        save_audit_log(combined_audit_data, organization_name)

# --- Sidebar ---
def sidebar():
    with st.sidebar:
        st.header("Settings")
        #auditor_name = st.text_input("Auditor Name:", "Enter Name")
        #st.session_state["auditor_name"] = auditor_name

        st.subheader("Guidance")
        st.markdown("""
        **Instructions:**

        1.  Enter the Organization Name.
        2.  For each control, read the description and determine the level of compliance (Yes, No, Partially Implemented).
        3.  Provide evidence or remarks to support your assessment.
        4.  Click "Generate Report" to view a summary of the audit.
        5.  Click "Save Audit Log" to save the data as a CSV file.

        **Note:** This is a basic application and can be extended with more features, such as:

        *   Importing controls from a file (CSV, Excel).
        *   Generating detailed reports (PDF).
        *   Adding user authentication.
        *   Calculating risk scores.
        *   Integration with other systems.
        """)