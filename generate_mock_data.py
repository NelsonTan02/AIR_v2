import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import random
import uuid


# ============================================================
# CREATE DATA FOLDER
# ============================================================

DATA_FOLDER = Path("data")
DATA_FOLDER.mkdir(exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

SOURCES = {
    "TCC": "Technology Command Centre",
    "SAAM": "Staff Anomaly Activity Monitoring",
    "DLM": "Data Loss Monitoring",
    "ORE": "Operational Risk Events"
}

SEVERITY_OPTIONS = [
    "Low",
    "Medium",
    "High"
]

FINANCIAL_IMPACT_OPTIONS = [
    "Low",
    "Medium",
    "High"
]


# ============================================================
# INCIDENT DESCRIPTIONS FOR MOCK DATA
# ============================================================

INCIDENTS = {

    "TCC": [
        "Microsoft Teams service disruption",
        "Network connectivity interruption",
        "Production server outage",
        "Application performance degradation",
        "Database connection failure",
        "Technology infrastructure alert",
        "System authentication failure",
        "Data centre connectivity issue",
        "Critical application unavailable",
        "Technology monitoring alert"
    ],

    "SAAM": [
        "Unusual staff login activity",
        "Multiple failed authentication attempts",
        "Unusual transaction behaviour",
        "Staff account accessed outside normal hours",
        "Anomalous system access",
        "Unusual privileged account activity",
        "Unexpected staff system access",
        "Suspicious login pattern",
        "Multiple unusual access attempts",
        "Anomalous staff activity detected"
    ],

    "DLM": [
        "Potential data transfer detected",
        "Unusual file movement",
        "Large volume data transfer",
        "Potential confidential data exposure",
        "Data transfer to external destination",
        "Unusual email attachment activity",
        "Potential sensitive document sharing",
        "Large file upload detected",
        "Unusual cloud storage activity",
        "Potential data leakage event"
    ],

    "ORE": [
        "Process failure resulting in operational impact",
        "Customer service disruption",
        "Operational procedure not followed",
        "Processing error identified",
        "Control weakness identified",
        "Operational incident requiring review",
        "Incorrect processing identified",
        "Manual process failure",
        "Operational control exception",
        "Business process disruption"
    ]
}


# ============================================================
# CREATE MOCK INCIDENTS
# ============================================================

def generate_incident_id():

    date_part = datetime.now().strftime("%Y%m%d")

    unique_part = uuid.uuid4().hex[:6].upper()

    return f"RI-{date_part}-{unique_part}"


all_records = []


for source, source_description in SOURCES.items():

    for i in range(10):

        created_time = (
            datetime.now()
            - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23)
            )
        )

        incident = {

            "Risk Incident ID":
                generate_incident_id(),

            "Risk Title":
                INCIDENTS[source][i],

            "Risk Description":
                (
                    f"Mock incident generated for "
                    f"{source_description}. "
                    f"This is sample data for testing "
                    f"the centralised risk incident register."
                ),

            "Source of Register":
                source,

            "Severity":
                random.choice(
                    SEVERITY_OPTIONS
                ),

            "Financial Impact":
                random.choice(
                    FINANCIAL_IMPACT_OPTIONS
                ),

            "Date & Time of Creation":
                created_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            # ------------------------------------------------
            # ASSESSMENT FIELDS
            # Initially empty
            # ------------------------------------------------

            "Potential Breach":
                "",

            "Breach PIC":
                "",

            "ORE Reportability":
                "",

            "ORE PIC":
                "",

            "ORE Case ID":
                "",

            # ------------------------------------------------
            # ATTACHMENTS
            # ------------------------------------------------

            "Attachments":
                ""
        }

        all_records.append(incident)


# ============================================================
# MASTER DATASET
# ============================================================

df = pd.DataFrame(
    all_records
)


# ============================================================
# SAVE INDIVIDUAL SOURCE FILES
# ============================================================

for source in SOURCES:

    source_df = df[
        df["Source of Register"] == source
    ].copy()

    source_file = (
        DATA_FOLDER /
        f"{source.lower()}_mock.csv"
    )

    source_df.to_csv(
        source_file,
        index=False
    )

    print(
        f"Created {source_file}"
    )


# ============================================================
# SAVE CONSOLIDATED REGISTER
# ============================================================

master_file = (
    DATA_FOLDER /
    "risk_incident_register.csv"
)

df.to_csv(
    master_file,
    index=False
)


print()
print("=" * 60)
print("MOCK DATA CREATED SUCCESSFULLY")
print("=" * 60)
print()
print(
    f"Total incidents: {len(df)}"
)
print()

for source in SOURCES:

    count = len(
        df[
            df["Source of Register"] == source
        ]
    )

    print(
        f"{source}: {count} incidents"
    )

print()
print(
    f"Master file: {master_file}"
)