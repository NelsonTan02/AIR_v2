import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
from google import genai
import os
from email_sender import send_email, is_email_configured, get_setting

# ============================================================
# GEMINI CONFIGURATION
# ============================================================

GEMINI_API_KEY = get_setting("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Central Risk Incident Register",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

if "view_table_reset" not in st.session_state:
    st.session_state["view_table_reset"] = 0

if "preserved_edits" not in st.session_state:
    st.session_state["preserved_edits"] = None

if "ore_email_drafts" not in st.session_state:
    st.session_state["ore_email_drafts"] = {}


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

COLUMNS = [
    "Risk Incident ID",
    "Risk Title",
    "Risk Description",
    "Source of Register",
    "Severity",
    "Financial Impact",
    "Date & Time of Creation",

    "TCC_System_Affected",
    "TCC_Downtime_Minutes",
    "TCC_Impact_Type",

    "SAAM_Staff_Name",
    "SAAM_Department",
    "SAAM_Anomaly_Type",

    "DLM_Data_Type",
    "DLM_Destination_Channel",
    "DLM_Data_Classification",

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

SOURCE_OPTIONS = ["TCC", "SAAM", "DLM", "ORE"]

SEVERITY_OPTIONS = ["Low", "Medium", "High"]

FINANCIAL_OPTIONS = ["Low", "Medium", "High"]

STATUS_OPTIONS = [
    "Open",
    "Under Investigation",
    "Pending Review",
    "Closed"
]

YES_NO_OPTIONS = ["Yes", "No"]


# ============================================================
# TCC OPTIONS
# ============================================================

TCC_SYSTEMS = [
    "Core Banking System",
    "Internet Banking",
    "Mobile App",
    "Payment Gateway",
    "Internal Email"
]

TCC_IMPACT_TYPES = [
    "Full Outage",
    "Degraded Performance",
    "Intermittent Failure"
]


# ============================================================
# SAAM OPTIONS
# ============================================================

SAAM_DEPARTMENTS = [
    "Retail Banking",
    "Treasury",
    "Operations",
    "IT",
    "Compliance"
]

SAAM_ANOMALY_TYPES = [
    "Unusual Login Time",
    "Excessive Access Attempts",
    "Privileged Access Misuse",
    "Unusual Transaction Pattern"
]


# ============================================================
# DLM OPTIONS
# ============================================================

DLM_DATA_TYPES = [
    "Customer PII",
    "Account Numbers",
    "Internal Financial Data",
    "Credentials",
    "Confidential Documents"
]

DLM_CHANNELS = [
    "Email (External)",
    "USB Storage",
    "Cloud Upload",
    "Printing",
    "Messaging App"
]

DLM_CLASSIFICATIONS = [
    "Confidential",
    "Restricted",
    "Internal Use Only"
]


# ============================================================
# BREACH PIC DIRECTORY
# ============================================================

BREACH_PIC_DIRECTORY = {
    "Alice Tan": "alice.tan@example.com",
    "Benjamin Lim": "benjamin.lim@example.com",
    "Carol Wong": "carol.wong@example.com",
    "Daniel Lee": "daniel.lee@example.com",
    "Emily Ng": "emily.ng@example.com",
    "Nelson Tan": "nelsontanzuxuan@gmail.com",
    "Emily Tan": "emilychai1725@gmail.com"
}


# ============================================================
# ORE PIC DIRECTORY
# ============================================================

ORE_PIC_DIRECTORY = {
    "Farah Ahmad": "farah.ahmad@example.com",
    "George Lim": "george.lim@example.com",
    "Hannah Wong": "hannah.wong@example.com",
    "Ivan Tan": "ivan.tan@example.com",
    "Jennifer Lee": "jennifer.lee@example.com"
}


# Values stored in the CSV/dashboard are the PIC names only.
# Keep the email-inclusive labels separate for the assignment widgets.
BREACH_PIC_OPTIONS = list(BREACH_PIC_DIRECTORY.keys())

BREACH_PIC_DISPLAY_OPTIONS = [
    f"{name} — {email}"
    for name, email in BREACH_PIC_DIRECTORY.items()
]

ORE_PIC_OPTIONS = list(ORE_PIC_DIRECTORY.keys())

ORE_PIC_DISPLAY_OPTIONS = [
    f"{name} — {email}"
    for name, email in ORE_PIC_DIRECTORY.items()
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_value(value):
    """Safely convert a value to a clean string."""

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


# ============================================================
# PIC HELPERS
# ============================================================

def get_breach_pic_display(name):

    name = clean_value(name)

    if not name:
        return ""

    if name in BREACH_PIC_DIRECTORY:
        return f"{name} — {BREACH_PIC_DIRECTORY[name]}"

    return name


def get_breach_pic_name(display_value):

    display_value = clean_value(display_value)

    if not display_value:
        return ""

    if " — " in display_value:
        return display_value.split(" — ", 1)[0].strip()

    if " - " in display_value:
        return display_value.split(" - ", 1)[0].strip()

    return display_value


def get_breach_pic_email(name):

    return BREACH_PIC_DIRECTORY.get(
        clean_value(name),
        ""
    )


def get_ore_pic_display(name):

    name = clean_value(name)

    if not name:
        return ""

    if name in ORE_PIC_DIRECTORY:
        return f"{name} — {ORE_PIC_DIRECTORY[name]}"

    return name


def get_ore_pic_name(display_value):

    display_value = clean_value(display_value)

    if not display_value:
        return ""

    if " — " in display_value:
        return display_value.split(" — ", 1)[0].strip()

    if " - " in display_value:
        return display_value.split(" - ", 1)[0].strip()

    return display_value


def get_ore_pic_email(name):

    return ORE_PIC_DIRECTORY.get(
        clean_value(name),
        ""
    )


# ============================================================
# AI BREACH ASSESSMENT
# ============================================================

def get_ai_breach_assessment(
    risk_title,
    risk_description,
    source,
    severity
):

    if client is None:

        return {
            "suggested_potential_breach": "No",
            "confidence": "Low",
            "reasoning": "Gemini API key is not configured.",
            "suggested_policies": ""
        }

    prompt = f"""
You are assisting a bank's operational risk team
in triaging a risk incident.

Analyze the incident below.

Respond in EXACTLY this plain text format:

Breach: Yes or No
Confidence: Low or Medium or High
Reasoning: 1-2 sentence explanation
Policies: short list of relevant policy/regulation areas,
or leave blank if none apply

Incident details:

Source: {source}
Severity: {severity}
Title: {risk_title}
Description: {risk_description}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return parse_ai_assessment(
            response.text.strip()
        )

    except Exception as e:

        return {
            "suggested_potential_breach": "No",
            "confidence": "Low",
            "reasoning": f"AI assessment unavailable: {e}",
            "suggested_policies": ""
        }


# ============================================================
# PARSE AI ASSESSMENT
# ============================================================

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

            value = stripped.split(
                ":",
                1
            )[1].strip()

            if value.lower() in ["yes", "no"]:
                result["suggested_potential_breach"] = value

            current_field = None

        elif lower.startswith("confidence:"):

            result["confidence"] = (
                stripped.split(":", 1)[1].strip()
            )

            current_field = None

        elif lower.startswith("reasoning:"):

            result["reasoning"] = (
                stripped.split(":", 1)[1].strip()
            )

            current_field = None

        elif lower.startswith("policies:"):

            first_line = (
                stripped.split(":", 1)[1].strip()
            )

            if first_line:
                policy_lines.append(first_line)

            current_field = "policies"

        elif current_field == "policies":

            policy_lines.append(stripped)

    result["suggested_policies"] = "\n".join(
        policy_lines
    )

    return result


def get_ai_policy_suggestion(
    risk_title,
    risk_description,
    source,
    severity
):

    result = get_ai_breach_assessment(
        risk_title,
        risk_description,
        source,
        severity
    )

    return result



# ============================================================
# ORE EMAIL DRAFT GENERATOR
# ============================================================

def generate_ore_email_draft(
    incident_id,
    risk_title,
    risk_description,
    source,
    severity,
    financial_impact,
    potential_breach,
    attachments,
    ore_pic_name,
    ore_pic_email
):

    """
    Creates an ORE email draft in the same style and structure as the
    Potential Breach email draft. The email contains the core incident
    information, potential breach status, attachments, and a clear request
    for the ORE PIC to create an ORE case in the bank's eGRC system.
    """

    incident_id = clean_value(incident_id)
    risk_title = clean_value(risk_title)
    risk_description = clean_value(risk_description)
    source = clean_value(source)
    severity = clean_value(severity)
    financial_impact = clean_value(financial_impact)
    potential_breach = (
        clean_value(potential_breach)
        or "Not Assessed"
    )
    attachments = clean_value(attachments)
    ore_pic_name = clean_value(ore_pic_name)
    ore_pic_email = clean_value(ore_pic_email)

    recipient_name = (
        ore_pic_name
        or "[ORE PIC]"
    )

    recipient_email = (
        ore_pic_email
        or "[ORE PIC email]"
    )

    subject = (
        "ORE Case Creation Required - "
        f"{incident_id} - {risk_title}"
    )

    attachment_text = (
        attachments
        or "No attachments recorded"
    )

    body = f"""To: {recipient_name} <{recipient_email}>

Subject: {subject}

Dear {recipient_name},

The following risk incident has been assessed as reportable to Operational Risk Events (ORE).

Please review the incident details below and create the corresponding ORE case in the bank's eGRC system.

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

Attachments:
{attachment_text}

ORE Action Required:
Please create an ORE case for this incident in the bank's eGRC system and record the relevant incident details and supporting documentation.

Once the ORE case has been created, please update the Risk Incident Register with the eGRC ORE Case ID.

Thank you.

Regards,
Central Risk Incident Register
"""

    return subject, body


# ============================================================
# INCIDENT DETAIL POPUP
# ============================================================

@st.dialog("Incident Details", width="large")
def show_incident_details(detail_row):

    incident_id = clean_value(
        detail_row.get(
            "Risk Incident ID",
            ""
        )
    )

    source_type = clean_value(
        detail_row.get(
            "Source of Register",
            ""
        )
    )

    st.markdown(
        f"""
        <div class="breach-pic-box">
            <strong>Incident:</strong> {incident_id}<br>
            <strong>Source:</strong> {source_type}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"**Risk Title:** "
        f"{clean_value(detail_row.get('Risk Title', ''))}"
    )

    st.markdown(
        f"**Description:** "
        f"{clean_value(detail_row.get('Risk Description', ''))}"
    )

    col1, col2, col3 = st.columns(3)

    col1.markdown(
        f"**Severity:** "
        f"{clean_value(detail_row.get('Severity', ''))}"
    )

    col2.markdown(
        f"**Financial Impact:** "
        f"{clean_value(detail_row.get('Financial Impact', ''))}"
    )

    col3.markdown(
        f"**Created:** "
        f"{clean_value(detail_row.get('Date & Time of Creation', ''))}"
    )

    if source_type in ["TCC", "SAAM", "DLM"]:

        st.markdown("---")

        st.markdown(
            f"**{source_type} Specific Details**"
        )

        col1, col2, col3 = st.columns(3)

        if source_type == "TCC":

            col1.metric(
                "System Affected",
                clean_value(
                    detail_row.get(
                        "TCC_System_Affected",
                        ""
                    )
                ) or "-"
            )

            col2.metric(
                "Downtime (min)",
                clean_value(
                    detail_row.get(
                        "TCC_Downtime_Minutes",
                        ""
                    )
                ) or "-"
            )

            col3.metric(
                "Impact Type",
                clean_value(
                    detail_row.get(
                        "TCC_Impact_Type",
                        ""
                    )
                ) or "-"
            )

        elif source_type == "SAAM":

            col1.metric(
                "Staff Name / ID",
                clean_value(
                    detail_row.get(
                        "SAAM_Staff_Name",
                        ""
                    )
                ) or "-"
            )

            col2.metric(
                "Department",
                clean_value(
                    detail_row.get(
                        "SAAM_Department",
                        ""
                    )
                ) or "-"
            )

            col3.metric(
                "Anomaly Type",
                clean_value(
                    detail_row.get(
                        "SAAM_Anomaly_Type",
                        ""
                    )
                ) or "-"
            )

        elif source_type == "DLM":

            col1.metric(
                "Data Type",
                clean_value(
                    detail_row.get(
                        "DLM_Data_Type",
                        ""
                    )
                ) or "-"
            )

            col2.metric(
                "Destination / Channel",
                clean_value(
                    detail_row.get(
                        "DLM_Destination_Channel",
                        ""
                    )
                ) or "-"
            )

            col3.metric(
                "Data Classification",
                clean_value(
                    detail_row.get(
                        "DLM_Data_Classification",
                        ""
                    )
                ) or "-"
            )

    if source_type == "ORE":

        st.markdown("---")

        st.markdown("**ORE Assessment**")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "ORE Reportability",
            clean_value(
                detail_row.get(
                    "ORE Reportability",
                    ""
                )
            ) or "Not Assessed"
        )

        ore_pic_name = clean_value(
            detail_row.get(
                "ORE PIC",
                ""
            )
        )

        ore_pic_email = get_ore_pic_email(
            ore_pic_name
        )

        col2.metric(
            "ORE PIC",
            ore_pic_name or "-"
        )

        col3.metric(
            "ORE Case ID",
            clean_value(
                detail_row.get(
                    "ORE Case ID",
                    ""
                )
            ) or "-"
        )

        if ore_pic_email:
            st.caption(
                f"ORE PIC Email: {ore_pic_email}"
            )

    st.markdown("---")

    st.markdown(
        "**Assessment Information**"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Potential Breach",
        clean_value(
            detail_row.get(
                "Potential Breach",
                ""
            )
        ) or "Not Assessed"
    )

    col2.metric(
        "Breach PIC",
        clean_value(
            detail_row.get(
                "Breach PIC",
                ""
            )
        ) or "-"
    )

    col3.metric(
        "Status",
        clean_value(
            detail_row.get(
                "Status",
                ""
            )
        ) or "-"
    )

    policies = clean_value(
        detail_row.get(
            "Policies / Regulations Breached",
            ""
        )
    )

    if policies:

        st.markdown(
            "**Policies / Regulations Breached**"
        )

        st.text(policies)

    attachments = clean_value(
        detail_row.get(
            "Attachments",
            ""
        )
    )

    if attachments:

        st.markdown("---")

        st.caption(
            f"📎 Attachments: {attachments}"
        )

    st.markdown("---")

    if st.button(
        "Close",
        use_container_width=True
    ):

        st.session_state["view_table_reset"] += 1
        st.rerun()


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

.info-box {{
    background-color: #EAF2FF;
    padding: 15px 18px;
    border-radius: 8px;
    color: {BLUE};
    margin-bottom: 20px;
}}

.breach-pic-box {{
    background-color: {OCBC_LIGHT_RED};
    border-left: 5px solid {OCBC_RED};
    padding: 16px 20px;
    border-radius: 7px;
    margin-top: 10px;
    margin-bottom: 20px;
}}

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

section[data-testid="stSidebar"] {{
    background-color: {LIGHT_GREY};
}}

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

    for column in COLUMNS:

        if column not in df.columns:
            df[column] = ""

    df = df[COLUMNS].copy()

    df = df.fillna("")

    for column in COLUMNS:

        df[column] = (
            df[column].astype(str)
        )

    return df


# ============================================================
# SAVE DATA
# ============================================================

def save_data(df):

    df = df.copy()

    for column in COLUMNS:

        if column not in df.columns:
            df[column] = ""

    df = df[COLUMNS]

    df = df.fillna("")

    for column in COLUMNS:

        df[column] = (
            df[column].astype(str)
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

    random_part = (
        uuid.uuid4()
        .hex[:6]
        .upper()
    )

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
            "Provide a detailed description of the risk incident..."
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

    # --------------------------------------------------------
    # SOURCE-SPECIFIC INFORMATION
    # --------------------------------------------------------

    if source == "TCC":

        st.markdown(
            """
            <div class="section-header">
                TCC Incident Details
            </div>
            """,
            unsafe_allow_html=True
        )

        tcc_col1, tcc_col2, tcc_col3 = st.columns(3)

        with tcc_col1:

            tcc_system = st.selectbox(
                "System Affected",
                [""] + TCC_SYSTEMS
            )

        with tcc_col2:

            tcc_downtime = st.text_input(
                "Downtime (Minutes)",
                placeholder="e.g. 30"
            )

        with tcc_col3:

            tcc_impact = st.selectbox(
                "Impact Type",
                [""] + TCC_IMPACT_TYPES
            )

    else:

        tcc_system = ""
        tcc_downtime = ""
        tcc_impact = ""

    if source == "SAAM":

        st.markdown(
            """
            <div class="section-header">
                SAAM Incident Details
            </div>
            """,
            unsafe_allow_html=True
        )

        saam_col1, saam_col2, saam_col3 = st.columns(3)

        with saam_col1:

            saam_staff = st.text_input(
                "Staff Name / ID"
            )

        with saam_col2:

            saam_department = st.selectbox(
                "Department",
                [""] + SAAM_DEPARTMENTS
            )

        with saam_col3:

            saam_anomaly = st.selectbox(
                "Anomaly Type",
                [""] + SAAM_ANOMALY_TYPES
            )

    else:

        saam_staff = ""
        saam_department = ""
        saam_anomaly = ""

    if source == "DLM":

        st.markdown(
            """
            <div class="section-header">
                DLM Incident Details
            </div>
            """,
            unsafe_allow_html=True
        )

        dlm_col1, dlm_col2, dlm_col3 = st.columns(3)

        with dlm_col1:

            dlm_data_type = st.selectbox(
                "Data Type",
                [""] + DLM_DATA_TYPES
            )

        with dlm_col2:

            dlm_channel = st.selectbox(
                "Destination / Channel",
                [""] + DLM_CHANNELS
            )

        with dlm_col3:

            dlm_classification = st.selectbox(
                "Data Classification",
                [""] + DLM_CLASSIFICATIONS
            )

    else:

        dlm_data_type = ""
        dlm_channel = ""
        dlm_classification = ""

    if source == "ORE":

        st.markdown(
            """
            <div class="section-header">
                ORE Assessment
            </div>
            """,
            unsafe_allow_html=True
        )

        st.info(
            "ORE assessment will be completed after the incident "
            "is created. The ORE PIC is assigned from the approved "
            "ORE PIC directory."
        )

    # --------------------------------------------------------
    # AI BREACH ASSESSMENT
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="section-header">
            AI Breach Assessment (Suggestion)
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption(
        "Optional: get an AI-generated first pass on whether "
        "this incident may constitute a breach. Review and "
        "confirm the result manually."
    )

    if st.button(
        "Get AI Suggestion",
        key="ai_suggest_create"
    ):

        if (
            not risk_title.strip()
            or not risk_description.strip()
        ):

            st.warning(
                "Enter a Risk Title and Description first."
            )

        else:

            with st.spinner(
                "Analyzing incident..."
            ):

                ai_result = get_ai_breach_assessment(
                    risk_title,
                    risk_description,
                    source,
                    severity
                )

            st.markdown(
                f"""
                <div class="breach-pic-box">
                    <strong>Suggested Potential Breach:</strong>
                    {ai_result['suggested_potential_breach']}
                    &nbsp;|&nbsp;
                    <strong>Confidence:</strong>
                    {ai_result['confidence']}
                    <br><br>
                    <strong>Reasoning:</strong>
                    {ai_result['reasoning']}
                    <br><br>
                    <strong>Possible relevant policies:</strong>
                    <br>
                    {ai_result['suggested_policies'] or 'None suggested'}
                </div>
                """,
                unsafe_allow_html=True
            )

    # --------------------------------------------------------
    # ATTACHMENTS
    # --------------------------------------------------------

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

    st.markdown("---")

    if st.button(
        "➕ Create Risk Incident",
        use_container_width=True
    ):

        if not risk_title.strip():

            st.error(
                "Please enter the Risk Title."
            )

        elif not risk_description.strip():

            st.error(
                "Please enter the Risk Description."
            )

        else:

            attachment_names = []

            if uploaded_files:

                for uploaded_file in uploaded_files:

                    filename = (
                        f"{incident_id}_"
                        f"{uploaded_file.name}"
                    )

                    filepath = (
                        ATTACHMENT_FOLDER
                        / filename
                    )

                    with open(filepath, "wb") as f:
                        f.write(
                            uploaded_file.getbuffer()
                        )

                    attachment_names.append(
                        filename
                    )

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

                "TCC_System_Affected":
                    tcc_system,

                "TCC_Downtime_Minutes":
                    tcc_downtime,

                "TCC_Impact_Type":
                    tcc_impact,

                "SAAM_Staff_Name":
                    saam_staff,

                "SAAM_Department":
                    saam_department,

                "SAAM_Anomaly_Type":
                    saam_anomaly,

                "DLM_Data_Type":
                    dlm_data_type,

                "DLM_Destination_Channel":
                    dlm_channel,

                "DLM_Data_Classification":
                    dlm_classification,

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

            new_row = pd.DataFrame(
                [new_incident],
                columns=COLUMNS
            )

            df = pd.concat(
                [df, new_row],
                ignore_index=True
            )

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

    st.markdown(
        """
        <div class="section-header">
            Risk Incident Dashboard
        </div>
        """,
        unsafe_allow_html=True
    )

    total_incidents = len(df)

    open_incidents = len(
        df[
            df["Status"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "open"
        ]
    )

    potential_breaches = len(
        df[
            df["Potential Breach"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        ]
    )

    reportable_ore = len(
        df[
            df["ORE Reportability"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        ]
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{total_incidents}</div>
                <div class="metric-label">Total Risk Incidents</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{open_incidents}</div>
                <div class="metric-label">Open Incidents</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{potential_breaches}</div>
                <div class="metric-label">Potential Breaches</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{reportable_ore}</div>
                <div class="metric-label">Reportable ORE</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if len(df) > 0:

        st.markdown("---")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:

            st.subheader(
                "Incidents by Source"
            )

            st.bar_chart(
                df[
                    "Source of Register"
                ].value_counts()
            )

        with chart_col2:

            st.subheader(
                "Incidents by Severity"
            )

            st.bar_chart(
                df[
                    "Severity"
                ].value_counts()
            )

    st.markdown("---")

    st.markdown(
        "### 🔎 Filter Risk Incidents"
    )

    filter1, filter2, filter3, filter4 = st.columns(4)

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
                "Search incident ID, title, description, "
                "PIC or ORE Case ID"
            )
        )

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
            search.strip().lower()
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

    st.markdown("---")

    st.markdown(
        """
        <div class="section-header">
            Recent Risk Incidents
        </div>
        """,
        unsafe_allow_html=True
    )

    if len(filtered_df) == 0:

        st.info(
            "No risk incidents match the selected filters."
        )

    else:

        recent_df = (
            filtered_df
            .tail(10)
            .iloc[::-1]
            .copy()
        )

        recent_df = recent_df.fillna("")

        for column in COLUMNS:

            if column not in recent_df.columns:
                recent_df[column] = ""

            recent_df[column] = (
                recent_df[column].astype(str)
            )

        recent_df = recent_df[COLUMNS]

        SOURCE_SPECIFIC_COLUMNS = [

            "TCC_System_Affected",
            "TCC_Downtime_Minutes",
            "TCC_Impact_Type",

            "SAAM_Staff_Name",
            "SAAM_Department",
            "SAAM_Anomaly_Type",

            "DLM_Data_Type",
            "DLM_Destination_Channel",
            "DLM_Data_Classification"
        ]

        editor_display_df = (
            recent_df
            .drop(
                columns=SOURCE_SPECIFIC_COLUMNS,
                errors="ignore"
            )
            .reset_index(drop=True)
        )

        editor_display_df.insert(
            0,
            "🔍 View",
            False
        )

        EDITABLE_COLS = [

            "Status",
            "Potential Breach",
            "Breach PIC",
            "Policies / Regulations Breached",
            "ORE Reportability",
            "ORE PIC",
            "ORE Case ID"
        ]

        # ----------------------------------------------------
        # REAPPLY UNSAVED EDITS
        # ----------------------------------------------------

        if st.session_state[
            "preserved_edits"
        ]:

            preserved_lookup = {

                row["Risk Incident ID"]: row

                for row in st.session_state[
                    "preserved_edits"
                ]

                if row.get(
                    "Risk Incident ID"
                )
            }

            for i, row in editor_display_df.iterrows():

                current_id = clean_value(
                    row["Risk Incident ID"]
                )

                if current_id in preserved_lookup:

                    preserved_row = (
                        preserved_lookup[
                            current_id
                        ]
                    )

                    for col in EDITABLE_COLS:

                        if col in editor_display_df.columns:

                            editor_display_df.at[
                                i,
                                col
                            ] = clean_value(
                                preserved_row.get(
                                    col,
                                    ""
                                )
                            )

                    editor_display_df.at[
                        i,
                        "🔍 View"
                    ] = False

        edited_df = st.data_editor(

            editor_display_df,

            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            height=500,

            key=(
                "risk_incident_editor_"
                f"{st.session_state['view_table_reset']}"
            ),

            disabled=[

                "Risk Incident ID",
                "Risk Title",
                "Risk Description",
                "Source of Register",
                "Severity",
                "Financial Impact",
                "Date & Time of Creation",
                "Attachments"
            ],

            column_config={

                "🔍 View":
                    st.column_config.CheckboxColumn(
                        "🔍 View",
                        help=(
                            "Tick to view incident "
                            "source-specific details"
                        ),
                        default=False,
                        width="small"
                    ),

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
                        disabled=False,
                        width="large"
                    ),

                "Attachments":
                    st.column_config.TextColumn(
                        "Attachments",
                        disabled=True,
                        width="medium"
                    ),

                "Status":
                    st.column_config.TextColumn(
                        "Status",
                        disabled=True,
                        width="medium",
                        help=(
                            "Status is automatically determined "
                            "when assessment changes are saved."
                        )
                    ),

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

                "Breach PIC":
                    st.column_config.SelectboxColumn(
                        "Breach PIC",
                        options=[
                            ""
                        ] + BREACH_PIC_OPTIONS,
                        required=False,
                        width="large"
                    ),

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

                "ORE PIC":
                    st.column_config.SelectboxColumn(
                        "ORE PIC",
                        options=[
                            ""
                        ] + ORE_PIC_OPTIONS,
                        required=False,
                        width="large"
                    ),

                "ORE Case ID":
                    st.column_config.TextColumn(
                        "ORE Case ID",
                        disabled=False,
                        width="medium"
                    )
            }
        )

        st.session_state[
            "preserved_edits"
        ] = edited_df.to_dict(
            "records"
        )

        # ----------------------------------------------------
        # VIEW INCIDENT POPUP
        # ----------------------------------------------------

        checked_rows = edited_df[
            edited_df["🔍 View"] == True
        ]

        if len(checked_rows) > 0:

            selected_incident_id = clean_value(
                checked_rows.iloc[0][
                    "Risk Incident ID"
                ]
            )

            matching_details = recent_df[
                recent_df[
                    "Risk Incident ID"
                ]
                .astype(str)
                .str.strip()
                == selected_incident_id
            ]

            if len(matching_details) > 0:

                show_incident_details(
                    matching_details.iloc[0]
                )

        # ====================================================
        # INCIDENT-BY-INCIDENT ASSESSMENT WORKFLOW
        # ====================================================

        breach_pic_selections = {}
        policy_selections = {}
        ore_pic_selections = {}

        workflow_df = edited_df[
            (
                edited_df["Potential Breach"]
                .astype(str)
                .str.strip()
                .str.lower()
                == "yes"
            )
            |
            (
                edited_df["ORE Reportability"]
                .astype(str)
                .str.strip()
                .str.lower()
                == "yes"
            )
        ].copy()

        if len(workflow_df) > 0:

            st.markdown("---")

            # ====================================================
            # CHANGED:
            # Kept the red header but removed the warning emoji.
            # ====================================================

            st.markdown(
                """
                <div class="section-header">
                    Incident Assessment & PIC Assignment
                </div>
                """,
                unsafe_allow_html=True
            )

            # ====================================================
            # CHANGED:
            # Removed the pink "Assessment workflow / Tip" box.
            # No workflow logic has been changed.
            # ====================================================

            for _, incident_row in workflow_df.iterrows():

                incident_id = clean_value(
                    incident_row[
                        "Risk Incident ID"
                    ]
                )

                risk_title = clean_value(
                    incident_row[
                        "Risk Title"
                    ]
                )

                risk_description = clean_value(
                    incident_row[
                        "Risk Description"
                    ]
                )

                source = clean_value(
                    incident_row[
                        "Source of Register"
                    ]
                )

                severity = clean_value(
                    incident_row[
                        "Severity"
                    ]
                )

                financial_impact = clean_value(
                    incident_row[
                        "Financial Impact"
                    ]
                )

                attachments = clean_value(
                    incident_row[
                        "Attachments"
                    ]
                )

                potential_breach = clean_value(
                    incident_row[
                        "Potential Breach"
                    ]
                )

                current_breach_pic = clean_value(
                    incident_row[
                        "Breach PIC"
                    ]
                )

                current_policy = clean_value(
                    incident_row[
                        "Policies / Regulations Breached"
                    ]
                )

                ore_reportability = clean_value(
                    incident_row[
                        "ORE Reportability"
                    ]
                )

                current_ore_pic = clean_value(
                    incident_row[
                        "ORE PIC"
                    ]
                )

                current_ore_case_id = clean_value(
                    incident_row[
                        "ORE Case ID"
                    ]
                )

                current_status = clean_value(
                    incident_row[
                        "Status"
                    ]
                )

                breach_yes = (
                    potential_breach.lower()
                    == "yes"
                )

                ore_yes = (
                    ore_reportability.lower()
                    == "yes"
                )

                workflow_flags = []

                if breach_yes:
                    workflow_flags.append(
                        "Potential Breach"
                    )

                if ore_yes:
                    workflow_flags.append(
                        "ORE"
                    )

                flag_text = " + ".join(
                    workflow_flags
                )

                # ------------------------------------------------
                # ONE EXPANDER PER INCIDENT
                # ------------------------------------------------

                with st.expander(
                    (
                        f"{incident_id} — "
                        f"{risk_title} | "
                        f"{flag_text} | "
                        f"Status: "
                        f"{current_status or 'Open'}"
                    ),
                    expanded=False
                ):

                    st.markdown(
                        f"### Incident: `{incident_id}`"
                    )

                    st.markdown(
                        f"**Risk Title:** {risk_title}"
                    )

                    summary_col1, summary_col2, summary_col3, summary_col4 = (
                        st.columns(4)
                    )

                    summary_col1.metric(
                        "Potential Breach",
                        potential_breach
                        or "Not Assessed"
                    )

                    summary_col2.metric(
                        "ORE Reportability",
                        ore_reportability
                        or "Not Assessed"
                    )

                    summary_col3.metric(
                        "Severity",
                        severity or "-"
                    )

                    summary_col4.metric(
                        "Status",
                        current_status or "Open"
                    )

                    st.markdown("---")

                    # ==================================================
                    # POTENTIAL BREACH SECTION FOR THIS INCIDENT
                    # ==================================================

                    if breach_yes:

                        st.markdown(
                            "### ⚠️ Potential Breach"
                        )

                        st.caption(
                            "Assign the appropriate Breach PIC "
                            "and record the applicable policies / "
                            "regulations for this incident."
                        )

                        current_display = (
                            get_breach_pic_display(
                                current_breach_pic
                            )
                        )

                        if (
                            current_display
                            in BREACH_PIC_DISPLAY_OPTIONS
                        ):

                            breach_default_index = (
                                BREACH_PIC_DISPLAY_OPTIONS.index(
                                    current_display
                                ) + 1
                            )

                        else:

                            breach_default_index = 0

                        selected_display = st.selectbox(
                            "Select Breach PIC",

                            options=[
                                "— Please select Breach PIC —"
                            ]
                            + BREACH_PIC_DISPLAY_OPTIONS,

                            index=breach_default_index,

                            key=f"breach_pic_{incident_id}"
                        )

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

                        else:

                            st.warning(
                                "Please select a Breach PIC "
                                "for this incident."
                            )

                        st.markdown(
                            "#### 📋 Policies / Regulations Breached"
                        )

                        if st.button(
                            "Suggest policy text",
                            key=f"ai_policy_{incident_id}"
                        ):

                            with st.spinner(
                                "Analyzing..."
                            ):

                                suggested_policy = (
                                    get_ai_policy_suggestion(
                                        risk_title,
                                        risk_description,
                                        source,
                                        severity
                                    )
                                )

                                # st.write("AI Policy Suggestion: " + str(suggested_policy))

                            if suggested_policy:

                                st.session_state[
                                    f"policy_{incident_id}"
                                ] = suggested_policy

                                st.info(
                                    f"""
Suggested potential breach: {suggested_policy['suggested_potential_breach']}\n
Confidence: {suggested_policy['confidence']}\n
Reasoning: {suggested_policy['reasoning']}\n
Suggested Policies: {suggested_policy['suggested_policies'] or 'None suggested'}\n
**Disclaimer:** The above suggestions are generated by an AI model and should be reviewed by a qualified professional before making any decisions.
                                    """
                                )

                            else:

                                st.info(
                                    "No specific policy suggestion available."
                                )

                        policies_breached = st.text_area(
                            "Enter applicable policies / regulations",

                            value=(
                                st.session_state.get(
                                    f"policy_{incident_id}",
                                    current_policy
                                )
                            ),

                            placeholder=(
                                "Example:\n"
                                "• Information Security Policy – Section 4.2\n"
                                "• Data Protection Procedure – Clause 6.1\n"
                                "• Operational Risk Management Policy – Section 3"
                            ),

                            height=130,

                            key=f"policy_input_{incident_id}"
                        )

                        policy_selections[
                            incident_id
                        ] = policies_breached

                        st.markdown("---")

                        st.markdown(
                            "#### 📧 Potential Breach Email Draft"
                        )

                        if (
                            selected_display
                            != "— Please select Breach PIC —"
                        ):

                            subject = (
                                "Potential Breach Review Required - "
                                f"{incident_id} - {risk_title}"
                            )

                            email_body = f"""
    Dear {selected_name},
    
    A potential breach has been identified in the Central Risk Incident Register.

    Please review the incident details below and assess the applicable policies, regulations, procedures, or requirements that may have been breached.

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

    Breach PIC:
    {selected_name}

    Policies / Regulations:
    {policies_breached or "To be assessed"}

    Attachments:
    {attachments or "No attachments recorded"}

    Please provide your assessment and advise on any further action required.

    Thank you.

    Regards,
    Central Risk Incident Register
"""

                            st.text_input(
                                "Email Subject",
                                value=subject,
                                key=(
                                    f"breach_email_subject_"
                                    f"{incident_id}"
                                )
                            )

                            st.text_area(
                                "Email Draft",
                                value=email_body,
                                height=400,
                                key=(
                                    f"breach_email_body_"
                                    f"{incident_id}"
                                )
                            )

                            # ------------------------------------------------
                            # SEND EMAIL
                            # ------------------------------------------------

                            if is_email_configured():

                                if st.button(
                                    "📤 Send this email",
                                    key=f"send_breach_{incident_id}"
                                ):

                                    try:

                                        send_email(
                                            to_address=selected_email,
                                            subject=subject,
                                            body=email_body
                                        )

                                        st.success(
                                            f"Email sent to {selected_email}"
                                        )

                                    except RuntimeError as e:

                                        st.error(str(e))

                            else:

                                st.caption(
                                    "Email sending not configured — add "
                                    "GMAIL_ADDRESS and GMAIL_APP_PASSWORD "
                                    "to .env to enable sending."
                                )


        
                        else:

                            st.info(
                                "Assign a Breach PIC above "
                                "to generate the email draft."
                            )

                    # ==================================================
                    # ORE SECTION FOR THIS INCIDENT
                    # ==================================================

                    if ore_yes:

                        if breach_yes:
                            st.markdown("---")

                        st.markdown(
                            "### 🟠 ORE — PIC Assignment & eGRC Case Creation"
                        )

                        st.caption(
                            "Assign the appropriate ORE PIC. "
                            "The system will prepare an email "
                            "requesting ORE case creation in eGRC."
                        )

                        current_ore_display = (
                            get_ore_pic_display(
                                current_ore_pic
                            )
                        )

                        if (
                            current_ore_display
                            in ORE_PIC_DISPLAY_OPTIONS
                        ):

                            ore_default_index = (
                                ORE_PIC_DISPLAY_OPTIONS.index(
                                    current_ore_display
                                ) + 1
                            )

                        else:

                            ore_default_index = 0

                        selected_ore_display = st.selectbox(
                            "Select ORE PIC",

                            options=[
                                "— Please select ORE PIC —"
                            ]
                            + ORE_PIC_DISPLAY_OPTIONS,

                            index=ore_default_index,

                            key=f"ore_pic_{incident_id}"
                        )

                        if (
                            selected_ore_display
                            != "— Please select ORE PIC —"
                        ):

                            selected_ore_name = (
                                get_ore_pic_name(
                                    selected_ore_display
                                )
                            )

                            selected_ore_email = (
                                get_ore_pic_email(
                                    selected_ore_name
                                )
                            )

                            ore_pic_selections[
                                incident_id
                            ] = {
                                "name":
                                    selected_ore_name,
                                "email":
                                    selected_ore_email
                            }

                            st.success(
                                f"Assigned ORE PIC: "
                                f"{selected_ore_name}"
                            )

                            st.caption(
                                f"ORE PIC Email: "
                                f"{selected_ore_email}"
                            )

                            ore_subject, ore_email_body = (
                                generate_ore_email_draft(
                                    incident_id=incident_id,
                                    risk_title=risk_title,
                                    risk_description=risk_description,
                                    source=source,
                                    severity=severity,
                                    financial_impact=financial_impact,
                                    potential_breach=potential_breach,
                                    attachments=attachments,
                                    ore_pic_name=selected_ore_name,
                                    ore_pic_email=selected_ore_email
                                )
                            )

                            st.session_state[
                                "ore_email_drafts"
                            ][
                                incident_id
                            ] = {
                                "subject":
                                    ore_subject,
                                "body":
                                    ore_email_body
                            }

                            st.markdown(
                                "#### 📧 ORE Email Draft"
                            )

                            st.text_input(
                                "ORE Email To",

                                value=(
                                    f"{selected_ore_name} "
                                    f"<{selected_ore_email}>"
                                ),

                                disabled=True,

                                key=(
                                    f"ore_email_to_"
                                    f"{incident_id}"
                                )
                            )

                            st.text_input(
                                "ORE Email Subject",
                                value=ore_subject,
                                key=(
                                    f"ore_email_subject_"
                                    f"{incident_id}"
                                )
                            )

                            st.text_area(
                                "Email Draft",
                                value=ore_email_body,
                                height=400,
                                key=(
                                    f"ore_email_body_"
                                    f"{incident_id}"
                                )
                            )

                            if attachments:

                                st.info(
                                    "📎 Attachments recorded in the register:\n\n"
                                    + "\n".join(
                                        f"• {item.strip()}"
                                        for item in attachments.split(";")
                                        if item.strip()
                                    )
                                    + "\n\n"
                                    "Attach these files to the email when sending."
                                )

                            else:

                                st.caption(
                                    "📎 No attachments were recorded "
                                    "for this incident."
                                )

                            st.info(
                                "Next step: copy the generated email "
                                "into the bank's approved email client, "
                                "attach the listed supporting documents, "
                                "and send it to the ORE PIC. The ORE PIC "
                                "should then create the corresponding "
                                "ORE case in eGRC."
                            )

                        else:

                            st.warning(
                                "Please select an ORE PIC for this "
                                "incident to generate the ORE eGRC "
                                "case creation email."
                            )

        # ====================================================
        # SAVE ASSESSMENT CHANGES
        # ====================================================

        st.markdown("")

        if st.button(
            "💾 Save Assessment Changes",
            use_container_width=True
        ):

            # --------------------------------------------------------
            # SYNC BOTTOM WORKFLOW ASSIGNMENTS BACK TO EDITED DATAFRAME
            # --------------------------------------------------------

            for (
                assignment_incident_id,
                assignment
            ) in breach_pic_selections.items():

                mask = (
                    edited_df[
                        "Risk Incident ID"
                    ]
                    .astype(str)
                    .str.strip()
                    == clean_value(
                        assignment_incident_id
                    )
                )

                edited_df.loc[
                    mask,
                    "Breach PIC"
                ] = clean_value(
                    assignment.get(
                        "name",
                        ""
                    )
                )

            for (
                assignment_incident_id,
                policy_text
            ) in policy_selections.items():

                mask = (
                    edited_df[
                        "Risk Incident ID"
                    ]
                    .astype(str)
                    .str.strip()
                    == clean_value(
                        assignment_incident_id
                    )
                )

                edited_df.loc[
                    mask,
                    "Policies / Regulations Breached"
                ] = clean_value(
                    policy_text
                )

            for (
                assignment_incident_id,
                assignment
            ) in ore_pic_selections.items():

                mask = (
                    edited_df[
                        "Risk Incident ID"
                    ]
                    .astype(str)
                    .str.strip()
                    == clean_value(
                        assignment_incident_id
                    )
                )

                edited_df.loc[
                    mask,
                    "ORE PIC"
                ] = clean_value(
                    assignment.get(
                        "name",
                        ""
                    )
                )

            # Save from the synchronised dataframe.

            for _, edited_row in edited_df.iterrows():

                incident_id = clean_value(
                    edited_row[
                        "Risk Incident ID"
                    ]
                )

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

                # ------------------------------------------------
                # POTENTIAL BREACH
                # ------------------------------------------------

                potential_breach = clean_value(
                    edited_row[
                        "Potential Breach"
                    ]
                )

                df.loc[
                    original_index,
                    "Potential Breach"
                ] = potential_breach

                # ------------------------------------------------
                # BREACH PIC
                # ------------------------------------------------

                if (
                    potential_breach.lower()
                    == "yes"
                ):

                    if (
                        incident_id
                        in breach_pic_selections
                    ):

                        df.loc[
                            original_index,
                            "Breach PIC"
                        ] = (
                            breach_pic_selections[
                                incident_id
                            ]["name"]
                        )

                    else:

                        df.loc[
                            original_index,
                            "Breach PIC"
                        ] = clean_value(
                            df.loc[
                                original_index,
                                "Breach PIC"
                            ]
                        )

                else:

                    df.loc[
                        original_index,
                        "Breach PIC"
                    ] = ""

                # ------------------------------------------------
                # POLICIES
                # ------------------------------------------------

                if (
                    potential_breach.lower()
                    == "yes"
                ):

                    if (
                        incident_id
                        in policy_selections
                    ):

                        df.loc[
                            original_index,
                            "Policies / Regulations Breached"
                        ] = (
                            policy_selections[
                                incident_id
                            ]
                        )

                    else:

                        df.loc[
                            original_index,
                            "Policies / Regulations Breached"
                        ] = clean_value(
                            df.loc[
                                original_index,
                                "Policies / Regulations Breached"
                            ]
                        )

                else:

                    df.loc[
                        original_index,
                        "Policies / Regulations Breached"
                    ] = ""

                # ------------------------------------------------
                # ORE REPORTABILITY
                # ------------------------------------------------

                ore_reportability = clean_value(
                    edited_row[
                        "ORE Reportability"
                    ]
                )

                df.loc[
                    original_index,
                    "ORE Reportability"
                ] = ore_reportability

                # ------------------------------------------------
                # ORE PIC
                # ------------------------------------------------

                if (
                    ore_reportability.lower()
                    == "yes"
                ):

                    if (
                        incident_id
                        in ore_pic_selections
                    ):

                        df.loc[
                            original_index,
                            "ORE PIC"
                        ] = (
                            ore_pic_selections[
                                incident_id
                            ]["name"]
                        )

                    else:

                        df.loc[
                            original_index,
                            "ORE PIC"
                        ] = clean_value(
                            df.loc[
                                original_index,
                                "ORE PIC"
                            ]
                        )

                else:

                    df.loc[
                        original_index,
                        "ORE PIC"
                    ] = ""

                    # Do not keep an ORE case ID if the incident
                    # is no longer reportable.

                    df.loc[
                        original_index,
                        "ORE Case ID"
                    ] = ""

                # ------------------------------------------------
                # ORE CASE ID
                # ------------------------------------------------

                if (
                    ore_reportability.lower()
                    == "yes"
                ):

                    df.loc[
                        original_index,
                        "ORE Case ID"
                    ] = clean_value(
                        edited_row[
                            "ORE Case ID"
                        ]
                    )

                # ------------------------------------------------
                # AUTO STATUS
                # ------------------------------------------------

                saved_breach_pic = clean_value(
                    df.loc[
                        original_index,
                        "Breach PIC"
                    ]
                )

                saved_ore_pic = clean_value(
                    df.loc[
                        original_index,
                        "ORE PIC"
                    ]
                )

                breach_pic_assigned = bool(
                    saved_breach_pic
                )

                ore_pic_assigned = bool(
                    saved_ore_pic
                )

                if (
                    (
                        potential_breach.lower()
                        == "yes"
                        and breach_pic_assigned
                    )
                    or
                    (
                        ore_reportability.lower()
                        == "yes"
                        and ore_pic_assigned
                    )
                ):

                    df.loc[
                        original_index,
                        "Status"
                    ] = "Pending Review"

                elif (
                    potential_breach.lower()
                    == "no"
                    and ore_reportability.lower()
                    == "no"
                ):

                    df.loc[
                        original_index,
                        "Status"
                    ] = "Closed"

                else:

                    current_status = clean_value(
                        df.loc[
                            original_index,
                            "Status"
                        ]
                    )

                    df.loc[
                        original_index,
                        "Status"
                    ] = (
                        current_status
                        or "Open"
                    )

            df = df.fillna("")

            for column in COLUMNS:

                df[column] = (
                    df[column].astype(str)
                )

            save_data(df)

            st.session_state[
                "preserved_edits"
            ] = None

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

        st.info(
            "No risk incidents recorded yet."
        )

    else:

        stats_df = df.copy()

        stats_df["Created"] = pd.to_datetime(
            stats_df[
                "Date & Time of Creation"
            ],
            errors="coerce"
        )

        stats_df = stats_df.dropna(
            subset=["Created"]
        )

        stats_df["Breach_Yes"] = (
            stats_df[
                "Potential Breach"
            ]
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        ).astype(int)

        stats_df["ORE_Yes"] = (
            stats_df[
                "ORE Reportability"
            ]
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        ).astype(int)

        period = st.radio(
            "View by",
            [
                "Day",
                "Week",
                "Month",
                "Year"
            ],
            horizontal=True
        )

        if period == "Day":

            stats_df["Period"] = (
                stats_df[
                    "Created"
                ].dt.date
            )

        elif period == "Week":

            stats_df["Period"] = (
                stats_df[
                    "Created"
                ]
                .dt.to_period("W")
                .apply(
                    lambda p:
                        p.start_time.date()
                )
            )

        elif period == "Month":

            stats_df["Period"] = (
                stats_df[
                    "Created"
                ]
                .dt.to_period("M")
                .astype(str)
            )

        else:

            stats_df["Period"] = (
                stats_df[
                    "Created"
                ]
                .dt.to_period("Y")
                .astype(str)
            )

        summary = (
            stats_df
            .groupby("Period")[
                [
                    "Breach_Yes",
                    "ORE_Yes"
                ]
            ]
            .sum()
            .rename(
                columns={
                    "Breach_Yes":
                        "Potential Breach = Yes",

                    "ORE_Yes":
                        "ORE Reportability = Yes"
                }
            )
            .sort_index()
        )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">
                        {
                            int(
                                summary[
                                    "Potential Breach = Yes"
                                ].sum()
                            )
                        }
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
                        {
                            int(
                                summary[
                                    "ORE Reportability = Yes"
                                ].sum()
                            )
                        }
                    </div>
                    <div class="metric-label">
                        Total Reportable ORE
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")

        st.subheader(
            f"Trend by {period}"
        )

        st.bar_chart(
            summary
        )

        st.subheader(
            "Detailed Breakdown"
        )

        st.dataframe(
            summary,
            use_container_width=True
        )