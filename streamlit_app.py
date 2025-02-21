import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from streamlit_authenticator import Authenticate  # pip install streamlit-authenticator
import yaml
from yaml.loader import SafeLoader

# --- Configuration ---
APP_TITLE = "ISO 27001 & ISO 27002 Audit App"
AUDIT_LOG_DIR = "audit_logs"
if not os.path.exists(AUDIT_LOG_DIR):
    os.makedirs(AUDIT_LOG_DIR)

# --- Data ---
ISO_27001_CONTROLS = [
    ("A.5.1", "Policies for information security", "Information security policies should be defined and approved by management."),
    ("A.5.2", "Information security roles and responsibilities", "Information security roles and responsibilities should be defined and allocated."),
    ("A.5.3", "Segregation of duties", "Conflicting duties and areas of responsibility should be segregated."),
    ("A.5.4", "Contact with authorities", "Contact with relevant authorities should be maintained."),
    ("A.5.5", "Contact with special interest groups", "Contact with special interest groups should be maintained."),
    ("A.18.1", "Compliance with legal and contractual requirements", "All relevant statutory, regulatory and contractual requirements should be identified and documented."),
]

ISO_27002_CONTROLS = [
    ("5.1", "Policies for information security", "Information security policies should be defined and approved by management."),
    ("5.2", "Information security roles and responsibilities", "Information security roles and responsibilities should be defined and allocated."),
    ("5.3", "Segregation of duties", "Conflicting duties and areas of responsibility should be segregated."),
    ("5.4", "Contact with authorities", "Contact with relevant authorities should be maintained."),
    ("5.5", "Contact with special interest groups", "Contact with special interest groups should be maintained."),
    ("18.1", "Compliance with legal and contractual requirements", "All relevant statutory, regulatory and contractual requirements should be identified and documented."),
]


# --- Helper Functions ---

def load_audit_data(filename):
    """Loads audit data from a CSV file, handling potential format changes."""
    try:
        df = pd.read_csv(filename)
        # Check if the file has the expected columns for the new format
        expected_columns = ["Organization", "Standard", "Control ID", "Control Name", "Compliance", "Risk Level",
                            "Evidence/Remarks", "Remediation Plan", "Auditor"]
        if all(col in df.columns for col in expected_columns):
            # It's the new format, no conversion needed
            return df
        else:
            # It's the old format, needs conversion
            print("Detected old CSV format.  Converting...")

            # Adapt column names and add missing columns
            # Adapt these renames to match your ACTUAL old column names
            column_mapping = {
                "Organization": "Organization",  # These should be changed!
                "Standard": "Standard",
                "Control ID": "Control ID",
                "Control Name": "Control Name",
                "Compliance": "Compliance",
                "Evidence/Remarks": "Evidence/Remarks",
                "Auditor": "Auditor",  # Example remap
                # Add more mappings as needed based on old CSV format!
            }
            df.rename(columns=column_mapping, inplace=True)

            # Add missing columns with default values
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = ""  # Or some appropriate default value

            df = df[expected_columns]  # Ensure right column order.
            return df
    except pd.errors.ParserError as e:
        print(f"Error parsing CSV: {e}")
        st.error(
            f"Error parsing CSV file: {filename}.  Check the file format.  Error was: {e}")  # Streamlit warning.
        return None  # Indicate failure.
    except FileNotFoundError:
        print(f"File not found: {filename}")
        st.error(f"Audit log file not found: {filename}")
        return None


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
    if df.empty:
        st.warning("No audit data available to generate the report.")
        return  # Exit if no data is available

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


def conduct_audit(controls_list, standard_name, organization_name, loaded_data=None):  # Added loaded_data
    """Conducts the audit for a given standard and returns the audit data."""
    audit_data = []
    for control_id, control_name, control_description in controls_list:
        st.subheader(f"{standard_name}: Control {control_id}")
        st.write(f"**Name:** {control_name}")
        st.write(f"**Description:** {control_description}")

        # Check if there's previously loaded data for this control
        default_compliance = ""
        default_risk_level = "Low"  # Default risk level
        default_evidence = ""
        default_remediation = ""

        if loaded_data is not None:
            # Try to find the matching row in the loaded data
            matching_row = loaded_data[
                (loaded_data['Control ID'] == control_id) & (loaded_data['Standard'] == standard_name)]
            if not matching_row.empty:
                # Use the loaded data as default values
                default_compliance = matching_row.iloc[0]['Compliance']
                default_risk_level = matching_row.iloc[0]['Risk Level']
                default_evidence = matching_row.iloc[0]['Evidence/Remarks']
                default_remediation = matching_row.iloc[0]['Remediation Plan']

        compliance = st.radio(f"Is this control implemented? (Control {control_id})",
                              options=["Yes", "No", "Partially Implemented"], horizontal=True,
                              index=["Yes", "No", "Partially Implemented"].index(
                                  default_compliance) if default_compliance else 0) #Set default

        risk_level = st.selectbox(f"Risk Level for Control {control_id}:", options=["Low", "Medium", "High"],
                                  index=["Low", "Medium", "High"].index(
                                      default_risk_level) if default_risk_level else 0)  # Risk Assessment, Set default

        evidence = st.text_area(f"Evidence/Remarks for Control {control_id}:", value=default_evidence)

        remediation_plan = st.text_area(f"Remediation Plan (if not fully implemented) for Control {control_id}:",
                                       value=default_remediation)  # Remediation Plan

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
    st.session_state["organization_name"] = organization_name  # Store organization name

    # Load audit data based on the stored organization name.
    filename_27001 = f"{AUDIT_LOG_DIR}/{st.session_state['organization_name']}_audit_27001_{datetime.now().strftime('%Y%m%d')}.csv"
    loaded_data_27001 = load_audit_data(filename_27001)
    filename_27002 = f"{AUDIT_LOG_DIR}/{st.session_state['organization_name']}_audit_27002_{datetime.now().strftime('%Y%m%d')}.csv"
    loaded_data_27002 = load_audit_data(filename_27002)

    st.header("ISO 27001 Audit")
    audit_data_27001 = conduct_audit(ISO_27001_CONTROLS, "ISO 27001", organization_name,
                                      loaded_data_27001)  # Pass loaded data
    st.header("ISO 27002 Audit")
    audit_data_27002 = conduct_audit(ISO_27002_CONTROLS, "ISO 27002", organization_name,
                                      loaded_data_27002)  # Pass loaded data

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


# --- Authentication ---
def authentication():
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status:
        authenticator.logout('Logout', 'sidebar')
        st.session_state["username"] = name  # Store username in session state
        st.sidebar.write(f'Welcome *{name}*')
        return True  # Authentication successful
    elif authentication_status == False:
        st.error('Username/password is incorrect')
        return False
    elif authentication_status == None:
        st.warning('Please enter username and password')
        return False

    return False  # Authentication failed

# --- Main Execution ---
if __name__ == "__main__":
    if 'organization_name' not in st.session_state: # Add this to initialize organization_name at the beginning of your script
        st.session_state['organization_name'] = "Example Organization"

    if authentication():  # Only run the app if authenticated
        sidebar()
        main()
    else:
        st.warning("Please log in to continue.")