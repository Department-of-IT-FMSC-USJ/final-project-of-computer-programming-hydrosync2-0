import streamlit as st
import database
# UPDATED: Import timezone directly
from datetime import datetime, timezone

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

# --- RE-ADDED Callback function for opening a team ---
def set_current_team(team_id, team_name):
    """Callback to set the current team view in session state."""
    st.session_state.current_team = team_id
    st.session_state.current_team_name = team_name
    # No rerun/stop needed, Streamlit handles it

# --- MAIN PAGE FUNCTION ---
def show_page(user_id, username):
    """Renders the Teams page using session state for navigation."""

    # --- VIEW 1: INDIVIDUAL TEAM DASHBOARD ---
    # Check FIRST if we are viewing a specific team using session state
    current_team_id = st.session_state.get('current_team')

    if current_team_id is not None:
        team_id = current_team_id
        # Use name from session state
        team_name = st.session_state.get('current_team_name', 'Unknown Team')

        if st.button("<- Back to All Teams"):
            st.session_state.current_team = None
            st.session_state.current_team_name = None
            st.rerun()
            st.stop() # Stop needed here

        st.header(f"Team: {team_name}")
        team_details = database.get_team_details(team_id) # Fetch owner info

        if team_details:
             owner_username_display = team_details['owner_username'] if 'owner_username' in team_details.keys() else 'N/A'
             st.caption(f"Owner: {owner_username_display}")
        st.markdown("---")

        is_owner = team_details and 'owner_id' in team_details.keys() and team_details['owner_id'] == user_id

        # --- Team Dashboard Tabs ---
        tab1, tab2 = st.tabs(["Members & Invites", "Settings"])

        # (Rest of the individual team view code remains the same)
        # --- TAB 1: Members & Invites ---
        with tab1:
            st.subheader("Manage Members")
            if is_owner:
                # Invite form logic (unchanged)
                with st.form("invite_team_member_form"):
                    st.write("Invite by username:")
                    col1, col2 = st.columns([3,1])
                    with col1: username_to_invite = st.text_input("Username", label_visibility="collapsed", key="team_invite_user")
                    with col2: invite_submitted = st.form_submit_button("Invite User")
                if invite_submitted:
                    if not username_to_invite: st.warning("Enter username.")
                    elif username_to_invite == username: st.warning("Cannot invite self.")
                    else:
                        invite_status = database.invite_team_member(team_id, user_id, username_to_invite)
                        if invite_status == 'invited': st.success(f"Invited {username_to_invite}."); st.rerun()
                        elif invite_status == 'already_member': st.warning(f"{username_to_invite} is member.")
                        elif invite_status == 'already_invited': st.info(f"{username_to_invite} pending.")
                        elif invite_status == 'not_found': st.error(f"User not found.")
                        elif invite_status == 'not_owner': st.error("Not team owner.") # Added
                        elif invite_status == 'self_invite': st.warning("Cannot invite self.")
                        else: st.error("Error sending invite.")
                st.markdown("---")

            # Display Members and Pending Invites (unchanged logic)
            members, pending = database.get_team_members_and_pending(team_id)
            st.subheader("Current Members")
            if not members: st.info("No members.")
            else:
                for member in members:
                    member_name = member['username'] if 'username' in member.keys() else 'N/A'
                    member_id = member['user_id'] if 'user_id' in member.keys() else None
                    if member_id is None: continue
                    role_display = "(Owner)" if 'role' in member.keys() and member['role'] == 'owner' else ""
                    joined_at = format_timestamp(member['joined_at'] if 'joined_at' in member.keys() else None)
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1: st.write(f"**{member_name}** {role_display}")
                    with col2: st.caption(f"Joined: {joined_at}")
                    with col3:
                        if is_owner and member_id != user_id:
                            if st.button("Remove", key=f"remove_member_{member_id}", type="primary"):
                                remove_status = database.remove_team_member(team_id, member_id, user_id)
                                if remove_status == 'removed': st.success(f"Removed {member_name}."); st.rerun()
                                else: st.error("Failed remove.")
            st.markdown("---")
            st.subheader("Pending Invitations")
            if not pending: st.info("No pending invites.")
            else:
                for invite in pending:
                    invite_name = invite['username'] if 'username' in invite.keys() else 'N/A'
                    invite_user_id = invite['user_id'] if 'user_id' in invite.keys() else None
                    if invite_user_id is None: continue
                    invited_at = format_timestamp(invite['invited_at'] if 'invited_at' in invite.keys() else None)
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1: st.write(f"**{invite_name}**")
                    with col2: st.caption(f"Invited: {invited_at}")
                    with col3:
                        if is_owner:
                            if st.button("Cancel Invite", key=f"cancel_invite_{invite_user_id}", type="primary"):
                                remove_status = database.remove_team_member(team_id, invite_user_id, user_id)
                                if remove_status == 'removed': st.success(f"Cancelled for {invite_name}."); st.rerun()
                                else: st.error("Failed cancel.")

        # --- TAB 2: Settings (Owner Only) ---
        with tab2:
            st.subheader("Team Settings")
            if is_owner:
                # Delete Team logic (unchanged)
                st.write("Manage team settings.")
                st.markdown("---"); st.write("Delete Team")
                st.warning("Warning: Deleting team is permanent.")
                if st.button("Delete This Team", type="primary"):
                    delete_status = database.delete_team(team_id, user_id)
                    if delete_status == 'deleted':
                        st.success(f"Team '{team_name}' deleted.")
                        st.session_state.current_team = None; st.session_state.current_team_name = None
                        st.experimental_rerun()
                    elif delete_status == 'not_owner': st.error("Only owner can delete.")
                    else: st.error("Failed to delete.")
            else: st.info("Only owner can access settings.")

    # --- VIEW 2: MAIN TEAM LIST & INVITES ---
    # This part runs only if current_team_id is None
    else:
        st.header("Your Teams")

        # --- Section for User's Pending Team Invites ---
        st.subheader("Pending Team Invitations")
        user_team_invites = database.get_user_team_invites(user_id)
        if not user_team_invites: st.info("No pending team invites.")
        else:
            # Display invites with Accept/Reject (unchanged)
            for invite in user_team_invites:
                invite_id = invite['id'] if 'id' in invite.keys() else None
                if invite_id is None: continue
                invite_name = invite['name'] if 'name' in invite.keys() else 'N/A'
                invite_owner = invite['owner_username'] if 'owner_username' in invite.keys() else 'N/A'
                with st.container(border=True):
                    st.write(f"Invited to **{invite_name}** (Owner: {invite_owner})")
                    col1, col2, col3 = st.columns([1,1,2])
                    with col1:
                        if st.button("Accept", key=f"accept_team_{invite_id}"):
                            success = database.respond_to_team_invite(user_id, invite_id, accept=True)
                            if success: st.success(f"Joined {invite_name}!"); st.rerun()
                            else: st.error("Failed accept.")
                    with col2:
                         if st.button("Reject", key=f"reject_team_{invite_id}", type="primary"):
                            success = database.respond_to_team_invite(user_id, invite_id, accept=False)
                            if success: st.success(f"Rejected invite."); st.rerun()
                            else: st.error("Failed reject.")

        st.markdown("---")
        # --- Section for Team Owner's Pending Project Invites ---
        st.subheader("Project Invitations for Your Teams")
        project_invites_for_owner = database.get_project_team_invites_for_owner(user_id)
        if not project_invites_for_owner: st.info("No pending project invites for your teams.")
        else:
             # Display project invites with Accept/Reject (unchanged)
            for invite in project_invites_for_owner:
                proj_id_for_invite = invite['project_id'] if 'project_id' in invite.keys() else None
                team_id_for_invite = invite['team_id'] if 'team_id' in invite.keys() else None
                if proj_id_for_invite is None or team_id_for_invite is None: continue
                proj_name_display = invite['project_name'] if 'project_name' in invite.keys() else 'N/A'
                team_name_display = invite['team_name'] if 'team_name' in invite.keys() else 'N/A'
                with st.container(border=True):
                    st.write(f"Team **{team_name_display}** invited to project **{proj_name_display}**.")
                    col1, col2, col3 = st.columns([1,1,2])
                    with col1:
                        if st.button("Accept for Team", key=f"accept_proj_team_{proj_id_for_invite}_{team_id_for_invite}"):
                            success = database.respond_to_project_invite_team(user_id, proj_id_for_invite, team_id_for_invite, accept=True)
                            if success: st.success(f"Accepted invite."); st.rerun()
                            else: st.error("Failed accept.")
                    with col2:
                        if st.button("Reject for Team", key=f"reject_proj_team_{proj_id_for_invite}_{team_id_for_invite}", type="primary"):
                            success = database.respond_to_project_invite_team(user_id, proj_id_for_invite, team_id_for_invite, accept=False)
                            if success: st.success(f"Rejected invite."); st.rerun()
                            else: st.error("Failed reject.")

        st.markdown("---")
        # --- Section to Create a Team ---
        with st.form("create_team_form"):
            st.subheader("Create New Team")
            new_team_name = st.text_input("Team Name", key="new_team_name")
            submitted = st.form_submit_button("Create Team")
            if submitted:
                # Create team logic (unchanged)
                if not new_team_name: st.warning("Enter name.")
                else:
                    team_id = database.create_team(new_team_name, user_id, username)
                    if team_id is not None:
                        st.success(f"Team '{new_team_name}' created!")
                        # Use callback approach
                        set_current_team(team_id, new_team_name)
                        st.rerun()
                    else: st.error("Could not create team.")

        st.markdown("---")
        # --- Section to List User's Teams ---
        st.subheader("Your Teams")
        teams = database.get_user_teams(user_id) # Gets only joined teams
        if not teams: st.info("Not member of any teams.")
        else:
            for team in teams:
                # Display team row
                team_id = team['id'] if 'id' in team.keys() else None
                if team_id is None: continue
                team_name = team['name'] if 'name' in team.keys() else 'N/A'
                team_role = team['role'] if 'role' in team.keys() else 'N/A'
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(team_name)
                        role_display = "Owner" if team_role == 'owner' else "Member"
                        st.caption(f"Role: {role_display}")
                    with col2:
                        # --- USE ON_CLICK CALLBACK ---
                        button_key = f"open_team_{team_id}"
                        st.button(
                            "Open Team",
                            key=button_key,
                            use_container_width=True,
                            on_click=set_current_team, # Assign callback
                            args=(team_id, team_name) # Pass args
                        )

