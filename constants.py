from pathlib import Path

# ============================================================
# FILE LOCATIONS
# ============================================================

DATA_FOLDER = Path("data")
ATTACHMENT_FOLDER = Path("attachments")
ASSETS = Path("assets")

DATA_FOLDER.mkdir(exist_ok=True)
ATTACHMENT_FOLDER.mkdir(exist_ok=True)
ASSETS.mkdir(exist_ok=True)

DATA_FILE = DATA_FOLDER / "risk_incident_register.csv"
BREACH_PIC_FILE = DATA_FOLDER / "breach_pic.csv"
ORE_PIC_FILE = DATA_FOLDER / "ore_pic.csv"
OCBC_LOGO = ASSETS / "logo_ocbc.png"

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

# To be excluded from the main dashboard table view, as they are source-specific columns
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

EDITABLE_COLS = [

    "Status",
    "Potential Breach",
    "Breach PIC",
    "Policies / Regulations Breached",
    "ORE Reportability",
    "ORE PIC",
    "ORE Case ID"
]