import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
from google import genai
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Central Risk Incident Register",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)


if "view_table_reset" not in st.session_state:
    st.session_state["view_table_reset"] = 0

if "preserved_edits" not in st.session_state:
    st.session_state["preserved_edits"] = None

# ============================================================
# OCBC COLOURS
# ============================================================

OCBC_RED = "#E31837"
OCBC_DARK_RED = "#B5122B"
OCBC_LIGHT_RED = "#FDECEF"

WHITE = "#FFFFFF"
LIGHT_GREY = "#F5F5F5"
DARK_GREY = "#333333"
BLUE = "#0755A5"


# ============================================================
# FILE LOCATIONS
# ============================================================

DATA_FOLDER = Path("data")
ATTACHMENT_FOLDER = Path("attachments")

DATA_FOLDER.mkdir(exist_ok=True)
ATTACHMENT_FOLDER.mkdir(exist_ok=True)

DATA_FILE = DATA_FOLDER / "risk_incident_register.csv"


# ============================================================
# DATABASE COLUMNS
# ============================================================

# COLUMNS = [
#     "Risk Incident ID",
#     "Risk Title",
#     "Risk Description",
#     "Source of Register",
#     "Severity",
#     "Financial Impact",
#     "Date & Time of Creation",
#     "Status",
#     "Potential Breach",
#     "Breach PIC",
#     "Policies / Regulations Breached",
#     "ORE Reportability",
#     "ORE PIC",
#     "ORE Case ID",
#     "Attachments"
# ]

COLUMNS = [
    "Risk Incident ID",
    "Risk Title",
    "Risk Description",
    "Source of Register",
    "Severity",
    "Financial Impact",
    "Date & Time of Creation",

    # TCC-specific
    "TCC_System_Affected",
    "TCC_Downtime_Minutes",
    "TCC_Impact_Type",

    # SAAM-specific
    "SAAM_Staff_Name",
    "SAAM_Department",
    "SAAM_Anomaly_Type",

    # DLM-specific
    "DLM_Data_Type",
    "DLM_Destination_Channel",
    "DLM_Data_Classification",

    # ORE-specific
    "ORE_Process_Affected",
    "ORE_Root_Cause_Category",
    "ORE_Business_Unit",

    "Status",
    "Potential Breach",
    "Breach PIC",
    "Policies / Regulations Breached",
    "ORE Reportability",
    "ORE PIC",
    "ORE Case ID",
    "Attachments"
]


# ============================================================
# DROPDOWN OPTIONS
# ============================================================

SOURCE_OPTIONS = [
    "TCC",
    "SAAM",
    "DLM",
    "ORE"
]

SEVERITY_OPTIONS = [
    "Low",
    "Medium",
    "High"
]

FINANCIAL_OPTIONS = [
    "Low",
    "Medium",
    "High"
]

STATUS_OPTIONS = [
    "Open",
    "Under Investigation",
    "Pending Review",
    "Closed"
]

YES_NO_OPTIONS = [
    "Yes",
    "No"
]

TCC_SYSTEMS = ["Core Banking System", "Internet Banking", "Mobile App", "Payment Gateway", "Internal Email"]
TCC_IMPACT_TYPES = ["Full Outage", "Degraded Performance", "Intermittent Failure"]

SAAM_DEPARTMENTS = ["Retail Banking", "Treasury", "Operations", "IT", "Compliance"]
SAAM_ANOMALY_TYPES = ["Unusual Login Time", "Excessive Access Attempts", "Privileged Access Misuse", "Unusual Transaction Pattern"]

DLM_DATA_TYPES = ["Customer PII", "Account Numbers", "Internal Financial Data", "Credentials", "Confidential Documents"]
DLM_CHANNELS = ["Email (External)", "USB Storage", "Cloud Upload", "Printing", "Messaging App"]
DLM_CLASSIFICATIONS = ["Confidential", "Restricted", "Internal Use Only"]

ORE_PROCESSES = ["Loan Processing", "Customer Onboarding", "Payment Reconciliation", "Card Issuance", "KYC Review"]
ORE_ROOT_CAUSES = ["Human Error", "System Error", "Process Gap", "Third-Party Failure"]
ORE_BUSINESS_UNITS = ["Consumer Banking", "Corporate Banking", "Treasury", "Operations"]


# ============================================================
# HARD-CODED BREACH PIC DIRECTORY
# ============================================================

BREACH_PIC_DIRECTORY = {
    "Alice Tan": "alice.tan@example.com",
    "Benjamin Lim": "benjamin.lim@example.com",
    "Carol Wong": "carol.wong@example.com",
    "Daniel Lee": "daniel.lee@example.com",
    "Emily Ng": "emily.ng@example.com"
}


# ============================================================
# BREACH PIC DROPDOWN DISPLAY
# ============================================================

BREACH_PIC_OPTIONS = [
    f"{name} — {email}"
    for name, email in BREACH_PIC_DIRECTORY.items()
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_breach_pic_display(name):

    if not name:
        return ""

    name = str(name).strip()

    if name in BREACH_PIC_DIRECTORY:

        return (
            f"{name} - "
            f"{BREACH_PIC_DIRECTORY[name]}"
        )

    return name


def get_breach_pic_name(display_value):

    if not display_value:
        return ""

    display_value = str(display_value).strip()

    if " - " in display_value:

        return display_value.split(
            " - ",
            1
        )[0].strip()

    return display_value


def get_breach_pic_email(name):

    if not name:
        return ""

    return BREACH_PIC_DIRECTORY.get(
        str(name).strip(),
        ""
    )
def get_ai_breach_assessment(risk_title, risk_description, source, severity):

    prompt = f"""
You are assisting a bank's operational risk team in triaging a risk incident.
Analyze the incident below and respond in EXACTLY this plain text format,
with each field on its own line, no markdown, no extra commentary:

Breach: Yes or No
Confidence: Low or Medium or High
Reasoning: 1-2 sentence explanation
Policies: short bullet-style list of relevant policy/regulation areas, or leave blank if none apply

Incident details:
- Source: {source}
- Severity: {severity}
- Title: {risk_title}
- Description: {risk_description}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        text = response.text.strip()

        return parse_ai_assessment(text)

    except Exception as e:
        return {
            "suggested_potential_breach": "No",
            "confidence": "Low",
            "reasoning": f"AI assessment unavailable: {e}",
            "suggested_policies": ""
        }

def parse_ai_assessment(text):

    result = {
        "suggested_potential_breach": "No",
        "confidence": "Low",
        "reasoning": "",
        "suggested_policies": ""
    }

    current_field = None
    policy_lines = []

    for line in text.splitlines():

        stripped = line.strip()

        if not stripped:
            continue

        lower = stripped.lower()

        if lower.startswith("breach:"):
            result["suggested_potential_breach"] = stripped.split(":", 1)[1].strip()
            current_field = None

        elif lower.startswith("confidence:"):
            result["confidence"] = stripped.split(":", 1)[1].strip()
            current_field = None

        elif lower.startswith("reasoning:"):
            result["reasoning"] = stripped.split(":", 1)[1].strip()
            current_field = None

        elif lower.startswith("policies:"):
            first_line = stripped.split(":", 1)[1].strip()
            if first_line:
                policy_lines.append(first_line)
            current_field = "policies"

        elif current_field == "policies":
            # Catches multi-line bullet lists that continue after "Policies:"
            policy_lines.append(stripped)

    result["suggested_policies"] = "\n".join(policy_lines)

    return result

# ============================================================
# INCIDENT DETAIL POPUP
# ============================================================

@st.dialog("Incident Details", width="large")
def show_incident_details(detail_row):

    incident_id = detail_row["Risk Incident ID"]
    source_type = str(detail_row["Source of Register"]).strip()

    st.markdown(
        f"""
        <div class="breach-pic-box">
            <strong>Incident:</strong> {incident_id}<br>
            <strong>Source:</strong> {source_type}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"**Risk Title:** {detail_row['Risk Title']}")
    st.markdown(f"**Description:** {detail_row['Risk Description']}")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Severity:** {detail_row['Severity']}")
    c2.markdown(f"**Financial Impact:** {detail_row['Financial Impact']}")
    c3.markdown(f"**Created:** {detail_row['Date & Time of Creation']}")

    st.markdown("---")
    st.markdown(f"**{source_type} Specific Details**")

    col1, col2, col3 = st.columns(3)

    if source_type == "TCC":
        col1.metric("System Affected", detail_row["TCC_System_Affected"] or "-")
        col2.metric("Downtime (min)", detail_row["TCC_Downtime_Minutes"] or "-")
        col3.metric("Impact Type", detail_row["TCC_Impact_Type"] or "-")

    elif source_type == "SAAM":
        col1.metric("Staff Name / ID", detail_row["SAAM_Staff_Name"] or "-")
        col2.metric("Department", detail_row["SAAM_Department"] or "-")
        col3.metric("Anomaly Type", detail_row["SAAM_Anomaly_Type"] or "-")

    elif source_type == "DLM":
        col1.metric("Data Type", detail_row["DLM_Data_Type"] or "-")
        col2.metric("Destination / Channel", detail_row["DLM_Destination_Channel"] or "-")
        col3.metric("Data Classification", detail_row["DLM_Data_Classification"] or "-")

    elif source_type == "ORE":
        col1.metric("Process Affected", detail_row["ORE_Process_Affected"] or "-")
        col2.metric("Root Cause Category", detail_row["ORE_Root_Cause_Category"] or "-")
        col3.metric("Business Unit", detail_row["ORE_Business_Unit"] or "-")

    if detail_row["Attachments"]:
        st.markdown("---")
        st.caption(f"📎 Attachments: {detail_row['Attachments']}")

    st.markdown("---")

    if st.button("Close", use_container_width=True):
        st.session_state["view_table_reset"] += 1
        st.rerun()


# ============================================================
# EMAIL DRAFT GENERATOR
# ============================================================

def generate_email_draft(
    incident_id,
    risk_title,
    risk_description,
    source,
    severity,
    financial_impact,
    potential_breach,
    breach_pic_name,
    breach_pic_email,
    policies_breached,
    attachments
):

    # --------------------------------------------------------
    # ATTACHMENT SECTION
    # --------------------------------------------------------

    if attachments:

        attachment_list = [
            item.strip()
            for item in str(attachments).split(";")
            if item.strip()
        ]

        if attachment_list:

            attachment_text = "\n".join(
                f"• {item}"
                for item in attachment_list
            )

        else:

            attachment_text = "No attachments recorded."

    else:

        attachment_text = "No attachments recorded."


    # --------------------------------------------------------
    # POLICY SECTION
    # --------------------------------------------------------

    if policies_breached.strip():

        policy_text = policies_breached.strip()

    else:

        policy_text = (
            "[To be completed by the assigned "
            "Breach PIC]"
        )


    # --------------------------------------------------------
    # PIC
    # --------------------------------------------------------

    if breach_pic_name:

        pic_name = breach_pic_name

    else:

        pic_name = "[Breach PIC to be assigned]"


    if breach_pic_email:

        pic_email = breach_pic_email

    else:

        pic_email = "[Email not available]"


    # --------------------------------------------------------
    # EMAIL SUBJECT
    # --------------------------------------------------------

    subject = (
        f"Potential Breach Review Required - "
        f"{incident_id} - {risk_title}"
    )


    # --------------------------------------------------------
    # EMAIL BODY
    # --------------------------------------------------------

    body = f"""To: {pic_name} <{pic_email}>

Subject: {subject}


Dear {pic_name},

A potential breach has been identified in the Central Risk Incident Register.

Please review the incident details below and assess the applicable policies, regulations, procedures, or requirements that may have been breached.


============================================================
RISK INCIDENT DETAILS
============================================================

Risk Incident ID:
{incident_id}

Risk Title:
{risk_title}

Risk Description:
{risk_description}

Source of Register:
{source}

Severity:
{severity}

Financial Impact:
{financial_impact}

Potential Breach:
{potential_breach}


============================================================
POLICIES / REGULATIONS BREACHED
============================================================

{policy_text}


Please identify the relevant policy, regulation, procedure, guideline, or other applicable requirement that may have been breached.

Where applicable, please include:

• Policy / regulation name
• Relevant section / clause
• Description of the requirement
• How the incident may have breached the requirement
• Any further action or investigation required


============================================================
ATTACHMENTS
============================================================

{attachment_text}


Please review the above incident and provide your assessment accordingly.

Thank you.

Regards,
Central Risk Incident Register
"""


    return subject, body


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
<style>

.stApp {{
    background-color: {WHITE};
}}

.main .block-container {{
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 100%;
}}


/* ============================================================
   MAIN HEADER
   ============================================================ */

.main-header {{
    background-color: {OCBC_RED};
    padding: 22px 30px;
    border-radius: 8px;
    margin-bottom: 25px;
}}

.main-header h1 {{
    color: white;
    margin: 0;
    font-size: 30px;
    font-weight: 700;
}}

.main-header p {{
    color: white;
    margin: 6px 0 0 0;
    font-size: 15px;
}}


/* ============================================================
   SECTION HEADER
   ============================================================ */

.section-header {{
    background-color: {OCBC_RED};
    color: white;
    padding: 13px 18px;
    border-radius: 7px;
    font-size: 18px;
    font-weight: 700;
    margin-top: 20px;
    margin-bottom: 18px;
}}


/* ============================================================
   KPI CARDS
   ============================================================ */

.metric-card {{
    background-color: {LIGHT_GREY};
    border-left: 5px solid {OCBC_RED};
    padding: 18px;
    border-radius: 0 8px 8px 0;
    min-height: 95px;
    text-align: center;
}}

.metric-value {{
    font-size: 28px;
    font-weight: bold;
    color: {OCBC_RED};
}}

.metric-label {{
    font-size: 13px;
    color: {DARK_GREY};
    margin-top: 5px;
}}


/* ============================================================
   INFO BOX
   ============================================================ */

.info-box {{
    background-color: #EAF2FF;
    padding: 15px 18px;
    border-radius: 8px;
    color: {BLUE};
    margin-bottom: 20px;
}}


/* ============================================================
   EDIT NOTE
   ============================================================ */

.edit-note {{
    background-color: {OCBC_LIGHT_RED};
    border-left: 5px solid {OCBC_RED};
    padding: 14px 18px;
    border-radius: 6px;
    margin-bottom: 18px;
    color: {DARK_GREY};
}}


/* ============================================================
   BREACH PIC BOX
   ============================================================ */

.breach-pic-box {{
    background-color: {OCBC_LIGHT_RED};
    border-left: 5px solid {OCBC_RED};
    padding: 16px 20px;
    border-radius: 7px;
    margin-top: 10px;
    margin-bottom: 20px;
}}


/* ============================================================
   EMAIL DRAFT BOX
   ============================================================ */

.email-draft-box {{
    background-color: #F8F9FA;
    border: 1px solid #D9D9D9;
    border-left: 5px solid {OCBC_RED};
    padding: 18px 22px;
    border-radius: 7px;
    margin-top: 15px;
    margin-bottom: 20px;
}}

.email-draft-title {{
    font-size: 18px;
    font-weight: 700;
    color: {OCBC_RED};
    margin-bottom: 8px;
}}


/* ============================================================
   BUTTON
   ============================================================ */

.stButton > button {{
    background-color: {OCBC_RED};
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
}}

.stButton > button:hover {{
    background-color: {OCBC_DARK_RED};
    color: white;
}}


/* ============================================================
   SIDEBAR
   ============================================================ */

section[data-testid="stSidebar"] {{
    background-color: {LIGHT_GREY};
}}


/* ============================================================
   DATA EDITOR
   ============================================================ */

[data-testid="stDataEditor"] {{
    border: 1px solid #DDDDDD;
    border-radius: 8px;
}}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not DATA_FILE.exists():

        return pd.DataFrame(
            columns=COLUMNS
        )

    try:

        df = pd.read_csv(
            DATA_FILE,
            dtype=str,
            keep_default_na=False
        )

    except Exception as e:

        st.error(
            f"Unable to read CSV file: {e}"
        )

        return pd.DataFrame(
            columns=COLUMNS
        )

    # Make sure all columns exist
    for column in COLUMNS:

        if column not in df.columns:

            df[column] = ""

    # Correct column order
    df = df[COLUMNS].copy()

    # Replace NaN
    df = df.fillna("")

    # Force all fields to text
    for column in COLUMNS:

        df[column] = (
            df[column]
            .astype(str)
        )

    return df


# ============================================================
# SAVE DATA
# ============================================================

def save_data(df):

    df = df.copy()

    df = df.fillna("")

    for column in COLUMNS:

        df[column] = (
            df[column]
            .astype(str)
        )

    df.to_csv(
        DATA_FILE,
        index=False
    )


# ============================================================
# GENERATE INCIDENT ID
# ============================================================

def generate_incident_id():

    date_part = datetime.now().strftime(
        "%Y%m%d"
    )

    random_part = uuid.uuid4().hex[:6].upper()

    return (
        f"RI-{date_part}-{random_part}"
    )


# ============================================================
# LOAD DATABASE
# ============================================================

df = load_data()


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="main-header">
        <h1>Central Risk Incident Register</h1>
        <p>Consolidated Risk Incident Monitoring Dashboard</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🔴 Risk Incident Register"
    )

    st.markdown("---")

    st.markdown(
        "### Navigation"
    )

    page = st.radio(
    "Select module",
    [
        "Dashboard",
        "Create Risk Incident",
        "Breach & ORE Statistics"
    ]
)

    st.markdown("---")

    st.markdown(
        "### Business Units"
    )

    st.markdown(
        """
        **TCC**  
        Technology Command Centre

        **SAAM**  
        Staff Anomaly Activity Monitoring

        **DLM**  
        Data Loss Monitoring

        **ORE**  
        Operational Risk Events
        """
    )

    st.markdown("---")

    st.caption(
        "Central Risk Incident Register v1.0"
    )


# ============================================================
# CREATE RISK INCIDENT
# ============================================================

if page == "Create Risk Incident":

    st.markdown(
        """
        <div class="section-header">
            Create New Risk Incident
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="info-box">
            <strong>System generated fields:</strong><br>
            Risk Incident ID and Date & Time of Creation
            will be automatically generated by the system.
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # AUTO GENERATED FIELDS
    # ========================================================

    incident_id = generate_incident_id()

    creation_datetime = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.text_input(
            "Risk Incident ID",
            value=incident_id,
            disabled=True
        )

    with col2:

        st.text_input(
            "Date & Time of Creation",
            value=creation_datetime,
            disabled=True
        )


    # ========================================================
    # INCIDENT DETAILS
    # ========================================================

    st.markdown(
        """
        <div class="section-header">
            Incident Details
        </div>
        """,
        unsafe_allow_html=True
    )


    risk_title = st.text_input(
        "Risk Title *",
        placeholder=(
            "Enter a short title for the risk incident"
        )
    )


    risk_description = st.text_area(
        "Risk Description *",
        placeholder=(
            "Provide a detailed description "
            "of the risk incident..."
        ),
        height=160
    )


    col1, col2 = st.columns(2)

    with col1:
        source = st.selectbox(
            "Source of Register *",
            SOURCE_OPTIONS
        )

    with col2:
        severity = st.selectbox(
            "Severity *",
            SEVERITY_OPTIONS
        )

    financial_impact = st.selectbox(
        "Financial Impact *",
        FINANCIAL_OPTIONS
    )

    # ========================================================
    # AI BREACH ASSESSMENT (SUGGESTION ONLY)
    # ========================================================

    st.markdown(
        """
        <div class="section-header">
            AI Breach Assessment (Suggestion)
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption(
        "Optional: get an AI-generated first pass on whether this "
        "incident may constitute a breach. This does not save "
        "anything automatically - review and confirm manually."
    )

    if st.button("Get AI Suggestion", key="ai_suggest_create"):

        if not risk_title.strip() or not risk_description.strip():
            st.warning("Enter a Risk Title and Description first.")
        else:
            with st.spinner("Analyzing incident..."):
                ai_result = get_ai_breach_assessment(
                    risk_title, risk_description, source, severity
                )

            st.markdown(
                f"""
                <div class="breach-pic-box">
                    <strong>Suggested Potential Breach:</strong> {ai_result['suggested_potential_breach']}
                    &nbsp;|&nbsp; <strong>Confidence:</strong> {ai_result['confidence']}<br><br>
                    <strong>Reasoning:</strong> {ai_result['reasoning']}<br><br>
                    <strong>Possible relevant policies:</strong><br>
                    {ai_result['suggested_policies'] or 'None suggested'}
                </div>
                """,
                unsafe_allow_html=True
            )


    # ========================================================
    # ATTACHMENTS
    # ========================================================

    st.markdown(
        """
        <div class="section-header">
            Attachments
        </div>
        """,
        unsafe_allow_html=True
    )


    uploaded_files = st.file_uploader(
        "Upload supporting documents",
        type=[
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx"
        ],
        accept_multiple_files=True
    )


    # ========================================================
    # CREATE BUTTON
    # ========================================================

    st.markdown("---")

    if st.button(
        "➕ Create Risk Incident",
        use_container_width=True
    ):

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not risk_title.strip():

            st.error(
                "Please enter the Risk Title."
            )

        elif not risk_description.strip():

            st.error(
                "Please enter the Risk Description."
            )

        else:

            # ------------------------------------------------
            # SAVE ATTACHMENTS
            # ------------------------------------------------

            attachment_names = []

            if uploaded_files:

                for uploaded_file in uploaded_files:

                    filename = (
                        f"{incident_id}_"
                        f"{uploaded_file.name}"
                    )

                    filepath = (
                        ATTACHMENT_FOLDER /
                        filename
                    )

                    with open(
                        filepath,
                        "wb"
                    ) as f:

                        f.write(
                            uploaded_file.getbuffer()
                        )

                    attachment_names.append(
                        filename
                    )


            # ------------------------------------------------
            # CREATE INCIDENT
            # ------------------------------------------------

            new_incident = {

                "Risk Incident ID":
                    incident_id,

                "Risk Title":
                    risk_title.strip(),

                "Risk Description":
                    risk_description.strip(),

                "Source of Register":
                    source,

                "Severity":
                    severity,

                "Financial Impact":
                    financial_impact,

                "Date & Time of Creation":
                    creation_datetime,

                "Status":
                    "Open",

                "Potential Breach":
                    "",

                "Breach PIC":
                    "",

                "Policies / Regulations Breached":
                    "",

                "ORE Reportability":
                    "",

                "ORE PIC":
                    "",

                "ORE Case ID":
                    "",

                "Attachments":
                    "; ".join(
                        attachment_names
                    )
            }


            # ------------------------------------------------
            # ADD TO DATAFRAME
            # ------------------------------------------------

            new_row = pd.DataFrame(
                [new_incident],
                columns=COLUMNS
            )

            df = pd.concat(
                [
                    df,
                    new_row
                ],
                ignore_index=True
            )


            # ------------------------------------------------
            # SAVE
            # ------------------------------------------------

            save_data(df)


            st.success(
                f"Risk Incident {incident_id} "
                "has been successfully created."
            )


            if attachment_names:

                st.info(
                    f"{len(attachment_names)} "
                    "attachment(s) saved successfully."
                )


# ============================================================
# DASHBOARD
# ============================================================

elif page == "Dashboard":

    # ========================================================
    # DASHBOARD HEADER
    # ========================================================

    st.markdown(
        """
        <div class="section-header">
            Risk Incident Dashboard
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # KPI CALCULATIONS
    # ========================================================

    total_incidents = len(df)


    open_incidents = len(
        df[
            df["Status"]
            .str.strip()
            .str.lower()
            == "open"
        ]
    )


    potential_breaches = len(
        df[
            df["Potential Breach"]
            .str.strip()
            .str.lower()
            == "yes"
        ]
    )


    reportable_ore = len(
        df[
            df["ORE Reportability"]
            .str.strip()
            .str.lower()
            == "yes"
        ]
    )


    # ========================================================
    # KPI CARDS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">
                    {total_incidents}
                </div>
                <div class="metric-label">
                    Total Risk Incidents
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    with col2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">
                    {open_incidents}
                </div>
                <div class="metric-label">
                    Open Incidents
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    with col3:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">
                    {potential_breaches}
                </div>
                <div class="metric-label">
                    Potential Breaches
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    with col4:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">
                    {reportable_ore}
                </div>
                <div class="metric-label">
                    Reportable ORE
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # SOURCE / SEVERITY SUMMARY
    # ========================================================

    if len(df) > 0:

        st.markdown("---")

        chart_col1, chart_col2 = st.columns(2)


        with chart_col1:

            st.subheader(
                "Incidents by Source"
            )

            source_counts = (
                df[
                    "Source of Register"
                ]
                .value_counts()
            )

            st.bar_chart(
                source_counts
            )


        with chart_col2:

            st.subheader(
                "Incidents by Severity"
            )

            severity_counts = (
                df[
                    "Severity"
                ]
                .value_counts()
            )

            st.bar_chart(
                severity_counts
            )


    # ========================================================
    # FILTERS
    # ========================================================

    st.markdown("---")

    st.markdown(
        "### 🔎 Filter Risk Incidents"
    )


    filter1, filter2, filter3, filter4 = (
        st.columns(4)
    )


    with filter1:

        source_filter = st.multiselect(
            "Source of Register",
            SOURCE_OPTIONS
        )


    with filter2:

        severity_filter = st.multiselect(
            "Severity",
            SEVERITY_OPTIONS
        )


    with filter3:

        financial_filter = st.multiselect(
            "Financial Impact",
            FINANCIAL_OPTIONS
        )


    with filter4:

        breach_filter = st.multiselect(
            "Potential Breach",
            [
                "Yes",
                "No",
                "Not Assessed"
            ]
        )


    filter5, filter6 = st.columns(2)


    with filter5:

        ore_filter = st.multiselect(
            "ORE Reportability",
            [
                "Yes",
                "No",
                "Not Assessed"
            ]
        )


    with filter6:

        search = st.text_input(
            "Search",
            placeholder=(
                "Search incident ID, title, "
                "description, PIC or ORE Case ID"
            )
        )


    # ========================================================
    # APPLY FILTERS
    # ========================================================

    filtered_df = df.copy()


    if source_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Source of Register"
            ].isin(source_filter)
        ]


    if severity_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Severity"
            ].isin(severity_filter)
        ]


    if financial_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Financial Impact"
            ].isin(financial_filter)
        ]


    if breach_filter:

        temp = (
            filtered_df[
                "Potential Breach"
            ]
            .replace(
                "",
                "Not Assessed"
            )
        )

        filtered_df = filtered_df[
            temp.isin(breach_filter)
        ]


    if ore_filter:

        temp = (
            filtered_df[
                "ORE Reportability"
            ]
            .replace(
                "",
                "Not Assessed"
            )
        )

        filtered_df = filtered_df[
            temp.isin(ore_filter)
        ]


    if search.strip():

        search_value = (
            search
            .strip()
            .lower()
        )

        search_mask = filtered_df.apply(
            lambda row:
                row.astype(str)
                .str.lower()
                .str.contains(
                    search_value,
                    regex=False,
                    na=False
                )
                .any(),
            axis=1
        )

        filtered_df = filtered_df[
            search_mask
        ]


    # ========================================================
    # RECENT INCIDENTS
    # ========================================================

    st.markdown("---")

    st.markdown(
        """
        <div class="section-header">
            Recent Risk Incidents
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="edit-note">

        <strong>Editable fields:</strong>

        Status, Potential Breach, Breach PIC,
        ORE Reportability, ORE PIC and ORE Case ID.

        <br><br>

        <strong>Locked fields:</strong>

        Incident ID, Risk Title, Risk Description,
        Source, Severity, Financial Impact,
        Creation Date/Time and Attachments.

        <br><br>

        <strong>Potential Breach:</strong>

        Select <strong>Yes</strong> if the incident may
        constitute a breach. A Breach PIC can then be
        assigned and an email draft will automatically
        be prepared below.

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # PREPARE TABLE
    # ========================================================

    if len(filtered_df) == 0:

        st.info(
            "No risk incidents match "
            "the selected filters."
        )

    else:

        # ----------------------------------------------------
        # Latest 10 incidents
        # ----------------------------------------------------

        recent_df = (
            filtered_df
            .tail(10)
            .iloc[::-1]
            .copy()
        )


        # ----------------------------------------------------
        # Ensure text datatype
        # ----------------------------------------------------

        recent_df = recent_df.fillna("")

        for column in COLUMNS:

            recent_df[column] = (
                recent_df[column]
                .astype(str)
            )


        # ====================================================
        # SLIM TABLE FOR EDITOR (hide source-specific fields)
        # ====================================================

        SOURCE_SPECIFIC_COLUMNS = [
            "TCC_System_Affected",
            "TCC_Downtime_Minutes",
            "TCC_Impact_Type",

            "SAAM_Staff_Name",
            "SAAM_Department",
            "SAAM_Anomaly_Type",

            "DLM_Data_Type",
            "DLM_Destination_Channel",
            "DLM_Data_Classification",

            "ORE_Process_Affected",
            "ORE_Root_Cause_Category",
            "ORE_Business_Unit"
        ]
        editor_display_df = recent_df.drop(
            columns=SOURCE_SPECIFIC_COLUMNS
        ).reset_index(drop=True)

        editor_display_df.insert(0, "🔍 View", False)

        # ----------------------------------------------------
        # RE-APPLY ANY UNSAVED EDITS FROM BEFORE THE RESET
        # ----------------------------------------------------

        EDITABLE_COLS = [
            "Status", "Potential Breach", "Breach PIC",
            "Policies / Regulations Breached",
            "ORE Reportability", "ORE PIC", "ORE Case ID"
        ]

        if st.session_state["preserved_edits"]:

            preserved_lookup = {
                row["Risk Incident ID"]: row
                for row in st.session_state["preserved_edits"]
            }

            for i, row in editor_display_df.iterrows():

                incident_id = row["Risk Incident ID"]

                if incident_id in preserved_lookup:

                    for col in EDITABLE_COLS:
                        editor_display_df.at[i, col] = preserved_lookup[incident_id][col]

                    # NOTE: "🔍 View" intentionally NOT restored — stays False


        # ====================================================
        # EDITABLE DATA EDITOR
        # ====================================================

        edited_df = st.data_editor(

            editor_display_df,

            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            height=500,
            key=f"risk_incident_editor_{st.session_state['view_table_reset']}",

            disabled=[
                "Risk Incident ID",
                "Risk Title",
                "Risk Description",
                "Source of Register",
                "Severity",
                "Financial Impact",
                "Date & Time of Creation",
                "Policies / Regulations Breached",
                "Attachments"
            ],
            column_config={

                "🔍 View":
                    st.column_config.CheckboxColumn(
                        "🔍 View",
                        help="Tick to view source-specific details",
                        default=False,
                        width="small"
                    ),

                # --------------------------------------------
                # LOCKED FIELDS
                # --------------------------------------------

                "Risk Incident ID":
                    st.column_config.TextColumn(
                        "Incident ID",
                        disabled=True,
                        width="medium"
                    ),

                "Risk Title":
                    st.column_config.TextColumn(
                        "Risk Title",
                        disabled=True,
                        width="medium"
                    ),

                "Risk Description":
                    st.column_config.TextColumn(
                        "Risk Description",
                        disabled=True,
                        width="large"
                    ),

                "Source of Register":
                    st.column_config.TextColumn(
                        "Source",
                        disabled=True,
                        width="small"
                    ),

                "Severity":
                    st.column_config.TextColumn(
                        "Severity",
                        disabled=True,
                        width="small"
                    ),

                "Financial Impact":
                    st.column_config.TextColumn(
                        "Financial Impact",
                        disabled=True,
                        width="small"
                    ),

                "Date & Time of Creation":
                    st.column_config.TextColumn(
                        "Created",
                        disabled=True,
                        width="medium"
                    ),

                "Policies / Regulations Breached":
                    st.column_config.TextColumn(
                        "Policies / Regulations Breached",
                        disabled=True,
                        width="large"
                    ),

                "Attachments":
                    st.column_config.TextColumn(
                        "Attachments",
                        disabled=True,
                        width="medium"
                    ),


                # --------------------------------------------
                # STATUS
                # --------------------------------------------

                "Status":
                    st.column_config.SelectboxColumn(
                        "Status",
                        options=STATUS_OPTIONS,
                        required=True,
                        width="medium"
                    ),


                # --------------------------------------------
                # POTENTIAL BREACH
                # --------------------------------------------

                "Potential Breach":
                    st.column_config.SelectboxColumn(
                        "Potential Breach",
                        options=[
                            "",
                            "Yes",
                            "No"
                        ],
                        required=False,
                        width="medium"
                    ),


                # --------------------------------------------
                # BREACH PIC
                # --------------------------------------------

                "Breach PIC":
                    st.column_config.SelectboxColumn(
                        "Breach PIC",
                        options=[
                            ""
                        ] + BREACH_PIC_OPTIONS,
                        required=False,
                        width="large"
                    ),


                # --------------------------------------------
                # ORE REPORTABILITY
                # --------------------------------------------

                "ORE Reportability":
                    st.column_config.SelectboxColumn(
                        "ORE Reportability",
                        options=[
                            "",
                            "Yes",
                            "No"
                        ],
                        required=False,
                        width="medium"
                    ),


                # --------------------------------------------
                # ORE PIC
                # --------------------------------------------

                "ORE PIC":
                    st.column_config.TextColumn(
                        "ORE PIC",
                        disabled=False,
                        width="medium"
                    ),


                # --------------------------------------------
                # ORE CASE ID
                # --------------------------------------------

                "ORE Case ID":
                    st.column_config.TextColumn(
                        "ORE Case ID",
                        disabled=False,
                        width="medium"
                    )
            }
        )

        # ----------------------------------------------------
        # ALWAYS SAVE THE LATEST STATE, IN CASE OF A RESET
        # ----------------------------------------------------

        st.session_state["preserved_edits"] = edited_df.to_dict("records")
        

      # ====================================================
        # TRIGGER POPUP FOR CHECKED ROW
        # ====================================================

        checked_rows = edited_df[edited_df["🔍 View"] == True]

        if len(checked_rows) > 0:

            # Only pop up for the first checked row per rerun
            selected_incident_id = checked_rows.iloc[0]["Risk Incident ID"]

            detail_row = recent_df[
                recent_df["Risk Incident ID"] == selected_incident_id
            ].iloc[0]

            show_incident_details(detail_row)

        # ====================================================
        # BREACH PIC ASSIGNMENT
        # ====================================================

        yes_breach_df = edited_df[
            edited_df[
                "Potential Breach"
            ]
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        ].copy()


        breach_pic_selections = {}
        policy_selections = {}


        if len(yes_breach_df) > 0:

            st.markdown("---")

            st.markdown(
                """
                <div class="section-header">
                    ⚠️ Potential Breach — Breach PIC Assignment
                </div>
                """,
                unsafe_allow_html=True
            )


            st.markdown(
                """
                <div class="breach-pic-box">

                <strong>
                    Potential breach incidents detected.
                </strong>

                <br><br>

                Please select the appropriate Breach PIC
                for each potential breach incident.

                <br><br>

                After selecting the Breach PIC, an email draft
                will automatically be prepared using the
                information recorded in the Risk Incident Register.

                </div>
                """,
                unsafe_allow_html=True
            )


            # =================================================
            # EACH POTENTIAL BREACH INCIDENT
            # =================================================

            for _, breach_row in yes_breach_df.iterrows():

                incident_id = str(
                    breach_row[
                        "Risk Incident ID"
                    ]
                ).strip()

                risk_title = str(
                    breach_row[
                        "Risk Title"
                    ]
                ).strip()

                risk_description = str(
                    breach_row[
                        "Risk Description"
                    ]
                ).strip()

                source = str(
                    breach_row[
                        "Source of Register"
                    ]
                ).strip()

                severity = str(
                    breach_row[
                        "Severity"
                    ]
                ).strip()

                financial_impact = str(
                    breach_row[
                        "Financial Impact"
                    ]
                ).strip()

                potential_breach = str(
                    breach_row[
                        "Potential Breach"
                    ]
                ).strip()

                attachments = str(
                    breach_row[
                        "Attachments"
                    ]
                ).strip()

                current_pic = str(
                    breach_row[
                        "Breach PIC"
                    ]
                ).strip()

                current_policy = str(
                    breach_row[
                        "Policies / Regulations Breached"
                    ]
                ).strip()


                # ------------------------------------------------
                # INCIDENT INFORMATION
                # ------------------------------------------------

                st.markdown(
                    f"""
                    ### Incident: `{incident_id}`

                    **Risk Title:** {risk_title}
                    """
                )


                # ------------------------------------------------
                # BREACH PIC DROPDOWN
                # ------------------------------------------------

                current_display = (
                    get_breach_pic_display(
                        current_pic
                    )
                )


                if current_display in BREACH_PIC_OPTIONS:

                    default_index = (
                        BREACH_PIC_OPTIONS.index(
                            current_display
                        ) + 1
                    )

                else:

                    default_index = 0


                selected_display = st.selectbox(

                    "Select Breach PIC",

                    options=[
                        "— Please select Breach PIC —"
                    ] + BREACH_PIC_OPTIONS,

                    index=default_index,

                    key=f"breach_pic_{incident_id}"
                )


                # ------------------------------------------------
                # SELECTED PIC
                # ------------------------------------------------

                if (
                    selected_display
                    != "— Please select Breach PIC —"
                ):

                    selected_name = (
                        get_breach_pic_name(
                            selected_display
                        )
                    )

                    selected_email = (
                        get_breach_pic_email(
                            selected_name
                        )
                    )

                    breach_pic_selections[
                        incident_id
                    ] = {
                        "name":
                            selected_name,
                        "email":
                            selected_email
                    }


                    st.success(
                        f"Assigned Breach PIC: "
                        f"{selected_name}"
                    )

                    st.caption(
                        f"Email: {selected_email}"
                    )


                    # =================================================
                    # POLICY INPUT
                    # =================================================

                    st.markdown(
                        "#### 📋 Policies / Regulations Breached"
                    )


                    st.caption(
                        "The assigned Breach PIC can enter the "
                        "relevant policies, regulations, procedures "
                        "or clauses that may have been breached."
                    )

                    if st.button("Suggest policy text", key=f"ai_policy_{incident_id}"):
                        with st.spinner("Analyzing..."):
                            ai_result = get_ai_breach_assessment(
                                risk_title, risk_description, source, severity
                            )

                        st.write(ai_result)

                        if ai_result["suggested_policies"]:
                            st.session_state[f"policy_{incident_id}"] = ai_result["suggested_policies"]
                            st.rerun()
                        else:
                            st.info("No specific policy suggestion available.")


                    policies_breached = st.text_area(

                        "Enter applicable policies / regulations",

                        value=current_policy,

                        placeholder=(
                            "Example:\n"
                            "• Information Security Policy – Section 4.2\n"
                            "• Data Protection Procedure – Clause 6.1\n"
                            "• Operational Risk Management Policy – Section 3"
                        ),

                        height=130,

                        key=f"policy_{incident_id}"
                    )


                    policy_selections[
                        incident_id
                    ] = policies_breached


                    # =================================================
                    # EMAIL DRAFT
                    # =================================================

                    st.markdown("---")

                    st.markdown(
                        """
                        <div class="email-draft-box">

                        <div class="email-draft-title">
                            📧 Potential Breach Email Draft
                        </div>

                        The draft below has been automatically
                        generated from the Risk Incident Register.
                        You can copy it into Gmail when ready.

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                    subject, email_body = (
                        generate_email_draft(

                            incident_id=
                                incident_id,

                            risk_title=
                                risk_title,

                            risk_description=
                                risk_description,

                            source=
                                source,

                            severity=
                                severity,

                            financial_impact=
                                financial_impact,

                            potential_breach=
                                potential_breach,

                            breach_pic_name=
                                selected_name,

                            breach_pic_email=
                                selected_email,

                            policies_breached=
                                policies_breached,

                            attachments=
                                attachments
                        )
                    )


                    # ------------------------------------------------
                    # EMAIL SUBJECT
                    # ------------------------------------------------

                    st.text_input(
                        "Email Subject",
                        value=subject,
                        key=f"email_subject_{incident_id}"
                    )


                    # ------------------------------------------------
                    # EMAIL BODY
                    # ------------------------------------------------

                    st.text_area(
                        "Email Draft",
                        value=email_body,
                        height=600,
                        key=f"email_body_{incident_id}"
                    )


                    # ------------------------------------------------
                    # ATTACHMENT SUMMARY
                    # ------------------------------------------------

                    if attachments:

                        st.info(
                            "📎 Attachments recorded in the "
                            "Risk Incident Register: "
                            f"{attachments}"
                        )

                    else:

                        st.caption(
                            "📎 No attachments were recorded "
                            "for this incident."
                        )


                else:

                    st.warning(
                        "Please select a Breach PIC to "
                        "generate the email draft."
                    )


                st.markdown("---")


        # ====================================================
        # SAVE ASSESSMENT CHANGES
        # ====================================================

        st.markdown("")

        if st.button(
            "💾 Save Assessment Changes",
            use_container_width=True
        ):

            editable_columns = [

                "Status",
                "Potential Breach",
                "Breach PIC",
                "Policies / Regulations Breached",
                "ORE Reportability",
                "ORE PIC",
                "ORE Case ID"
            ]


            # =================================================
            # UPDATE MASTER DATA
            # =================================================

            for _, edited_row in edited_df.iterrows():

                incident_id = str(
                    edited_row[
                        "Risk Incident ID"
                    ]
                ).strip()


                matching_rows = df.index[
                    df[
                        "Risk Incident ID"
                    ]
                    .astype(str)
                    .str.strip()
                    == incident_id
                ]


                if len(matching_rows) == 0:

                    continue


                original_index = (
                    matching_rows[0]
                )


                # ---------------------------------------------
                # NORMAL EDITABLE FIELDS
                # ---------------------------------------------

                for column in editable_columns:

                    # -----------------------------------------
                    # BREACH PIC
                    # -----------------------------------------

                    if column == "Breach PIC":

                        potential_breach = str(
                            edited_row[
                                "Potential Breach"
                            ]
                        ).strip().lower()


                        if (
                            potential_breach
                            == "yes"
                            and incident_id
                            in breach_pic_selections
                        ):

                            selected_name = (
                                breach_pic_selections[
                                    incident_id
                                ]["name"]
                            )

                            df.loc[
                                original_index,
                                "Breach PIC"
                            ] = selected_name


                        elif (
                            potential_breach
                            != "yes"
                        ):

                            df.loc[
                                original_index,
                                "Breach PIC"
                            ] = ""


                        continue


                    # -----------------------------------------
                    # POLICIES / REGULATIONS
                    # -----------------------------------------

                    if (
                        column
                        == "Policies / Regulations Breached"
                    ):

                        potential_breach = str(
                            edited_row[
                                "Potential Breach"
                            ]
                        ).strip().lower()


                        if (
                            potential_breach
                            == "yes"
                            and incident_id
                            in policy_selections
                        ):

                            df.loc[
                                original_index,
                                column
                            ] = policy_selections[
                                incident_id
                            ]

                        elif (
                            potential_breach
                            != "yes"
                        ):

                            df.loc[
                                original_index,
                                column
                            ] = ""


                        continue


                    # -----------------------------------------
                    # OTHER EDITABLE FIELDS
                    # -----------------------------------------

                    value = edited_row[column]


                    if pd.isna(value):

                        value = ""


                    df.loc[
                        original_index,
                        column
                    ] = str(value)


            # =================================================
            # FORCE TEXT
            # =================================================

            df = df.fillna("")

            for column in COLUMNS:

                df[column] = (
                    df[column]
                    .astype(str)
                )


            # =================================================
            # SAVE CSV
            # =================================================

            save_data(df)


            st.success(
                "Assessment changes saved successfully."
            )


            st.rerun()

# ============================================================
# BREACH & ORE STATISTICS
# ============================================================

elif page == "Breach & ORE Statistics":

    st.markdown(
        """
        <div class="section-header">
            Potential Breach & ORE Reportability Statistics
        </div>
        """,
        unsafe_allow_html=True
    )

    if len(df) == 0:

        st.info("No risk incidents recorded yet.")

    else:

        # --------------------------------------------------
        # PREP: parse creation datetime, flag Yes rows
        # --------------------------------------------------

        stats_df = df.copy()

        stats_df["Created"] = pd.to_datetime(
            stats_df["Date & Time of Creation"],
            errors="coerce"
        )

        stats_df = stats_df.dropna(subset=["Created"])

        stats_df["Breach_Yes"] = (
            stats_df["Potential Breach"]
            .astype(str).str.strip().str.lower() == "yes"
        ).astype(int)

        stats_df["ORE_Yes"] = (
            stats_df["ORE Reportability"]
            .astype(str).str.strip().str.lower() == "yes"
        ).astype(int)

        # --------------------------------------------------
        # PERIOD SELECTOR
        # --------------------------------------------------

        period = st.radio(
            "View by",
            ["Day", "Week", "Month", "Year"],
            horizontal=True
        )

        if period == "Day":
            stats_df["Period"] = stats_df["Created"].dt.date

        elif period == "Week":
            stats_df["Period"] = (
                stats_df["Created"].dt.to_period("W").apply(lambda p: p.start_time.date())
            )

        elif period == "Month":
            stats_df["Period"] = (
                stats_df["Created"].dt.to_period("M").astype(str)
            )

        else:  # Year
            stats_df["Period"] = (
                stats_df["Created"].dt.to_period("Y").astype(str)
            )

        # --------------------------------------------------
        # AGGREGATE
        # --------------------------------------------------

        summary = (
            stats_df
            .groupby("Period")[["Breach_Yes", "ORE_Yes"]]
            .sum()
            .rename(columns={
                "Breach_Yes": "Potential Breach = Yes",
                "ORE_Yes": "ORE Reportability = Yes"
            })
            .sort_index()
        )

        # --------------------------------------------------
        # KPI TOTALS (for the currently selected period range)
        # --------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">
                        {int(summary["Potential Breach = Yes"].sum())}
                    </div>
                    <div class="metric-label">
                        Total Potential Breaches
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">
                        {int(summary["ORE Reportability = Yes"].sum())}
                    </div>
                    <div class="metric-label">
                        Total Reportable ORE
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )    

            page = st.radio(
                "Select module",
                [
                    "Dashboard",
                    "Create Risk Incident",
                    "Breach & ORE Statistics"
                ]
            )

        st.markdown("---")

        # --------------------------------------------------
        # CHART
        # --------------------------------------------------

        st.subheader(f"Trend by {period}")

        st.bar_chart(summary)

        # --------------------------------------------------
        # TABLE
        # --------------------------------------------------

        st.subheader("Detailed Breakdown")

        st.dataframe(
            summary,
            use_container_width=True
        )

