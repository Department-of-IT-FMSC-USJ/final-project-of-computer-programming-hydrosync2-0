import streamlit as st
import database
import functions # Import functions for the calculation forms
import pandas as pd
import json
# UPDATED: Import timezone directly
from datetime import datetime, timezone
import io

def generate_template(columns):
    df = pd.DataFrame(columns=columns)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return buffer.getvalue()

# --- Interpretation Helper Functions ---
from utils.interpretations import get_simpson_interpretation, get_pielou_interpretation, get_richness_interpretation, get_plankton_interpretation
from services.analysis_service import AnalysisService

analysis_service_instance = AnalysisService()

# --- HELPER FUNCTIONS ---
def format_timestamp(ts_input):
    """Formats timestamp (string or datetime obj) into readable format."""
    if ts_input is None: return "N/A"
    try:
        if isinstance(ts_input, str): dt = datetime.fromisoformat(ts_input.replace('Z', '+00:00'))
        elif isinstance(ts_input, datetime): dt = ts_input
        else: return str(ts_input)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%b %d, %Y - %I:%M %p %Z")
    except (ValueError, TypeError) as e: print(f"Error formatting timestamp '{ts_input}': {e}"); return str(ts_input)

# --- RE-ADDED Callback function for opening a project ---
def set_current_project(project_id, project_name):
    """Callback to set the current project view in session state."""
    st.session_state.current_project = project_id
    st.session_state.current_project_name = project_name
    # No rerun/stop needed, Streamlit handles it

# --- MAIN PAGE FUNCTION ---
def show_page(user_id, username):
    """
    Renders the entire "Projects" page.
    Uses session state ('current_project') for navigation within the page.
    """

    # --- VIEW 1: INDIVIDUAL PROJECT DASHBOARD ---
    # Check FIRST if we are viewing a specific project using session state
    current_project_id = st.session_state.get('current_project')

    if current_project_id is not None:
        project_id = current_project_id
        # Use name from session state
        project_name = st.session_state.get('current_project_name', 'Unknown Project')

        if st.button("<- Back to All Projects"):
            st.session_state.current_project = None
            st.session_state.current_project_name = None
            st.rerun()
            st.stop() # Stop needed here

        st.header(f"Project: {project_name}")
        st.markdown("---")

        # --- Project Dashboard Tabs ---
        tab1, tab2, tab3, tab4 = st.tabs(["Calculations", "Members & Invites", "Add Calculation", "Project Analytics"])

        # --- TAB 1: Calculations ---
        with tab1:
            st.subheader("Project Calculations")
            project_calcs = database.get_project_calculations(project_id)
            if not project_calcs: st.info("No calculations yet.")
            else:
                for record in project_calcs:
                    # Safe access to record data using dictionary-style access with checks
                    calc_type_display = record['calculation_type'] if 'calculation_type' in record.keys() else 'N/A'
                    timestamp_display = format_timestamp(record['timestamp'] if 'timestamp' in record.keys() else None)
                    exp_label = f"**{calc_type_display}** — {timestamp_display}"
                    with st.expander(exp_label):
                        st.metric("Result", record['result'] if 'result' in record.keys() else 'N/A')
                        interpretation = "" # Interpretation logic...
                        try:
                            result_val_str = record['result'] if 'result' in record.keys() else None
                            if result_val_str is not None:
                                result_val = float(result_val_str)
                                calc_type = record['calculation_type'] if 'calculation_type' in record.keys() else None
                                if calc_type == "Simpson’s Diversity Index": interpretation = get_simpson_interpretation(result_val)
                                elif calc_type == "Pielou’s Evenness": interpretation = get_pielou_interpretation(result_val)
                                elif calc_type == "Margalef’s Richness Index": interpretation = get_richness_interpretation(result_val)
                                elif calc_type == "Plankton Abundance": interpretation = get_plankton_interpretation(result_val)
                            else: interpretation = "Result missing."
                        except (ValueError, TypeError): interpretation = "Could not interpret."
                        if interpretation:
                            if isinstance(interpretation, dict):
                                st.info(f"**Interpretation:** {interpretation.get('short', '')}")
                                with st.expander("Explain More"): st.write(interpretation.get('detailed', ''))
                            else:
                                st.info(f"**Interpretation:** {interpretation}")
                        st.caption("Certificate ID:") # Display Cert ID, Inputs, Prev Hash...
                        cert_id_display = record['certificate_id'] if 'certificate_id' in record.keys() else 'N/A'
                        st.code(f"#0x{cert_id_display}", language=None)
                        st.subheader("Inputs:")
                        inputs_json = record['inputs_json'] if 'inputs_json' in record.keys() else None
                        if inputs_json:
                            try:
                                inputs = json.loads(inputs_json)
                                if "species_data" in inputs:
                                    display_df = pd.DataFrame(inputs["species_data"])
                                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                                else: st.json(inputs)
                            except json.JSONDecodeError: st.error("Could not display inputs.")
                        else: st.warning("Input data not found.")
                        st.caption("Linked to previous block:")
                        prev_hash_display = record['previous_hash'] if 'previous_hash' in record.keys() else 'N/A'
                        hash_prefix = "#0x" if len(prev_hash_display) == 64 and prev_hash_display != database.GENESIS_HASH else ""
                        st.code(f"{hash_prefix}{prev_hash_display}", language=None)


        # --- TAB 2: Members & Invites (UPDATED) ---
        with tab2:
            st.subheader("Manage Project Access")
            project_details = database.get_project_details(project_id)
            is_owner = project_details and 'owner_id' in project_details.keys() and project_details['owner_id'] == user_id

            if is_owner:
                st.write("**Invite Users or Teams**")
                invite_type = st.radio("Invite Type:", ["User", "Team"], key="proj_invite_type", horizontal=True)
                if invite_type == "User":
                    with st.form("invite_user_form"):
                        username_to_invite = st.text_input("Username to Invite")
                        invite_user_submitted = st.form_submit_button("Send User Invite")
                    if invite_user_submitted:
                        if not username_to_invite: st.warning("Enter username.")
                        elif username_to_invite == username: st.warning("Cannot invite self.")
                        else:
                            invite_status = database.invite_project_member(project_id, user_id, username_to_invite)
                            if invite_status == 'invited': st.success(f"Invited {username_to_invite}."); st.rerun()
                            elif invite_status == 'already_member': st.warning(f"{username_to_invite} is member.")
                            elif invite_status == 'already_invited': st.info(f"{username_to_invite} pending.")
                            elif invite_status == 'not_found': st.error(f"User not found.")
                            elif invite_status == 'not_owner': st.error("Not owner.")
                            else: st.error("Error sending invite.")
                elif invite_type == "Team":
                    with st.form("invite_team_form"):
                        teamname_to_invite = st.text_input("Team Name to Invite")
                        st.caption("Enter exact team name. Team owner must accept.")
                        invite_team_submitted = st.form_submit_button("Send Team Invite")
                    if invite_team_submitted:
                        if not teamname_to_invite: st.warning("Enter team name.")
                        else:
                            invite_status = database.invite_team_to_project(project_id, user_id, teamname_to_invite)
                            if invite_status == 'invited': st.success(f"Invite sent to owner of '{teamname_to_invite}'."); st.rerun()
                            elif invite_status == 'not_found': st.error(f"Team not found.")
                            elif invite_status == 'not_owner': st.error("Not project owner.")
                            elif invite_status == 'already_exists': st.info(f"Team already linked or invited.")
                            else: st.error("Error sending invite.")
            else: st.info("Only project owner can invite.")

            st.markdown("---")
            # --- Display Joined Members ---
            st.subheader("Current Members")
            members = database.get_project_members(project_id) # Gets only joined USERS
            if not members: st.info("No individual members joined.")
            else:
                for member in members:
                    member_id = member['user_id'] if 'user_id' in member.keys() else None; member_name = member['username'] if 'username' in member.keys() else 'N/A'
                    if member_id is None: continue
                    role_display = "(Owner)" if 'role' in member.keys() and member['role'] == 'owner' else ""
                    col1, col2 = st.columns([3, 1])
                    with col1: st.write(f"• **{member_name}** {role_display}")
                    with col2:
                        if is_owner and member_id != user_id:
                            button_key = f"remove_proj_member_{member_id}"
                            if st.button("Remove", key=button_key, type="primary", use_container_width=True):
                                remove_status = database.remove_project_member(project_id, member_id, user_id)
                                if remove_status == 'removed': st.success(f"Removed {member_name}."); st.rerun()
                                else: st.error("Could not remove.")

            st.markdown("---")
            # --- Display Joined Teams ---
            st.subheader("Joined Teams")
            joined_teams = database.get_project_teams(project_id) # Gets only joined TEAMS
            if not joined_teams: st.info("No teams have joined.")
            else:
                for team in joined_teams:
                    team_id = team['team_id'] if 'team_id' in team.keys() else None
                    if team_id is None: continue
                    team_name = team['team_name'] if 'team_name' in team.keys() else 'N/A'
                    # Make team name an expander
                    with st.expander(f"**{team_name}** (Team)"):
                        team_members = database.get_team_members_only(team_id) # Fetch members
                        if not team_members: st.write("No members in this team.")
                        else: member_names = [f"- {m['username']}" for m in team_members if 'username' in m.keys()]; st.markdown("\n".join(member_names))
                        if is_owner:
                            remove_team_key = f"remove_proj_team_{team_id}"
                            if st.button("Remove Team Link", key=remove_team_key, type="primary"):
                                success = database.remove_team_from_project(project_id, team_id, user_id)
                                if success: st.success(f"Removed Team {team_name}."); st.rerun()
                                else: st.error("Failed remove link.")

            st.markdown("---")
            # --- Display Pending User Invites (Owner View) ---
            if is_owner:
                st.subheader("Pending User Invites")
                pending_users = database.get_project_pending_invites(project_id)
                if not pending_users: st.info("No pending user invites.")
                else:
                    for invite in pending_users:
                        invite_user_id = invite['user_id'] if 'user_id' in invite.keys() else None; invite_name = invite['username'] if 'username' in invite.keys() else 'N/A'
                        if invite_user_id is None: continue
                        invited_at_display = format_timestamp(invite['invited_at'] if 'invited_at' in invite.keys() else None)
                        col1, col2 = st.columns([3, 1])
                        with col1: st.write(f"• {invite_name} (Invited: {invited_at_display})")
                        with col2:
                            cancel_key = f"cancel_user_invite_{invite_user_id}"
                            if st.button("Cancel", key=cancel_key, type="primary", use_container_width=True):
                                cancel_status = database.remove_project_member(project_id, invite_user_id, user_id) # Works for pending too
                                if cancel_status == 'removed': st.success(f"Cancelled for {invite_name}."); st.rerun()
                                else: st.error("Failed cancel.")

            # --- Display Pending Team Invites (Owner View) ---
            if is_owner:
                 st.subheader("Pending Team Invites")
                 pending_teams = database.get_project_pending_team_invites(project_id)
                 if not pending_teams: st.info("No pending team invites.")
                 else:
                      for invite in pending_teams:
                          team_id_pending = invite['team_id'] if 'team_id' in invite.keys() else None
                          if team_id_pending is None: continue
                          team_name_display = invite['team_name'] if 'team_name' in invite.keys() else 'N/A'
                          invited_at_display = format_timestamp(invite['invited_at'] if 'invited_at' in invite.keys() else None)
                          col1, col2 = st.columns([3, 1])
                          with col1: st.write(f"• Team: **{team_name_display}** (Invited: {invited_at_display})")
                          with col2:
                               cancel_key = f"cancel_team_invite_{team_id_pending}"
                               if st.button("Cancel", key=cancel_key, type="primary", use_container_width=True):
                                    cancel_status = database.cancel_project_team_invite(project_id, team_id_pending, user_id)
                                    if cancel_status == 'cancelled': st.success(f"Cancelled for {team_name_display}."); st.rerun()
                                    else: st.error("Failed cancel.")

        # --- TAB 3: Add Calculation ---
        with tab3:
            st.subheader("Add New Calculation to Project")
            # (Calculation forms remain the same)
            function_choice = st.selectbox("Select Function:", ["Shannon-Wiener Index", "Pielou’s Evenness", "Simpson’s Diversity Index", "Margalef’s Richness Index", "Plankton Abundance", "Water Quality & TSI", "Correlation & Heatmap"], key="project_calc_choice")
            if function_choice in ["Shannon-Wiener Index", "Pielou’s Evenness", "Simpson’s Diversity Index", "Margalef’s Richness Index"]:
                st.subheader(f"{function_choice}")
                with st.form("project_indices_form"):
                    st.write("Enter species counts:")
                    initial_data = {"Species Name": ["D1", "C1", "R1"], "Count": [50, 15, 5]}
                    df_input = pd.DataFrame(initial_data)
                    edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True, column_config={"Species Name": st.column_config.TextColumn(required=True), "Count": st.column_config.NumberColumn(min_value=0, required=True)})
                    submitted = st.form_submit_button("Calculate & Add")
                    if submitted:
                        try:
                            # Validation, Calculation, Interpretation, Save (Code unchanged)
                            if edited_df.empty: st.warning("Enter species."); st.stop()
                            if "Count" not in edited_df.columns or "Species Name" not in edited_df.columns: st.error("Need 'Species Name' and 'Count'."); st.stop()
                            if edited_df["Species Name"].isnull().any() or (edited_df["Species Name"] == "").any(): st.warning("Provide names."); st.stop()
                            try: counts_series = pd.to_numeric(edited_df["Count"].fillna(0), errors='coerce')
                            except Exception as e: st.error(f"Count error: {e}"); st.stop()
                            if counts_series.isnull().any(): st.error("Counts must be numbers."); st.stop()
                            if (counts_series < 0).any(): st.error("Counts >= 0."); st.stop()
                            calc_df = edited_df[counts_series > 0].copy(); counts = calc_df["Count"].astype(int).tolist()
                            save_df = edited_df.copy(); save_df['Count'] = save_df['Count'].astype(str); inputs_list_of_dicts = save_df.to_dict('records')
                            S = len(counts); N = sum(counts); result = 0.0
                            if S == 0 and function_choice != "Plankton Abundance": st.warning("Need count > 0."); st.stop()
                            if function_choice == "Shannon-Wiener Index": result = 0.0 if N == 0 else functions.shannon_index(counts)
                            elif function_choice == "Pielou’s Evenness":
                                if N == 0 or S < 2: st.warning("Pielou needs >= 2 species."); result = 0.0
                                else: result = functions.pielou_evenness(counts)
                            elif function_choice == "Simpson’s Diversity Index":
                                if N < 2: st.warning("Simpson needs N >= 2."); result = 0.0
                                else: result = functions.simpson_diversity(counts)
                            elif function_choice == "Margalef’s Richness Index":
                                if N <= 1: st.warning("Margalef needs N > 1."); result = 0.0
                                else: result = functions.richness_index(counts)
                            if result is None: st.error("Calculation failed."); result = 0.0
                            st.success(f"**{function_choice}: {result:.4f}**")
                            interpretation = "";
                            if function_choice == "Simpson’s Diversity Index": interpretation = get_simpson_interpretation(result)
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
                            inputs_dict = {"species_data": inputs_list_of_dicts}
                            cert_id = database.add_calculation(user_id, function_choice, inputs_dict, f"{result:.4f}", project_id=project_id, project_name=project_name)
                            if cert_id: st.info(f"Saved."); st.caption("Certificate ID:"); st.code(f"#0x{cert_id}", language=None)
                            else: st.error("Failed to save.")
                            if S > 0:
                                st.subheader("Visualization")
                                chart_df = calc_df.set_index("Species Name")
                                st.bar_chart(chart_df["Count"], color="#4299E1")
                        except ValueError as ve: st.error(f"Input Error: {ve}")
                        except Exception as e: st.error(f"Error: {e}")

            elif function_choice == "Plankton Abundance":
                st.subheader("Plankton Abundance")
                with st.form("project_plankton_form"):
                     # Plankton form fields (unchanged)
                    col1, col2 = st.columns(2)
                    with col1:
                        n = st.number_input("Observed (n)", min_value=0, value=10)
                        V = st.number_input("Vol bottle (ml)", min_value=0.1, value=100.0, format="%.1f")
                        V_src = st.number_input("Vol SRC (ml)", min_value=0.1, value=5.0, format="%.1f")
                    with col2:
                        A_src = st.number_input("SRC area (mm²)", min_value=0.1, value=50.0, format="%.2f")
                        A_a = st.number_input("Microscope area (mm²)", min_value=0.01, value=1.0, format="%.2f")
                        V_d = st.number_input("Vol filtered (m³)", min_value=0.001, value=1.0, format="%.3f")
                    submitted = st.form_submit_button("Calculate & Add")
                    if submitted:
                        try:
                             # Calculation and Save (unchanged)
                            if A_a <= 0 or V_d <= 0: st.error("Aa and Vd must be > 0.")
                            else:
                                N = float(n) * float(V) * (float(V_src) * float(A_src)) / (float(A_a) * float(V_d))
                                st.success(f"**Plankton Abundance: {N:.4f}**")
                                inputs_dict = {"n": n, "V": V, "V_src": V_src, "A_src": A_src, "A_a": A_a, "V_d": V_d}
                                cert_id = database.add_calculation(user_id, function_choice, inputs_dict, f"{N:.4f}", project_id=project_id, project_name=project_name)
                                if cert_id: st.info(f"Saved."); st.caption("Certificate ID:"); st.code(f"#0x{cert_id}", language=None)
                                else: st.error("Failed to save.")
                        except ZeroDivisionError: st.error("Division by zero.")
                        except Exception as e: st.error(f"Error: {e}")

            elif function_choice == "Water Quality & TSI":
                st.subheader("Water Quality & TSI")
                with st.form("project_wq_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        chl_a = st.number_input("Chlorophyll-a (µg/L)", min_value=0.0, value=10.0, format="%.2f")
                        phosphorus = st.number_input("Total Phosphorus (µg/L)", min_value=0.0, value=50.0, format="%.2f")
                    with col2:
                        secchi = st.number_input("Secchi Depth (m)", min_value=0.0, value=2.0, format="%.2f")
                        nitrogen = st.number_input("Total Nitrogen (µg/L)", min_value=0.0, value=1000.0, format="%.2f")
                    submitted = st.form_submit_button("Calculate & Add")
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
                                user_id, 
                                function_choice, 
                                save_inputs,
                                f"{val_chl:.4f}" if val_chl is not None else "0.0", 
                                project_id=project_id, 
                                project_name=project_name
                            )
                            if cert_id: st.info(f"Saved."); st.caption("Certificate ID:"); st.code(f"#0x{cert_id}", language=None)
                            else: st.error("Failed to save.")
                        except Exception as e:
                            st.error(f"Error: {e}")

            elif function_choice == "Correlation & Heatmap":
                st.subheader("Correlation & Heatmap")
                st.info("Explore relationships between multiple metrics on an uploaded dataset.")
                st.download_button(label=" Download Empty Template", data=generate_template(["Site_Name", "Temperature", "pH", "Dissolved_Oxygen", "Conductivity", "Turbidity"]), file_name="correlation_project_template.xlsx", mime="application/vnd.ms-excel")
                uploaded_file = st.file_uploader("Upload Dataset (Excel format)", key="proj_corr_upload")
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
                            file_name="correlation_project_report.txt",
                            mime="text/plain",
                            key="proj_corr_dl"
                        )
                    except Exception as e:
                        st.error(f"Error generating correlation report: {e}")

        # --- TAB 4: Project Analytics ---
        with tab4:
            st.subheader("Time-Series Trends")
            project_calcs = database.get_project_calculations(project_id)
            if not project_calcs:
                st.info("No calculations available to map trends.")
            else:
                df_calcs = pd.DataFrame([dict(row) for row in project_calcs])
                if not df_calcs.empty and 'calculation_type' in df_calcs.columns and 'result' in df_calcs.columns:
                    df_calcs['result_num'] = pd.to_numeric(df_calcs['result'], errors='coerce')
                    df_calcs = df_calcs.dropna(subset=['result_num'])
                    
                    if df_calcs.empty:
                        st.warning("No purely numeric results available to plot.")
                    else:
                        types = sorted(df_calcs['calculation_type'].unique())
                        selected_type = st.selectbox("Select Metric to View:", types)
                        
                        trend_data = df_calcs[df_calcs['calculation_type'] == selected_type].copy()
                        if not trend_data.empty:
                            trend_data['timestamp'] = pd.to_datetime(trend_data['timestamp'])
                            trend_data = trend_data.sort_values('timestamp')
                            trend_data.set_index('timestamp', inplace=True)
                            st.line_chart(trend_data['result_num'])
                        else:
                            st.info("No data for this metric.")

    # --- VIEW 2: MAIN PROJECT LIST ---
    # This part only runs if current_project_id is None
    else:
        st.header("Your Projects")

        # --- Section for Pending Invites (moved from Profile) ---
        st.subheader("Pending Project Invitations")
        user_invites = database.get_user_project_invites(user_id)
        if not user_invites:
            st.info("You have no pending project invitations.")
        else:
            for invite in user_invites:
                proj_invite_id = invite['id'] if 'id' in invite.keys() else None
                if proj_invite_id is None: continue
                proj_invite_name = invite['name'] if 'name' in invite.keys() else 'N/A'
                proj_invite_owner = invite['owner_username'] if 'owner_username' in invite.keys() else 'N/A'
                with st.container(border=True):
                    st.write(f"Invited to join **{proj_invite_name}** (Owner: {proj_invite_owner})")
                    col1, col2, col3 = st.columns([1,1,2])
                    with col1:
                        if st.button("Accept", key=f"accept_proj_{proj_invite_id}"):
                            success = database.respond_to_project_invite_user(user_id, proj_invite_id, accept=True)
                            if success: st.success(f"Joined {proj_invite_name}!"); st.rerun()
                            else: st.error("Failed accept.")
                    with col2:
                         if st.button("Reject", key=f"reject_proj_{proj_invite_id}", type="primary"):
                            success = database.respond_to_project_invite_user(user_id, proj_invite_id, accept=False)
                            if success: st.success(f"Rejected invite."); st.rerun()
                            else: st.error("Failed reject.")

        st.markdown("---")


        with st.form("create_project_form"):
            st.subheader("Create a New Project")
            new_project_name = st.text_input("Project Name", key="new_proj_name")
            submitted = st.form_submit_button("Create Project")

            if submitted:
                if not new_project_name:
                    st.warning("Please enter a project name.")
                else:
                    project_id = database.create_project(new_project_name, user_id, username)
                    if project_id:
                        st.success(f"Project '{new_project_name}' created!")
                        # Use callback to set state
                        set_current_project(project_id, new_project_name)
                        st.rerun() # Rerun immediately
                    else:
                        st.error("Could not create project.")

        st.markdown("---")

        st.subheader("Your Projects")
        projects = database.get_user_projects(user_id) # Gets joined projects AND projects from joined teams

        if not projects:
            st.info("You are not a member of any projects yet.")
        else:
            for project in projects:
                # project is a tuple: (id, name, role_order_num, role_text)
                proj_id = project[0]
                proj_name = project[1]
                proj_role = project[3] # Use the role_text

                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(proj_name)
                        st.caption(f"Your role: {proj_role}") # Display the calculated role
                    with col2:
                        # --- USE ON_CLICK CALLBACK ---
                        button_key = f"open_proj_{proj_id}"
                        st.button(
                            "Open Project",
                            key=button_key,
                            use_container_width=True,
                            on_click=set_current_project, # Assign callback
                            args=(proj_id, proj_name) # Pass args
                        )

