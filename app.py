import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid


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
    "Status",
    "Potential Breach",
    "Breach PIC",
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

        return pd.DataFrame(columns=COLUMNS)

    try:

        df = pd.read_csv(
            DATA_FILE,
            dtype=str,
            keep_default_na=False
        )

    except Exception as e:

        st.error(f"Unable to read CSV file: {e}")

        return pd.DataFrame(columns=COLUMNS)

    # Make sure all columns exist
    for column in COLUMNS:

        if column not in df.columns:

            df[column] = ""

    # Keep correct column order
    df = df[COLUMNS].copy()

    # Replace blanks / NaN
    df = df.fillna("")

    # IMPORTANT:
    # Force ALL columns to text.
    # This prevents the FLOAT problem in data_editor.
    for column in COLUMNS:

        df[column] = df[column].astype(str)

    return df


# ============================================================
# SAVE DATA
# ============================================================

def save_data(df):

    df = df.copy()

    df = df.fillna("")

    for column in COLUMNS:

        df[column] = df[column].astype(str)

    df.to_csv(
        DATA_FILE,
        index=False
    )


# ============================================================
# GENERATE INCIDENT ID
# ============================================================

def generate_incident_id():

    date_part = datetime.now().strftime("%Y%m%d")

    random_part = uuid.uuid4().hex[:6].upper()

    return f"RI-{date_part}-{random_part}"


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

    st.markdown("## 🔴 Risk Incident Register")

    st.markdown("---")

    st.markdown("### Navigation")

    page = st.radio(
        "Select module",
        [
            "Dashboard",
            "Create Risk Incident"
        ]
    )

    st.markdown("---")

    st.markdown("### Business Units")

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
# ============================================================
# CREATE RISK INCIDENT
# ============================================================
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
        placeholder="Enter a short title for the risk incident"
    )


    risk_description = st.text_area(
        "Risk Description *",
        placeholder="Provide a detailed description of the risk incident...",
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

        # Validation

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

                # --------------------------------------------
                # EMPTY ASSESSMENT FIELDS
                # --------------------------------------------

                "Status":
                    "Open",

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

                "Attachments":
                    "; ".join(attachment_names)
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
            # FORCE STRING TYPE
            # ------------------------------------------------

            df = df.fillna("")

            for column in COLUMNS:

                df[column] = (
                    df[column]
                    .astype(str)
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
# ============================================================
# DASHBOARD
# ============================================================
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
            df["Status"].str.strip().str.lower()
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
            f'<div class="metric-card"><div class="metric-value">{total_incidents}</div>'
            f'<div class="metric-label">Total Risk Incidents</div></div>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{open_incidents}</div>'
            f'<div class="metric-label">Open Incidents</div></div>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{potential_breaches}</div>'
            f'<div class="metric-label">Potential Breaches</div></div>',
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{reportable_ore}</div>'
            f'<div class="metric-label">Reportable ORE</div></div>',
            unsafe_allow_html=True
        )


    # ========================================================
    # SOURCE / SEVERITY SUMMARY
    # ========================================================

    if len(df) > 0:

        st.markdown("---")

        chart_col1, chart_col2 = st.columns(2)


        with chart_col1:

            st.subheader("Incidents by Source")

            source_counts = (
                df["Source of Register"]
                .value_counts()
            )

            st.bar_chart(
                source_counts
            )


        with chart_col2:

            st.subheader("Incidents by Severity")

            severity_counts = (
                df["Severity"]
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


    # ========================================================
    # APPLY FILTERS
    # ========================================================

    filtered_df = df.copy()


    # Source

    if source_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Source of Register"
            ].isin(source_filter)
        ]


    # Severity

    if severity_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Severity"
            ].isin(severity_filter)
        ]


    # Financial Impact

    if financial_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Financial Impact"
            ].isin(financial_filter)
        ]


    # Potential Breach

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


    # ORE Reportability

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


    # Search

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

        Make your changes directly in the table and click
        <strong>Save Assessment Changes</strong>.

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # PREPARE TABLE
    # ========================================================

    if len(filtered_df) == 0:

        st.info(
            "No risk incidents match the selected filters."
        )

    else:

        # Latest 10 incidents
        recent_df = (
            filtered_df
            .tail(10)
            .iloc[::-1]
            .copy()
        )


        # VERY IMPORTANT
        # Convert every column to string BEFORE data_editor

        recent_df = recent_df.fillna("")

        for column in COLUMNS:

            recent_df[column] = (
                recent_df[column]
                .astype(str)
            )


        # ====================================================
        # EDITABLE DATA EDITOR
        # ====================================================

        edited_df = st.data_editor(

            recent_df,

            use_container_width=True,

            hide_index=True,

            num_rows="fixed",

            height=500,

            key="risk_incident_editor",

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

                # --------------------------------------------
                # LOCKED
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

                "Attachments":
                    st.column_config.TextColumn(
                        "Attachments",
                        disabled=True,
                        width="medium"
                    ),


                # --------------------------------------------
                # EDITABLE STATUS
                # --------------------------------------------

                "Status":
                    st.column_config.SelectboxColumn(
                        "Status",
                        options=STATUS_OPTIONS,
                        required=True,
                        width="medium"
                    ),


                # --------------------------------------------
                # EDITABLE POTENTIAL BREACH
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
                # EDITABLE BREACH PIC
                # --------------------------------------------

                "Breach PIC":
                    st.column_config.TextColumn(
                        "Breach PIC",
                        disabled=False,
                        width="medium"
                    ),


                # --------------------------------------------
                # EDITABLE ORE REPORTABILITY
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
                # EDITABLE ORE PIC
                # --------------------------------------------

                "ORE PIC":
                    st.column_config.TextColumn(
                        "ORE PIC",
                        disabled=False,
                        width="medium"
                    ),


                # --------------------------------------------
                # EDITABLE ORE CASE ID
                # --------------------------------------------

                "ORE Case ID":
                    st.column_config.TextColumn(
                        "ORE Case ID",
                        disabled=False,
                        width="medium"
                    )
            }
        )


        # ====================================================
        # SAVE ASSESSMENT CHANGES
        # ====================================================

        st.markdown("")


        if st.button(
            "💾 Save Assessment Changes"
        ):

            editable_columns = [

                "Status",
                "Potential Breach",
                "Breach PIC",
                "ORE Reportability",
                "ORE PIC",
                "ORE Case ID"
            ]


            # -----------------------------------------------
            # UPDATE MASTER DATA
            # -----------------------------------------------

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


                original_index = matching_rows[0]


                # -------------------------------------------
                # Update only editable fields
                # -------------------------------------------

                for column in editable_columns:

                    value = edited_row[column]


                    if pd.isna(value):

                        value = ""


                    df.loc[
                        original_index,
                        column
                    ] = str(value)


            # -----------------------------------------------
            # FORCE TEXT
            # -----------------------------------------------

            df = df.fillna("")

            for column in COLUMNS:

                df[column] = (
                    df[column]
                    .astype(str)
                )


            # -----------------------------------------------
            # SAVE CSV
            # -----------------------------------------------

            save_data(df)


            st.success(
                "Assessment changes saved successfully."
            )


            st.rerun()