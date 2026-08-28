import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
from google import genai
import os
from dotenv import load_dotenv


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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

if "ai_breach_result" not in st.session_state:
    st.session_state["ai_breach_result"] = None


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

    # --------------------------------------------------------
    # TCC
    # --------------------------------------------------------

    "TCC_System_Affected",
    "TCC_Downtime_Minutes",
    "TCC_Impact_Type",

    # --------------------------------------------------------
    # SAAM
    # --------------------------------------------------------

    "SAAM_Staff_Name",
    "SAAM_Department",
    "SAAM_Anomaly_Type",

    # --------------------------------------------------------
    # DLM
    # --------------------------------------------------------

    "DLM_Data_Type",
    "DLM_Destination_Channel",
    "DLM_Data_Classification",

    # --------------------------------------------------------
    # ORE
    # --------------------------------------------------------

    "ORE_Process_Affected",

    # --------------------------------------------------------
    # GENERAL ASSESSMENT
    # --------------------------------------------------------

    "Status",
    "Potential Breach",
    "Breach PIC",
    "Policies / Regulations Breached",

    # --------------------------------------------------------
    # ORE ASSESSMENT
    # --------------------------------------------------------

    "ORE Reportability",
    "ORE PIC",
    "ORE Case ID",

    # --------------------------------------------------------
    # ATTACHMENTS
    # --------------------------------------------------------

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
# ORE OPTIONS
# ============================================================

ORE_PROCESS_OPTIONS = [
    "Customer Onboarding",
    "Account Management",
    "Payments",
    "Treasury Operations",
    "Technology Operations",
    "Data Management",
    "Regulatory Reporting",
    "Financial Operations",
    "Other"
]


# ============================================================
# BREACH PIC DIRECTORY
# ============================================================

BREACH_PIC_DIRECTORY = {
    "Alice Tan": "alice.tan@example.com",
    "Benjamin Lim": "benjamin.lim@example.com",
    "Carol Wong": "carol.wong@example.com",
    "Daniel Lee": "daniel.lee@example.com",
    "Emily Ng": "emily.ng@example.com"
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


BREACH_PIC_OPTIONS = [
    f"{name} — {email}"
    for name, email in BREACH_PIC_DIRECTORY.items()
]

ORE_PIC_OPTIONS = [
    f"{name} — {email}"
    for name, email in ORE_PIC_DIRECTORY.items()
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_value(value):
    """
    Safely convert any value to a clean string.

    This is particularly important for Streamlit's data editor
    because blank cells can sometimes become NaN/float values.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def force_string_columns(dataframe, columns=None):
    """
    Force selected columns to contain only Python strings.

    This prevents Streamlit data_editor from interpreting an
    entirely blank column as FLOAT and then rejecting a
    SelectboxColumn/TextColumn configuration.
    """

    df_copy = dataframe.copy()

    target_columns = columns or df_copy.columns.tolist()

    for column in target_columns:

        if column not in df_copy.columns:
            df_copy[column] = ""

        df_copy[column] = (
            df_copy[column]
            .map(clean_value)
            .astype("object")
        )

    return df_copy


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
            "reasoning": (
                "Gemini API key is not configured."
            ),
            "suggested_policies": ""
        }

    prompt = f"""
You are assisting a bank's operational risk team
in triaging a risk incident.

Your role is to provide a preliminary recommendation only.
The final breach determination must be made by the authorised
human reviewer.

Analyze the incident below.

Respond in EXACTLY this plain text format:

Breach: Yes or No
Confidence: Low or Medium or High
Reasoning: 1-2 sentence explanation
Policies: short list of potentially relevant policy,
regulation, procedure, control or regulatory areas,
or leave blank if none can reasonably be identified.

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

        response_text = clean_value(
            getattr(response, "text", "")
        )

        return parse_ai_assessment(response_text)

    except Exception as e:

        return {
            "suggested_potential_breach": "No",
            "confidence": "Low",
            "reasoning": (
                f"AI assessment unavailable: {e}"
            ),
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

    for line in clean_value(text).splitlines():

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

                result[
                    "suggested_potential_breach"
                ] = value

            current_field = None

        elif lower.startswith("confidence:"):

            value = stripped.split(
                ":",
                1
            )[1].strip()

            if value:

                result[
                    "confidence"
                ] = value

            current_field = None

        elif lower.startswith("reasoning:"):

            result[
                "reasoning"
            ] = stripped.split(
                ":",
                1
            )[1].strip()

            current_field = None

        elif lower.startswith("policies:"):

            first_line = stripped.split(
                ":",
                1
            )[1].strip()

            if first_line:
                policy_lines.append(first_line)

            current_field = "policies"

        elif current_field == "policies":

            policy_lines.append(stripped)

    result[
        "suggested_policies"
    ] = "\n".join(policy_lines)

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

    return result.get(
        "suggested_policies",
        ""
    )


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
    ore_process_affected,
    attachments,
    ore_pic_name,
    ore_pic_email
):

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
    ore_process_affected = clean_value(
        ore_process_affected
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

    process_text = (
        ore_process_affected
        or "Not specified"
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

Process Affected:
{process_text}

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

    # ========================================================
    # TCC / SAAM / DLM
    # ========================================================

    if source_type in [
        "TCC",
        "SAAM",
        "DLM"
    ]:

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

    # ========================================================
    # ORE DETAILS
    # ========================================================

    if source_type == "ORE":

        st.markdown("---")
        st.markdown("**ORE Incident Details**")

        st.metric(
            "Process Affected",
            clean_value(
                detail_row.get(
                    "ORE_Process_Affected",
                    ""
                )
            ) or "-"
        )

    # ========================================================
    # ORE ASSESSMENT
    # ========================================================

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

    # ========================================================
    # ASSESSMENT
    # ========================================================

    st.markdown("---")
    st.markdown("**Assessment Information**")

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

        st.session_state[
            "view_table_reset"
        ] += 1

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

.edit-note {{
    background-color: {OCBC_LIGHT_RED};
    border-left: 5px solid {OCBC_RED};
    padding: 14px 18px;
    border-radius: 6px;
    margin-bottom: 18px;
    color: {DARK_GREY};
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
            keep_default_na=False,
            na_filter=False
        )

    except Exception as e:

        st.error(
            f"Unable to read CSV file: {e}"
        )

        return pd.DataFrame(
            columns=COLUMNS
        )

    # --------------------------------------------------------
    # Add missing columns
    # --------------------------------------------------------

    for column in COLUMNS:

        if column not in df.columns:

            df[column] = ""

    # --------------------------------------------------------
    # Keep only expected columns and correct order
    # --------------------------------------------------------

    df = df[COLUMNS].copy()

    # --------------------------------------------------------
    # Convert EVERYTHING to string
    # --------------------------------------------------------

    df = force_string_columns(
        df,
        COLUMNS
    )

    return df


# ============================================================
# SAVE DATA
# ============================================================

def save_data(df):

    df = df.copy()

    # --------------------------------------------------------
    # Add missing columns
    # --------------------------------------------------------

    for column in COLUMNS:

        if column not in df.columns:

            df[column] = ""

    # --------------------------------------------------------
    # Correct column order
    # --------------------------------------------------------

    df = df[COLUMNS].copy()

    # --------------------------------------------------------
    # Force every column to string
    # --------------------------------------------------------

    df = force_string_columns(
        df,
        COLUMNS
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
    # TCC
    # ========================================================

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

    # ========================================================
    # SAAM
    # ========================================================

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

    # ========================================================
    # DLM
    # ========================================================

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

    # ========================================================
    # ORE
    # ========================================================

    if source == "ORE":

        st.markdown(
            """
            <div class="section-header">
                ORE Incident Details
            </div>
            """,
            unsafe_allow_html=True
        )

        ore_process_affected = st.selectbox(
            "Process Affected",
            [""] + ORE_PROCESS_OPTIONS
        )

        st.info(
            "ORE reportability and ORE PIC assignment will be "
            "completed from the Dashboard after the incident "
            "has been created."
        )

    else:

        ore_process_affected = ""

    # ========================================================
    # AI BREACH ASSESSMENT
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
        "Optional: get an AI-generated first pass on whether "
        "this incident may constitute a breach. The AI result "
        "is advisory only and must be reviewed by the authorised "
        "human reviewer."
    )

    if st.button(
        "Get AI Suggestion",
        key="ai_suggest_create"
    ):

        if (
            not clean_value(risk_title)
            or not clean_value(risk_description)
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

            st.session_state[
                "ai_breach_result"
            ] = ai_result

    if st.session_state[
        "ai_breach_result"
    ]:

        ai_result = st.session_state[
            "ai_breach_result"
        ]

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
                {ai_result['suggested_policies']
                    or 'None suggested'}
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

    st.markdown("---")

    if st.button(
        "➕ Create Risk Incident",
        use_container_width=True
    ):

        if not clean_value(risk_title):

            st.error(
                "Please enter the Risk Title."
            )

        elif not clean_value(risk_description):

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

            new_incident = {

                "Risk Incident ID":
                    incident_id,

                "Risk Title":
                    clean_value(risk_title),

                "Risk Description":
                    clean_value(risk_description),

                "Source of Register":
                    clean_value(source),

                "Severity":
                    clean_value(severity),

                "Financial Impact":
                    clean_value(financial_impact),

                "Date & Time of Creation":
                    creation_datetime,

                # TCC
                "TCC_System_Affected":
                    clean_value(tcc_system),

                "TCC_Downtime_Minutes":
                    clean_value(tcc_downtime),

                "TCC_Impact_Type":
                    clean_value(tcc_impact),

                # SAAM
                "SAAM_Staff_Name":
                    clean_value(saam_staff),

                "SAAM_Department":
                    clean_value(saam_department),

                "SAAM_Anomaly_Type":
                    clean_value(saam_anomaly),

                # DLM
                "DLM_Data_Type":
                    clean_value(dlm_data_type),

                "DLM_Destination_Channel":
                    clean_value(dlm_channel),

                "DLM_Data_Classification":
                    clean_value(dlm_classification),

                # ORE
                "ORE_Process_Affected":
                    clean_value(
                        ore_process_affected
                    ),

                # Assessment
                "Status":
                    "Open",

                "Potential Breach":
                    "",

                "Breach PIC":
                    "",

                "Policies / Regulations Breached":
                    "",

                # ORE assessment
                "ORE Reportability":
                    "",

                "ORE PIC":
                    "",

                "ORE Case ID":
                    "",

                # Attachments
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
                [
                    df,
                    new_row
                ],
                ignore_index=True
            )

            save_data(df)

            # Reset AI result
            st.session_state[
                "ai_breach_result"
            ] = None

            st.success(
                f"Risk Incident {incident_id} "
                "has been successfully created."
            )

            if attachment_names:

                st.info(
                    f"{len(attachment_names)} "
                    "attachment(s) saved successfully."
                )

            st.rerun()


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

    # ========================================================
    # METRICS
    # ========================================================

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
    # CHARTS
    # ========================================================

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

    # ========================================================
    # FILTERS
    # ========================================================

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
                "Search incident ID, title, "
                "description, PIC or ORE Case ID"
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
            .map(clean_value)
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
            .map(clean_value)
            .replace(
                "",
                "Not Assessed"
            )
        )

        filtered_df = filtered_df[
            temp.isin(ore_filter)
        ]

    if clean_value(search):

        search_value = (
            clean_value(search)
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
        Policies / Regulations Breached, ORE Reportability,
        ORE PIC and ORE Case ID.
        <br><br>

        <strong>Locked fields:</strong>
        Incident ID, Risk Title, Risk Description, Source,
        Severity, Financial Impact, Creation Date/Time and
        Attachments.
        <br><br>

        <strong>ORE workflow:</strong>
        Set ORE Reportability to <strong>Yes</strong>,
        select an ORE PIC, then use the generated email
        draft to request ORE case creation in eGRC.
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

        # ----------------------------------------------------
        # VERY IMPORTANT:
        # Force all database fields to string
        # ----------------------------------------------------

        recent_df = force_string_columns(
            recent_df,
            COLUMNS
        )

        recent_df = recent_df[
            COLUMNS
        ].copy()

        # ----------------------------------------------------
        # SOURCE SPECIFIC COLUMNS HIDDEN FROM TABLE
        # ----------------------------------------------------

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

            "ORE_Process_Affected"
        ]

        editor_display_df = (
            recent_df
            .drop(
                columns=SOURCE_SPECIFIC_COLUMNS,
                errors="ignore"
            )
            .reset_index(drop=True)
        )

        # ----------------------------------------------------
        # VIEW CHECKBOX
        # ----------------------------------------------------

        editor_display_df.insert(
            0,
            "🔍 View",
            False
        )

        # ----------------------------------------------------
        # EDITABLE COLUMNS
        # ----------------------------------------------------

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
        # FORCE EDITABLE COLUMNS TO STRING
        #
        # THIS IS THE IMPORTANT FIX FOR:
        #
        # StreamlitAPIException:
        # configured column type text/selectbox is not
        # compatible with underlying FLOAT data type
        # ----------------------------------------------------

        for column in EDITABLE_COLS:

            if column in editor_display_df.columns:

                editor_display_df[column] = (
                    editor_display_df[column]
                    .map(clean_value)
                    .astype("object")
                )

        # ----------------------------------------------------
        # REAPPLY UNSAVED EDITS
        # ----------------------------------------------------

        if st.session_state[
            "preserved_edits"
        ]:

            preserved_lookup = {}

            for row in st.session_state[
                "preserved_edits"
            ]:

                row_id = clean_value(
                    row.get(
                        "Risk Incident ID",
                        ""
                    )
                )

                if row_id:

                    preserved_lookup[
                        row_id
                    ] = row

            for i, row in editor_display_df.iterrows():

                current_id = clean_value(
                    row.get(
                        "Risk Incident ID",
                        ""
                    )
                )

                if current_id in preserved_lookup:

                    preserved_row = (
                        preserved_lookup[
                            current_id
                        ]
                    )

                    for column in EDITABLE_COLS:

                        if column in editor_display_df.columns:

                            editor_display_df.at[
                                i,
                                column
                            ] = clean_value(
                                preserved_row.get(
                                    column,
                                    ""
                                )
                            )

                    editor_display_df.at[
                        i,
                        "🔍 View"
                    ] = False

        # ----------------------------------------------------
        # FINAL STRING SAFETY CHECK
        # ----------------------------------------------------

        editor_display_df = force_string_columns(
            editor_display_df,
            [
                column
                for column in EDITABLE_COLS
                if column in editor_display_df.columns
            ]
        )

        # Restore checkbox to bool
        editor_display_df[
            "🔍 View"
        ] = editor_display_df[
            "🔍 View"
        ].astype(bool)

        # ====================================================
        # DATA EDITOR
        # ====================================================

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
                            "details"
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
                    st.column_config.SelectboxColumn(
                        "Status",
                        options=STATUS_OPTIONS,
                        required=True,
                        width="medium"
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

        # ----------------------------------------------------
        # FORCE OUTPUT STRING TYPES
        # ----------------------------------------------------

        edited_df = edited_df.copy()

        for column in EDITABLE_COLS:

            if column in edited_df.columns:

                edited_df[column] = (
                    edited_df[column]
                    .map(clean_value)
                    .astype("object")
                )

        # ----------------------------------------------------
        # PRESERVE CURRENT EDITS
        # ----------------------------------------------------

        st.session_state[
            "preserved_edits"
        ] = edited_df.to_dict(
            "records"
        )

        # ====================================================
        # VIEW INCIDENT POPUP
        # ====================================================

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
        # POTENTIAL BREACH WORKFLOW
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
                <strong>Potential breach incidents detected.</strong>
                <br><br>
                Please select the appropriate Breach PIC for each
                potential breach incident.
                <br><br>
                The breach assessment email draft can then be
                prepared for the assigned Breach PIC.
                </div>
                """,
                unsafe_allow_html=True
            )

            for _, breach_row in yes_breach_df.iterrows():

                incident_id = clean_value(
                    breach_row[
                        "Risk Incident ID"
                    ]
                )

                risk_title = clean_value(
                    breach_row[
                        "Risk Title"
                    ]
                )

                risk_description = clean_value(
                    breach_row[
                        "Risk Description"
                    ]
                )

                source = clean_value(
                    breach_row[
                        "Source of Register"
                    ]
                )

                severity = clean_value(
                    breach_row[
                        "Severity"
                    ]
                )

                financial_impact = clean_value(
                    breach_row[
                        "Financial Impact"
                    ]
                )

                potential_breach = clean_value(
                    breach_row[
                        "Potential Breach"
                    ]
                )

                attachments = clean_value(
                    breach_row[
                        "Attachments"
                    ]
                )

                current_pic = clean_value(
                    breach_row[
                        "Breach PIC"
                    ]
                )

                current_policy = clean_value(
                    breach_row[
                        "Policies / Regulations Breached"
                    ]
                )

                st.markdown(
                    f"""
                    ### Incident: `{incident_id}`

                    **Risk Title:** {risk_title}
                    """
                )

                # ------------------------------------------------
                # BREACH PIC
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
                        "name": selected_name,
                        "email": selected_email
                    }

                    st.success(
                        f"Assigned Breach PIC: "
                        f"{selected_name}"
                    )

                    st.caption(
                        f"Email: {selected_email}"
                    )

                    # ------------------------------------------------
                    # POLICY
                    # ------------------------------------------------

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

                        if suggested_policy:

                            st.session_state[
                                f"policy_{incident_id}"
                            ] = suggested_policy

                            st.rerun()

                        else:

                            st.info(
                                "No specific policy suggestion available."
                            )

                    policy_default = (
                        st.session_state.get(
                            f"policy_{incident_id}",
                            current_policy
                        )
                    )

                    policies_breached = st.text_area(
                        "Enter applicable policies / regulations",
                        value=clean_value(
                            policy_default
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
                    ] = clean_value(
                        policies_breached
                    )

                    # ------------------------------------------------
                    # EMAIL
                    # ------------------------------------------------

                    st.markdown("---")

                    st.markdown(
                        """
                        <div class="email-draft-box">
                        <div class="email-draft-title">
                            📧 Potential Breach Email Draft
                        </div>
                        Draft prepared for the assigned Breach PIC.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    subject = (
                        "Potential Breach Review Required - "
                        f"{incident_id} - {risk_title}"
                    )

                    email_body = f"""To: {selected_name} <{selected_email}>

Subject: {subject}

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
                        height=500,
                        key=(
                            f"breach_email_body_"
                            f"{incident_id}"
                        )
                    )

                else:

                    st.warning(
                        "Please select a Breach PIC to "
                        "generate the email draft."
                    )

                st.markdown("---")

        # ====================================================
        # ORE WORKFLOW
        # ====================================================

        ore_yes_df = edited_df[
            edited_df[
                "ORE Reportability"
            ]
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        ].copy()

        ore_pic_selections = {}

        if len(ore_yes_df) > 0:

            st.markdown("---")

            st.markdown(
                """
                <div class="section-header">
                    🟠 ORE — ORE PIC Assignment & eGRC Case Creation
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <div class="breach-pic-box">
                <strong>Reportable ORE incidents detected.</strong>
                <br><br>
                Please assign an ORE PIC from the approved ORE PIC
                directory.
                <br><br>
                Once an ORE PIC is selected, the system automatically
                drafts an email containing the incident information
                and requests the ORE PIC to create the ORE case in
                the bank's eGRC system.
                <br><br>
                The ORE Case ID can be entered after the ORE PIC
                creates the case in eGRC.
                </div>
                """,
                unsafe_allow_html=True
            )

            for _, ore_row in ore_yes_df.iterrows():

                incident_id = clean_value(
                    ore_row[
                        "Risk Incident ID"
                    ]
                )

                risk_title = clean_value(
                    ore_row[
                        "Risk Title"
                    ]
                )

                risk_description = clean_value(
                    ore_row[
                        "Risk Description"
                    ]
                )

                source = clean_value(
                    ore_row[
                        "Source of Register"
                    ]
                )

                severity = clean_value(
                    ore_row[
                        "Severity"
                    ]
                )

                financial_impact = clean_value(
                    ore_row[
                        "Financial Impact"
                    ]
                )

                potential_breach = clean_value(
                    ore_row[
                        "Potential Breach"
                    ]
                )

                attachments = clean_value(
                    ore_row[
                        "Attachments"
                    ]
                )

                ore_process_affected = clean_value(
                    ore_row.get(
                        "ORE_Process_Affected",
                        ""
                    )
                )

                current_ore_pic = clean_value(
                    ore_row[
                        "ORE PIC"
                    ]
                )

                current_ore_display = (
                    get_ore_pic_display(
                        current_ore_pic
                    )
                )

                if (
                    current_ore_display
                    in ORE_PIC_OPTIONS
                ):

                    ore_default_index = (
                        ORE_PIC_OPTIONS.index(
                            current_ore_display
                        ) + 1
                    )

                else:

                    ore_default_index = 0

                st.markdown(
                    f"""
                    ### ORE Incident: `{incident_id}`

                    **Risk Title:** {risk_title}
                    """
                )

                if ore_process_affected:

                    st.caption(
                        "Process Affected: "
                        f"{ore_process_affected}"
                    )

                selected_ore_display = st.selectbox(
                    "Select ORE PIC",
                    options=[
                        "— Please select ORE PIC —"
                    ] + ORE_PIC_OPTIONS,
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
                        "name": selected_ore_name,
                        "email": selected_ore_email
                    }

                    st.success(
                        f"Assigned ORE PIC: "
                        f"{selected_ore_name}"
                    )

                    st.caption(
                        f"ORE PIC Email: "
                        f"{selected_ore_email}"
                    )

                    # --------------------------------------------
                    # AUTO-GENERATE ORE EMAIL
                    # --------------------------------------------

                    (
                        ore_subject,
                        ore_email_body
                    ) = generate_ore_email_draft(

                        incident_id=incident_id,

                        risk_title=risk_title,

                        risk_description=risk_description,

                        source=source,

                        severity=severity,

                        financial_impact=financial_impact,

                        potential_breach=potential_breach,

                        ore_process_affected=(
                            ore_process_affected
                        ),

                        attachments=attachments,

                        ore_pic_name=(
                            selected_ore_name
                        ),

                        ore_pic_email=(
                            selected_ore_email
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
                        """
                        <div class="email-draft-box">
                        <div class="email-draft-title">
                            📧 ORE Email Draft
                        </div>
                        Draft prepared for the assigned ORE PIC.
                        </div>
                        """,
                        unsafe_allow_html=True
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
                        height=500,
                        key=(
                            f"ore_email_body_"
                            f"{incident_id}"
                        )
                    )

                    if attachments:

                        st.info(
                            "📎 Attachments recorded "
                            "in the register:\n\n"
                            +
                            "\n".join(
                                f"• {item.strip()}"
                                for item
                                in attachments.split(";")
                                if item.strip()
                            )
                            +
                            "\n\n"
                            "Attach these files to the email "
                            "when sending."
                        )

                    else:

                        st.caption(
                            "📎 No attachments were recorded "
                            "for this incident."
                        )

                    st.markdown(
                        """
                        <div class="info-box">
                        <strong>Next step:</strong>
                        Copy the generated email into the bank's
                        approved email client, attach the listed
                        supporting documents, and send it to the
                        ORE PIC. The ORE PIC should then create
                        the corresponding ORE case in eGRC.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:

                    st.warning(
                        "Please select an ORE PIC to generate "
                        "the ORE eGRC case creation email."
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

                # ----------------------------------------------
                # STATUS
                # ----------------------------------------------

                df.loc[
                    original_index,
                    "Status"
                ] = clean_value(
                    edited_row[
                        "Status"
                    ]
                )

                # ----------------------------------------------
                # POTENTIAL BREACH
                # ----------------------------------------------

                potential_breach = clean_value(
                    edited_row[
                        "Potential Breach"
                    ]
                )

                df.loc[
                    original_index,
                    "Potential Breach"
                ] = potential_breach

                # ----------------------------------------------
                # BREACH PIC
                # ----------------------------------------------

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
                        ] = clean_value(
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

                # ----------------------------------------------
                # POLICIES
                # ----------------------------------------------

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
                        ] = clean_value(
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

                # ----------------------------------------------
                # ORE REPORTABILITY
                # ----------------------------------------------

                ore_reportability = clean_value(
                    edited_row[
                        "ORE Reportability"
                    ]
                )

                df.loc[
                    original_index,
                    "ORE Reportability"
                ] = ore_reportability

                # ----------------------------------------------
                # ORE PIC
                # ----------------------------------------------

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
                        ] = clean_value(
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

                    # ------------------------------------------
                    # Clear ORE case if no longer reportable
                    # ------------------------------------------

                    df.loc[
                        original_index,
                        "ORE Case ID"
                    ] = ""

            # =================================================
            # SAVE ORE CASE ID SEPARATELY
            # =================================================

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

            # =================================================
            # NORMALIZE BEFORE SAVE
            # =================================================

            df = force_string_columns(
                df,
                COLUMNS
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

        # ====================================================
        # CREATED DATE
        # ====================================================

        stats_df["Created"] = pd.to_datetime(
            stats_df[
                "Date & Time of Creation"
            ],
            errors="coerce"
        )

        stats_df = stats_df.dropna(
            subset=[
                "Created"
            ]
        )

        # ====================================================
        # BREACH
        # ====================================================

        stats_df[
            "Breach_Yes"
        ] = (
            stats_df[
                "Potential Breach"
            ]
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        ).astype(int)

        # ====================================================
        # ORE
        # ====================================================

        stats_df[
            "ORE_Yes"
        ] = (
            stats_df[
                "ORE Reportability"
            ]
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        ).astype(int)

        # ====================================================
        # PERIOD
        # ====================================================

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

            stats_df[
                "Period"
            ] = stats_df[
                "Created"
            ].dt.date

        elif period == "Week":

            stats_df[
                "Period"
            ] = (
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

            stats_df[
                "Period"
            ] = (
                stats_df[
                    "Created"
                ]
                .dt.to_period("M")
                .astype(str)
            )

        else:

            stats_df[
                "Period"
            ] = (
                stats_df[
                    "Created"
                ]
                .dt.to_period("Y")
                .astype(str)
            )

        # ====================================================
        # SUMMARY
        # ====================================================

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

        # ====================================================
        # METRICS
        # ====================================================

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">
                        {int(
                            summary[
                                "Potential Breach = Yes"
                            ].sum()
                        )}
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
                        {int(
                            summary[
                                "ORE Reportability = Yes"
                            ].sum()
                        )}
                    </div>

                    <div class="metric-label">
                        Total Reportable ORE
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ====================================================
        # TREND
        # ====================================================

        st.markdown("---")

        st.subheader(
            f"Trend by {period}"
        )

        st.bar_chart(
            summary
        )

        # ====================================================
        # DETAILED BREAKDOWN
        # ====================================================

        st.subheader(
            "Detailed Breakdown"
        )

        st.dataframe(
            summary,
            use_container_width=True
        )