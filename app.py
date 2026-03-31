import streamlit as st
import functions
import database
import json
import pandas as pd
import io
def generate_template(columns):
    df = pd.DataFrame(columns=columns)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return buffer.getvalue()

# UPDATED: Import timezone directly
from datetime import datetime, timezone, timedelta
import re  # <-- Import for email validation
from streamlit_option_menu import option_menu  # <-- Import the new menu

# --- Import page files ---
import page_projects
import page_teams
import page_auth
import page_about  # <-- NEW: Import the about page

# --- NEW: Import Analysis Service ---
from services.analysis_service import AnalysisService
analysis_service_instance = AnalysisService()

# --- APP CONFIGURATION ---
st.set_page_config(page_title="HYDROSYNC", page_icon="logo.png", layout="wide")

# --- CUSTOM CSS INJECTION (SIDEBAR) ---
# (Keep existing CSS blocks for sidebar and global styles - unchanged)
st.markdown(
    """
    <style>
        /* Modern Web Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        
        /* Hide the sidebar close button */
        button[kind="header"][aria-label="Close"] { display: none; }
        
        /* Sidebar layout & custom scrollbar */
        [data-testid="stSidebar"] > div:first-child { 
            display: flex; flex-direction: column; height: calc(100vh - 2rem); 
            background: linear-gradient(180deg, #101827 0%, #0B111A 100%);
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        .menu-container { flex-grow: 1; padding-top: 1rem; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

        /* General Typography */
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        h1, h2, h3, h4, h5, h6 { color: #F8FAFC !important; font-weight: 800 !important; letter-spacing: -0.02em; }
        p, span, label { color: #CBD5E1; }
        
        /* Headers & Dividers */
        .main h1, .main h2, .main h3 { 
            &:not(.auth-container h1):not(.auth-container h2):not(.auth-container h3) { 
                border-bottom: 2px solid rgba(255,255,255,0.05); 
                padding-bottom: 12px; margin-bottom: 2rem; 
            } 
        }

        /* Glassmorphism Containers (Metrics, Forms, Expanders) */
        [data-testid="stMetric"], [data-testid="stForm"], [data-testid="stExpander"], .st-emotion-cache-12w0qpk:not(.auth-container) { 
            background: rgba(30, 41, 59, 0.4) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-radius: 16px !important; 
            border: 1px solid rgba(255, 255, 255, 0.08) !important; 
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        [data-testid="stMetric"]:hover, [data-testid="stExpander"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.15) !important; 
        }
        [data-testid="stMetric"] { padding: 24px !important; }
        [data-testid="stForm"] { padding: 32px !important; }

        /* Modern Inputs & Selectors */
        [data-testid="stTextInput"] > div > div > input, [data-testid="stNumberInput"] > div > div > input { 
            background: rgba(15, 23, 42, 0.6) !important; 
            border-radius: 12px !important; 
            border: 1px solid rgba(255,255,255,0.1) !important; 
            color: #F8FAFC !important; padding: 12px !important; 
            transition: all 0.2s ease;
        }
        [data-testid="stTextInput"] > div > div > input:focus, [data-testid="stNumberInput"] > div > div > input:focus { 
            border-color: #38BDF8 !important; 
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important; 
        }
        [data-testid="stSelectbox"] > label { color: #94A3B8 !important; font-size: 0.85em !important; letter-spacing: 0.05em; }
        [data-testid="stSelectbox"] > div > div > div { 
            background: rgba(15, 23, 42, 0.6) !important; 
            border-radius: 12px !important; 
            border: 1px solid rgba(255,255,255,0.1) !important; 
        }

        /* Oceanic Buttons */
        [data-testid="stButton"] > button, [data-testid="stFormSubmitButton"] > button { 
            border-radius: 12px !important; 
            border: none !important; 
            background: linear-gradient(135deg, #0284C7 0%, #38BDF8 100%) !important; 
            color: #FFFFFF !important; 
            padding: 8px 24px !important; 
            font-weight: 600 !important; 
            box-shadow: 0 4px 14px 0 rgba(2, 132, 199, 0.39) !important;
            transition: all 0.3s ease !important; 
        }
        [data-testid="stButton"] > button:hover, [data-testid="stFormSubmitButton"] > button:hover { 
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(2, 132, 199, 0.5) !important;
            filter: brightness(1.1);
        }
        
        /* Secondary / Destructive Buttons */
        [data-testid="stButton"] > button[kind="primary"] { 
            background: linear-gradient(135deg, #E11D48 0%, #FB7185 100%) !important; 
            box-shadow: 0 4px 14px 0 rgba(225, 29, 72, 0.39) !important;
        }
        [data-testid="stButton"] > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(225, 29, 72, 0.5) !important;
        }

        /* Certificate Highlights */
        [data-testid="stApp"] div:has(> [data-testid="stSuccess"]) > .st-emotion-cache-12w0qpk { 
            border: 1px solid #38BDF8 !important; 
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.1);
        }
        [data-testid="stDataFrame"] { border-radius: 16px !important; overflow: hidden !important; border: 1px solid rgba(255,255,255,0.05); }
        
        /* Match Expander Summaries */
        [data-testid="stExpander"] > summary { font-weight: 600 !important; font-size: 1.05em !important; color: #E2E8F0 !important; }

        /* Footer */
        .footer {
            width: 100%; background: transparent;
            border-top: 1px solid rgba(255,255,255,0.05);
            padding: 2rem 1rem; margin-top: 5rem;
            text-align: center;
        }
        .footer p { font-size: 0.85em; color: #64748B; }
        .footer .dept-name { font-size: 0.95em; font-weight: 600; color: #94A3B8; margin-bottom: 0.5rem; letter-spacing: 0.05em; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- INITIALIZE DATABASE ---
database.create_tables()

# --- SESSION MANAGEMENT ---
# Initialize core state variables if they don't exist
if "page" not in st.session_state: st.session_state.page = "home"
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = ""
if "user_id" not in st.session_state: st.session_state.user_id = 0
# Ensure sub-page states for callbacks exist
if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'current_project_name' not in st.session_state: st.session_state.current_project_name = None
if 'current_team' not in st.session_state: st.session_state.current_team = None
if 'current_team_name' not in st.session_state: st.session_state.current_team_name = None


# --- HELPER FUNCTIONS ---
def navigate(page_name):
    """
    Switches the app's main page state AND resets sub-page states
    to ensure navigation back to list views.
    """
    page_changed = st.session_state.page != page_name
    st.session_state.page = page_name

    # If page changed OR user clicked Projects/Teams, reset sub-states
    if page_changed or page_name in ["projects", "teams"]:
        st.session_state.current_project = None
        st.session_state.current_project_name = None
        st.session_state.current_team = None
        st.session_state.current_team_name = None

    # Clear query params as they are not the primary navigation method
    current_params = st.query_params.to_dict()
    if "view_project_id" in current_params: del st.query_params["view_project_id"]
    if "view_team_id" in current_params: del st.query_params["view_team_id"]


# --- UPDATED: Footer Function ---
def show_footer():
    """Displays the app footer with department logo and info."""
    st.markdown(
        f"""
        <div class="footer">
            <!-- Logo removed as requested -->
            <p class="dept-name">Department of Information Technology - FMSC</p>
            <p>© {datetime.now().year} HydroSync. All Rights Reserved.</p>
            <p>University of Sri Jayewardenepura.</p>
        </div>
        """,
        unsafe_allow_html=True  # <-- THIS IS THE CRITICAL FIX
    )


# --- format_timestamp, get_clean_cert_id, Interpretation funcs (unchanged) ---
def format_timestamp(ts_input):
    if ts_input is None: return "N/A"
    try:
        if isinstance(ts_input, datetime):
            dt = ts_input
        elif isinstance(ts_input, str):
            dt = datetime.fromisoformat(ts_input.replace('Z', '+00:00'))
        else:
            return str(ts_input)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%b %d, %Y - %I:%M %p %Z")
    except (ValueError, TypeError) as e:
        print(f"Error formatting: {e}"); return str(ts_input)


def get_clean_cert_id(cert_id_input):
    if cert_id_input is None: return ""
    cert_id_str = str(cert_id_input).strip();
    return cert_id_str[3:] if cert_id_str.startswith("#0x") else cert_id_str


from utils.interpretations import get_simpson_interpretation, get_pielou_interpretation, get_richness_interpretation, get_plankton_interpretation

# --- PAGE ROUTING ---

# --- PRE-LOGIN AREA ---
if not st.session_state.logged_in:
    current_page = st.session_state.page
    if current_page == "login":
        page_auth.show_login()
    elif current_page == "register":
        page_auth.show_register()
    elif current_page == "hydroscan":
        # Public HydroScan (CORRECTED to use safe access)
        st.title("HYDROSCAN Public Ledger")
        st.write("Verify calculation certificate.")
        cert_id_input = st.text_input("Certificate ID:", placeholder="e.g., #0xa4b...")
        if st.button("Search"):
            if not cert_id_input:
                st.warning("Enter ID.")
            else:
                clean_id = get_clean_cert_id(cert_id_input);
                record = database.get_calc_by_certificate(clean_id)
                if record:
                    st.success("**Verified Calculation**")
                    with st.container(border=True):
                        # Use safe access record['key'] if 'key' in record.keys() else 'default'
                        calc_type = record['calculation_type'] if 'calculation_type' in record.keys() else 'N/A'
                        st.subheader(f"Type: {calc_type}")
                        proj_name = record['project_name'] if 'project_name' in record.keys() else None
                        if proj_name: st.info(f"Project: **{proj_name}**")
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Result", record['result'] if 'result' in record.keys() else 'N/A')
                        with col2:
                            st.caption("On:"); st.subheader(
                                format_timestamp(record['timestamp'] if 'timestamp' in record.keys() else None))
                        interpretation = "";
                        result_val = None  # Interpretation (code unchanged)
                        try:
                            result_str = record['result'] if 'result' in record.keys() else None
                            if result_str: result_val = float(result_str)
                            calc_t = record['calculation_type'] if 'calculation_type' in record.keys() else None
                            if result_val is not None and calc_t:
                                if calc_t == "Simpson’s Diversity Index":
                                    interpretation = get_simpson_interpretation(result_val)
                                elif calc_t == "Pielou’s Evenness":
                                    interpretation = get_pielou_interpretation(result_val)
                                elif calc_t == "Margalef’s Richness Index":
                                    interpretation = get_richness_interpretation(result_val)
                        except:
                            interpretation = "Interpret error."
                        if interpretation: st.info(f"**Interpretation:** {interpretation}")
                        st.caption("Certificate ID:");
                        cert_id = record['certificate_id'] if 'certificate_id' in record.keys() else 'N/A';
                        st.code(f"#0x{cert_id}", language=None)
                        st.caption("Inputs:");
                        inputs_json = record[
                            'inputs_json'] if 'inputs_json' in record.keys() else None  # Inputs display (code unchanged)
                        if inputs_json:
                            try:
                                inputs = json.loads(inputs_json)
                                if "species_data" in inputs:
                                    st.dataframe(pd.DataFrame(inputs["species_data"]), use_container_width=True,
                                                 hide_index=True)
                                else:
                                    st.json(inputs)
                            except:
                                st.error("Inputs error.")
                        else:
                            st.warning("Inputs missing.")
                else:
                    st.error("**Certificate invalid.**")
        st.markdown("---")
        if st.button("Back to Home"): navigate("home"); st.rerun()
    else:  # Default to home
        if st.session_state.page != "home": st.session_state.page = "home"; st.rerun()
        page_auth.show_home()

    show_footer()  # <-- NEW: Show footer on all pre-login pages


# --- LOGGED-IN AREA ---
else:
    # --- NAVIGATION SIDEBAR ---
    with st.sidebar:
        st.image("logo.png", use_container_width=True)
        st.header(f"Welcome, {st.session_state.username}!")
        st.markdown('<div class="menu-container">', unsafe_allow_html=True)

        # --- UPDATED: Navigation Pages ---
        pages = ["Dashboard", "My Profile", "Projects", "Teams", "HydroScan", "About Us"]
        page_to_state = {
            "Dashboard": "dashboard", "My Profile": "profile",
            "Projects": "projects", "Teams": "teams", "HydroScan": "hydroscan",
            "About Us": "about"
        }
        state_to_page = {v: k for k, v in page_to_state.items()}

        current_page_state = st.session_state.page
        current_page_name = state_to_page.get(current_page_state, "Dashboard")
        try:
            default_index = pages.index(current_page_name)
        except ValueError:
            default_index = 0

        # --- UPDATED: Added new icon ---
        selected_page = option_menu(
            key="nav_menu_main",
            menu_title=None, options=pages,
            icons=["grid-fill", "person-circle", "archive-fill", "people-fill",
                   "box-fill", "shield-lock-fill", "info-circle-fill"],
            default_index=default_index,
            on_change=lambda key: navigate(page_to_state.get(st.session_state[key], "dashboard")),
            styles={
                "container": {"padding": "0!important", "background-color": "#1A202C"},
                "icon": {"color": "#4299E1", "font-size": "20px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "3px", "color": "#E2E8F0",
                             "--hover-color": "#2D3748"},
                "nav-link-selected": {"background-color": "#4A5568"},
                "nav-item:nth-child(7)": {"margin-bottom": "20px", "border-bottom": "1px solid #2D3748"}
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            keys_to_delete = list(st.session_state.keys());
            for key in keys_to_delete: del st.session_state[key]
            st.session_state.page = "home";
            st.query_params.clear();
            st.rerun()

    # --- MAIN CONTENT ROUTER ---
    current_page = st.session_state.page

    if current_page == "dashboard":
        st.header("HYDROSYNC — Analyzer")
        st.info("Personal Calculations Dashboard.")
        # ... (Dashboard code - unchanged) ...
        function_choice = st.selectbox("Select Function:",
                                       ["Shannon-Wiener Index", "Pielou’s Evenness", "Simpson’s Diversity Index",
                                        "Margalef’s Richness Index", "Plankton Abundance",
                                        "Water Quality & TSI", "Correlation & Heatmap"])
        if function_choice in ["Shannon-Wiener Index", "Pielou’s Evenness", "Simpson’s Diversity Index",
                               "Margalef’s Richness Index"]:
            st.subheader(f"{function_choice}")
            input_meth = st.radio("Input Method", ["Manual Input", "File Upload"], horizontal=True, key=f"method_{function_choice}")
            edited_df = None
            if input_meth == "Manual Input":
                with st.form("indices_form"):
                    st.write("Enter counts:")
                    initial_data = {"Species Name": ["A", "B", "C", "D"], "Count": [12, 5, 8, 3]};
                    df_input = pd.DataFrame(initial_data)
                    edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)
                    submitted = st.form_submit_button("Calculate")
            else:
                st.download_button(label=" Download Empty Template", data=generate_template(["Species Name", "Count"]), file_name="biodiversity_template.xlsx", mime="application/vnd.ms-excel")
                uploaded_file = st.file_uploader("Upload filled Excel/CSV (Must contain 'Count' column)")
                if uploaded_file:
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            edited_df = pd.read_csv(uploaded_file)
                        else:
                            edited_df = pd.read_excel(uploaded_file)
                        st.dataframe(edited_df)
                    except Exception as e:
                        st.error("Invalid file format.")
                submitted = st.button("Calculate from File") if uploaded_file else False

            if submitted and edited_df is not None:
                try:  # Calculation, Interpretation, Save logic (unchanged)
                    if "Count" not in edited_df.columns: st.error("Need 'Count' column."); st.stop()
                    counts_series = pd.to_numeric(edited_df["Count"], errors='coerce')
                    if counts_series.isnull().any() or (counts_series < 0).any(): st.error(
                        "Counts must be positive numbers."); st.stop()
                    counts = counts_series[counts_series > 0].astype(int).tolist();
                    S = len(counts);
                    N = sum(counts);
                    result = 0.0
                    if S == 0: st.warning("Need count > 0."); st.stop()
                    if function_choice == "Shannon-Wiener Index":
                        result = 0.0 if N == 0 else functions.shannon_index(counts)
                    elif function_choice == "Pielou’s Evenness":
                        if N == 0 or S < 2:
                            st.warning("Pielou needs >= 2 species."); result = 0.0
                        else:
                            result = functions.pielou_evenness(counts); result = 0.0 if result is None else result
                    elif function_choice == "Simpson’s Diversity Index":
                        if N < 2:
                            st.warning("Simpson needs N >= 2."); result = 0.0
                        else:
                            result = functions.simpson_diversity(counts); result = 0.0 if result is None else result
                    elif function_choice == "Margalef’s Richness Index":
                        if N <= 1:
                            st.warning("Margalef needs N > 1."); result = 0.0
                        else:
                            result = functions.richness_index(counts); result = 0.0 if result is None else result
                    if result is None: st.error("Calculation failed."); result = 0.0
                    st.success(f"**Result: {result:.4f}**")
                    interpretation = "";  # Interpretation logic...
                    if function_choice == "Simpson’s Diversity Index":
                        interpretation = get_simpson_interpretation(result)
                    elif function_choice == "Pielou’s Evenness":
                        if S >= 2: interpretation = get_pielou_interpretation(result)
                    elif function_choice == "Margalef’s Richness Index":
                        if N > 1: interpretation = get_richness_interpretation(result)
                    if interpretation:
                        if isinstance(interpretation, dict):
                            st.info(f"**Interpretation:** {interpretation.get('short', '')}")
                            with st.expander("Explain More"): st.write(interpretation.get('detailed', ''))
                        else:
                            st.info(f"**Interpretation:** {interpretation}")
                    valid_data_df = edited_df[counts_series > 0].copy();
                    inputs_list_of_dicts = valid_data_df.to_dict('records');
                    inputs_dict = {"species_data": inputs_list_of_dicts}
                    cert_id = database.add_calculation(st.session_state.user_id, function_choice, inputs_dict,
                                                       f"{result:.4f}", None, None)
                    if cert_id: st.info("Saved."); st.caption("Certificate ID:"); st.code(f"#0x{cert_id}",
                                                                                          language=None)
                    if S > 0: st.subheader("Visualization"); chart_df = valid_data_df.set_index(
                        "Species Name" if "Species Name" in valid_data_df.columns else valid_data_df.columns[0]); st.bar_chart(chart_df["Count"], color="#4299E1")
                except Exception as e:
                    st.error(f"Error: {e}")
        elif function_choice == "Plankton Abundance":
            st.subheader("Plankton Abundance")
            input_meth = st.radio("Input Method", ["Manual Input", "File Upload"], horizontal=True, key="method_plankton")
            if input_meth == "Manual Input":
                with st.form("plankton_form"):
                    col1, col2 = st.columns(2);
                    with col1:
                        n = st.number_input("Observed (n)", 0, value=10); V = st.number_input("Vol bottle (ml)", 0.1,
                                                                                              value=100.0,
                                                                                              format="%.1f"); V_src = st.number_input(
                            "Vol SRC (ml)", 0.1, value=5.0, format="%.1f")
                    with col2:
                        A_src = st.number_input("SRC area (mm²)", 0.1, value=50.0, format="%.2f"); A_a = st.number_input(
                            "Microscope area (mm²)", 0.01, value=1.0, format="%.2f"); V_d = st.number_input(
                            "Vol filtered (m³)", 0.001, value=1.0, format="%.3f")
                    submitted = st.form_submit_button("Calculate")
                    if submitted:
                        try:
                            if A_a <= 0 or V_d <= 0:
                                st.error("Aa and Vd > 0.")
                            else:
                                N = float(n) * float(V) * (float(V_src) * float(A_src)) / (float(A_a) * float(V_d));
                                st.success(f"**Result: {N:.4f}**")
                                interp = get_plankton_interpretation(N)
                                st.info(f"**Interpretation:** {interp.get('short', '')}")
                                with st.expander("Explain More"): st.write(interp.get('detailed', ''))
                                inputs_dict = {"n": n, "V": V, "V_src": V_src, "A_src": A_src, "A_a": A_a, "V_d": V_d}
                                cert_id = database.add_calculation(st.session_state.user_id, function_choice, inputs_dict,
                                                                   f"{N:.4f}", None, None)
                                if cert_id: st.info("Saved."); st.caption("Certificate ID:"); st.code(f"#0x{cert_id}", language=None)
                        except ZeroDivisionError:
                            st.error("Division by zero.")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.download_button(label=" Download Empty Template", data=generate_template(["n", "V", "V_src", "A_src", "A_a", "V_d"]), file_name="plankton_template.xlsx", mime="application/vnd.ms-excel")
                uploaded_file = st.file_uploader("Upload filled Excel/CSV")
                if uploaded_file:
                    try:
                        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
                        else: df = pd.read_excel(uploaded_file)
                        st.dataframe(df)
                        if st.button("Calculate from File"):
                            for idx, row in df.iterrows():
                                try:
                                    r_n, r_V, r_V_src, r_A_src, r_A_a, r_V_d = row['n'], row['V'], row['V_src'], row['A_src'], row['A_a'], row['V_d']
                                    if r_A_a <= 0 or r_V_d <= 0:
                                        st.error(f"Row {idx}: Aa and Vd > 0.")
                                        continue
                                    N = float(r_n) * float(r_V) * (float(r_V_src) * float(r_A_src)) / (float(r_A_a) * float(r_V_d))
                                    st.success(f"**Row {idx} Result: {N:.4f}**")
                                    inputs_dict = {"n": r_n, "V": r_V, "V_src": r_V_src, "A_src": r_A_src, "A_a": r_A_a, "V_d": r_V_d}
                                    cert_id = database.add_calculation(st.session_state.user_id, function_choice, inputs_dict, f"{N:.4f}", None, None)
                                    if cert_id: st.info(f"Row {idx} Saved."); st.caption("Certificate ID:"); st.code(f"#0x{cert_id}", language=None)
                                except Exception as inner_e:
                                    st.error(f"Error on row {idx}: {inner_e}")
                    except Exception as e:
                        st.error(f"Error processing file. Ensure correct columns: {e}")

        elif function_choice == "Water Quality & TSI":
            st.subheader("Water Quality & TSI")
            input_meth = st.radio("Input Method", ["Manual Input", "File Upload"], horizontal=True, key="method_wq")
            if input_meth == "Manual Input":
                with st.form("wq_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        chl_a = st.number_input("Chlorophyll-a (µg/L)", min_value=0.0, value=10.0, format="%.2f")
                        phosphorus = st.number_input("Total Phosphorus (µg/L)", min_value=0.0, value=50.0, format="%.2f")
                    with col2:
                        secchi = st.number_input("Secchi Depth (m)", min_value=0.0, value=2.0, format="%.2f")
                        nitrogen = st.number_input("Total Nitrogen (µg/L)", min_value=0.0, value=1000.0, format="%.2f")
                    submitted = st.form_submit_button("Calculate")
                    if submitted:
                        try:
                            inputs_data = {
                                "chl_a": chl_a,
                                "phosphorus": phosphorus,
                                "secchi": secchi,
                                "nitrogen": nitrogen
                            }
                            result_data = analysis_service_instance.run_water_quality(inputs_data)
                            
                            st.success("**Water Quality Analysis Complete**")
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                val_chl = result_data.get('TSI (Chlorophyll)')
                                st.metric("TSI (Chlorophyll)", f"{val_chl:.2f}" if val_chl is not None else "N/A")
                            with col_b:
                                val_p = result_data.get('TSI (Phosphorus)')
                                st.metric("TSI (Phosphorus)", f"{val_p:.2f}" if val_p is not None else "N/A")
                            with col_c:
                                val_s = result_data.get('TSI (Secchi)')
                                st.metric("TSI (Secchi)", f"{val_s:.2f}" if val_s is not None else "N/A")
                            
                            interp_chl = result_data.get('TSI Interpretation (Chl)')
                            if interp_chl:
                                st.info(f"**TSI Interpretation:** {interp_chl.get('short', '')}")
                                with st.expander("Explain More"): st.write(interp_chl.get('detailed', ''))
                            
                            np_ratio = result_data.get('N:P Ratio')
                            st.metric("N:P Ratio", f"{np_ratio:.2f}" if np_ratio is not None else "N/A")
                            interp_np = result_data.get('N:P Interpretation')
                            if interp_np:
                                st.info(f"**N:P Interpretation:** {interp_np.get('short', '')}")
                                with st.expander("Explain More"): st.write(interp_np.get('detailed', ''))

                            # Save full results in inputs so history can display them
                            save_inputs = inputs_data.copy()
                            save_inputs["metrics"] = result_data

                            cert_id = database.add_calculation(
                                st.session_state.user_id, 
                                function_choice, 
                                save_inputs,
                                f"{val_chl:.4f}" if val_chl is not None else "0.0", 
                                None, 
                                None
                            )
                            if cert_id: st.info("Saved."); st.caption("Certificate ID:"); st.code(f"#0x{cert_id}", language=None)
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.download_button(label=" Download Empty Template", data=generate_template(["Site_Name", "Chlorophyll-a", "Phosphorus", "Secchi_Depth", "Nitrogen"]), file_name="water_quality_template.xlsx", mime="application/vnd.ms-excel")
                uploaded_file = st.file_uploader("Upload filled Water Quality Excel File")
                if uploaded_file:
                    try:
                        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
                        else: df = pd.read_excel(uploaded_file)
                        st.dataframe(df)
                        if st.button("Calculate from File"):
                            for idx, row in df.iterrows():
                                try:
                                    inputs_data = {
                                        "chl_a": row.get('Chlorophyll-a'),
                                        "phosphorus": row.get('Phosphorus'),
                                        "secchi": row.get('Secchi_Depth'),
                                        "nitrogen": row.get('Nitrogen')
                                    }
                                    result_data = analysis_service_instance.run_water_quality(inputs_data)
                                    val_chl = result_data.get('TSI (Chlorophyll)')
                                    st.success(f"**Row {idx} ({row.get('Site_Name', 'Unknown')}) Processed - TSI(Chl): {val_chl:.2f}**")
                                    
                                    save_inputs = inputs_data.copy()
                                    save_inputs["Site_Name"] = row.get('Site_Name')
                                    save_inputs["metrics"] = result_data
                                    
                                    cert_id = database.add_calculation(
                                        st.session_state.user_id, 
                                        function_choice, 
                                        save_inputs, 
                                        f"{val_chl:.4f}" if val_chl is not None else "0.0", 
                                        None, 
                                        None
                                    )
                                    if cert_id: st.caption(f"Certificate ID: #0x{cert_id}"); st.markdown("---")
                                except Exception as inner_e:
                                    st.error(f"Error on row {idx}: {inner_e}")
                    except Exception as e:
                        st.error(f"Error processing file. Ensure correct columns: {e}")

        elif function_choice == "Correlation & Heatmap":
            st.subheader("Correlation & Heatmap")
            st.info("Explore relationships between multiple metrics on an uploaded dataset.")
            st.download_button(label=" Download Empty Template", data=generate_template(["Site_Name", "Temperature", "pH", "Dissolved_Oxygen", "Conductivity", "Turbidity"]), file_name="correlation_template.xlsx", mime="application/vnd.ms-excel")
            uploaded_file = st.file_uploader("Upload Dataset (Excel format)", key="corr_upload")
            if uploaded_file:
                try:
                    df, corr_matrix, heatmap, insights, full_report = analysis_service_instance.run_correlation_analysis(uploaded_file)
                    st.success("**Analysis Generated Successfully**")
                    
                    st.write("**Correlation Matrix:**")
                    st.dataframe(corr_matrix, use_container_width=True)
                    
                    st.write("**Heatmap visualization:**")
                    st.pyplot(heatmap)
                    
                    st.subheader("🔑 Key Insights")
                    for insight in insights:
                        st.write(f"• {insight}")
                    
                    import io
                    buffer = io.StringIO()
                    buffer.write(full_report)
                    st.download_button(
                        label="Download Full Interpretation Report",
                        data=buffer.getvalue(),
                        file_name="correlation_report.txt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error generating correlation report: {e}")

    elif current_page == "profile":
        st.header(f"{st.session_state.username}'s History")
        st.info("Personal Calculations.")
        calcs = database.get_calcs_by_user(st.session_state.user_id)
        if not calcs:
            st.info("No calculations yet.")
        else:
            map_data = []
            for c in calcs:
                if 'inputs_json' in c.keys() and c['inputs_json']:
                    try:
                        inp = json.loads(c['inputs_json'])
                        if 'lat' in inp and 'lon' in inp:
                            map_data.append({'lat': float(inp['lat']), 'lon': float(inp['lon'])})
                    except: pass
            
            if map_data:
                st.subheader(" Global Sample Map")
                st.map(pd.DataFrame(map_data))
                st.markdown("---")

            # History display (using safe access, unchanged)
            all_types = sorted(list(set([c['calculation_type'] for c in calcs if 'calculation_type' in c.keys()])))
            filter_options = ["All"] + all_types if all_types else ["All"]
            filter_choice = st.selectbox("Filter:", filter_options)
            st.markdown("---")
            filtered_calcs = calcs
            if filter_choice != "All": filtered_calcs = [c for c in calcs if (
                        'calculation_type' in c.keys() and c['calculation_type'] == filter_choice)]
            if not filtered_calcs:
                st.warning("None found.")
            else:
                for record in filtered_calcs:
                    calc_type = record['calculation_type'] if 'calculation_type' in record.keys() else 'N/A'
                    ts = format_timestamp(record['timestamp'] if 'timestamp' in record.keys() else None)
                    exp_label = f"**{calc_type}** — {ts}"
                    with st.expander(exp_label):
                        st.metric("Result", record['result'] if 'result' in record.keys() else 'N/A')
                        interpretation = "";
                        result_val = None  # Interpretation (unchanged)...
                        try:
                            result_str = record['result'] if 'result' in record.keys() else None
                            if result_str: result_val = float(result_str)
                            calc_t = record['calculation_type'] if 'calculation_type' in record.keys() else None
                            if result_val is not None and calc_t:
                                if calc_t == "Simpson’s Diversity Index":
                                    interpretation = get_simpson_interpretation(result_val)
                                elif calc_t == "Pielou’s Evenness":
                                    interpretation = get_pielou_interpretation(result_val)
                                elif calc_t == "Margalef’s Richness Index":
                                    interpretation = get_richness_interpretation(result_val)
                                elif calc_t == "Plankton Abundance":
                                    interpretation = get_plankton_interpretation(result_val)
                        except:
                            interpretation = "Interpret error."
                        if interpretation:
                            if isinstance(interpretation, dict):
                                st.info(f"**Interpretation:** {interpretation.get('short', '')}")
                                with st.expander("Explain More"): st.write(interpretation.get('detailed', ''))
                            else:
                                st.info(f"**Interpretation:** {interpretation}")
                        st.caption("Certificate ID:");
                        cert_id = record['certificate_id'] if 'certificate_id' in record.keys() else 'N/A';
                        st.code(f"#0x{cert_id}", language=None)
                        st.subheader("Inputs:");
                        inputs_json = record[
                            'inputs_json'] if 'inputs_json' in record.keys() else None  # Inputs display (unchanged)...
                        if inputs_json:
                            try:
                                inputs = json.loads(inputs_json)
                                if "species_data" in inputs:
                                    st.dataframe(pd.DataFrame(inputs["species_data"]), use_container_width=True,
                                                 hide_index=True)
                                else:
                                    st.json(inputs)
                            except:
                                st.error("Inputs error.")
                        else:
                            st.warning("Inputs missing.")
                        st.caption("Previous Block:");
                        prev_hash = record['previous_hash'] if 'previous_hash' in record.keys() else 'N/A';
                        hash_prefix = "#0x" if len(prev_hash) == 64 and prev_hash != database.GENESIS_HASH else "";
                        st.code(f"{hash_prefix}{prev_hash}", language=None)

    elif current_page == "hydroscan":
        st.header("HYDROSCAN Ledger")
        st.write("Verify certificate.")
        cert_id_input = st.text_input("Certificate ID:", placeholder="e.g., #0xa4b...")
        if st.button("Search"):
            if not cert_id_input:
                st.warning("Enter ID.")
            else:
                clean_id = get_clean_cert_id(cert_id_input);
                record = database.get_calc_by_certificate(clean_id)
                if record:
                    # HydroScan display (using safe access, unchanged)
                    st.success("**Verified**")
                    with st.container(border=True):
                        calc_type = record['calculation_type'] if 'calculation_type' in record.keys() else 'N/A';
                        st.subheader(f"Type: {calc_type}")
                        proj_name = record['project_name'] if 'project_name' in record.keys() else None;
                        if proj_name: st.info(f"Project: **{proj_name}**")
                        st.markdown("---");
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Result", record['result'] if 'result' in record.keys() else 'N/A')
                        with col2:
                            st.caption("On:"); st.subheader(
                                format_timestamp(record['timestamp'] if 'timestamp' in record.keys() else None))
                        interpretation = "";
                        result_val = None  # Interpretation (unchanged)...
                        try:
                            result_str = record['result'] if 'result' in record.keys() else None
                            if result_str: result_val = float(result_str)
                            calc_t = record['calculation_type'] if 'calculation_type' in record.keys() else None
                            if result_val is not None and calc_t:
                                if calc_t == "Simpson’s Diversity Index":
                                    interpretation = get_simpson_interpretation(result_val)
                                elif calc_t == "Pielou’s Evenness":
                                    interpretation = get_pielou_interpretation(result_val)
                                elif calc_t == "Margaleg’s Richness Index":
                                    interpretation = get_richness_interpretation(result_val)
                        except:
                            interpretation = "Interpret error."
                        if interpretation: st.info(f"**Interpretation:** {interpretation}")
                        st.caption("Certificate ID:");
                        cert_id = record['certificate_id'] if 'certificate_id' in record.keys() else 'N/A';
                        st.code(f"#0x{cert_id}", language=None)
                        st.caption("Inputs:");
                        inputs_json = record[
                            'inputs_json'] if 'inputs_json' in record.keys() else None  # Inputs display (unchanged)...
                        if inputs_json:
                            try:
                                inputs = json.loads(inputs_json)
                                if "species_data" in inputs:
                                    st.dataframe(pd.DataFrame(inputs["species_data"]), use_container_width=True,
                                                 hide_index=True)
                                else:
                                    st.json(inputs)
                            except:
                                st.error("Inputs error.")
                        else:
                            st.warning("Inputs missing.")
                else:
                    st.error("**Invalid ID.**")

    elif current_page == "projects":
        page_projects.show_page(st.session_state.user_id, st.session_state.username)

    elif current_page == "teams":
        page_teams.show_page(st.session_state.user_id, st.session_state.username)

    # --- NEW: Route for About Us page ---
    elif current_page == "about":
        page_about.show_page()

    # Placeholder for other pages
    elif current_page in ["reports", "settings"]:
        current_page_name = state_to_page.get(current_page, "Unknown")
        st.header(f"{current_page_name} Page");
        st.info("Under construction.")

    # Fallback
    else:
        st.header("Error");
        st.error("Invalid page.");
        st.session_state.page = "dashboard";
        st.rerun()

    # --- NEW: Show footer on all logged-in pages (except maybe auth) ---
    if st.session_state.page != "home":  # Avoid double footer on home
        show_footer()

