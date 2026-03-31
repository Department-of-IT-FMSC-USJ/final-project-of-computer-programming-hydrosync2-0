import sqlite3
import hashlib
from datetime import datetime, timezone, timedelta
import json
from werkzeug.security import generate_password_hash, check_password_hash

# --- DATABASE CONSTANTS ---
DB_NAME = 'hydrosync.db'
GENESIS_HASH = '0' * 64

# --- DATABASE SETUP ---
def connect_db():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

def create_tables():
    """Creates all necessary tables if they don't exist."""
    conn = connect_db()
    c = conn.cursor()
    # User Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # Calculations Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            calculation_type TEXT NOT NULL,
            inputs_json TEXT NOT NULL,
            result TEXT NOT NULL,
            certificate_id TEXT UNIQUE NOT NULL,
            previous_hash TEXT NOT NULL,
            project_id INTEGER,
            project_name TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
        )
    ''')
    # Projects Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            owner_id INTEGER NOT NULL,
            owner_username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')
    # Project Members Table (Individual Users Only)
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_members (
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            role TEXT NOT NULL, -- 'owner', 'member'
            status TEXT NOT NULL, -- 'pending', 'joined'
            invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            joined_at TIMESTAMP,
            PRIMARY KEY (project_id, user_id),
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    # Teams Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            owner_id INTEGER NOT NULL,
            owner_username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')
    # Team Members Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS team_members (
            team_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            role TEXT NOT NULL, -- 'owner', 'member'
            status TEXT NOT NULL, -- 'invited', 'joined'
            invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            joined_at TIMESTAMP,
            PRIMARY KEY (team_id, user_id),
            FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    # Project Teams Table (Links Projects and Teams)
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_teams (
            project_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            team_name TEXT NOT NULL,
            invited_by_user_id INTEGER NOT NULL,
            team_owner_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'joined', 'rejected'
            invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_at TIMESTAMP,
            PRIMARY KEY (project_id, team_id),
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
            FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE CASCADE,
            FOREIGN KEY (invited_by_user_id) REFERENCES users (id),
            FOREIGN KEY (team_owner_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# --- PASSWORD HASHING ---
def hash_password(password): 
    return generate_password_hash(password)

def check_password(hashed_password, user_password): 
    return check_password_hash(hashed_password, user_password)

# --- USER FUNCTIONS ---
def add_user(username, email, password):
    conn = connect_db(); c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hashed_pw))
        conn.commit(); return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()
def login_user(username, password):
    conn = connect_db(); c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    data = c.fetchone(); conn.close()
    if data:
        user_id, stored_hash = data
        if check_password(stored_hash, password): return user_id
    return None
def get_user_by_username(username):
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE username = ?", (username,))
    user = c.fetchone(); conn.close(); return user

# --- CALCULATION LEDGER FUNCTIONS ---
# (Unchanged)
def get_last_hash():
    conn = connect_db(); c = conn.cursor()
    c.execute("SELECT certificate_id FROM calculations ORDER BY id DESC LIMIT 1")
    data = c.fetchone(); conn.close()
    return data[0] if data else GENESIS_HASH
def create_certificate(timestamp_str, user_id, calc_type, inputs_json, result, previous_hash, project_id=None):
    project_part = str(project_id) if project_id is not None else ""
    # Ensure inputs_json is deterministic by reloading and dumping with sorted keys if it is valid json
    try:
        parsed_json = json.loads(inputs_json)
        deterministic_json = json.dumps(parsed_json, sort_keys=True)
    except Exception:
        deterministic_json = inputs_json
    data_string = f"{timestamp_str}{user_id}{calc_type}{deterministic_json}{result}{previous_hash}{project_part}"
    return hashlib.sha256(data_string.encode()).hexdigest()
def add_calculation(user_id, calc_type, inputs_dict, result, project_id=None, project_name=None):
    conn = connect_db(); c = conn.cursor()
    timestamp = datetime.now(timezone.utc); timestamp_str = timestamp.isoformat()
    # Sort keys for deterministic hashing down the line
    inputs_json = json.dumps(inputs_dict, sort_keys=True); result_str = str(result); previous_hash = get_last_hash()
    certificate_id = create_certificate(timestamp_str, user_id, calc_type, inputs_json, result_str, previous_hash, project_id)
    try:
        c.execute(
            "INSERT INTO calculations (user_id, timestamp, calculation_type, inputs_json, result, certificate_id, previous_hash, project_id, project_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, timestamp, calc_type, inputs_json, result_str, certificate_id, previous_hash, project_id, project_name)
        ); conn.commit(); return certificate_id
    except Exception as e: print(f"Error adding calc: {e}"); conn.rollback(); return None
    finally: conn.close()
def get_calc_by_certificate(certificate_id):
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM calculations WHERE certificate_id = ?", (certificate_id,))
    data = c.fetchone(); conn.close(); return data
def get_calcs_by_user(user_id):
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM calculations WHERE user_id = ? AND проект_id IS NULL ORDER BY timestamp DESC".replace("проект", "project"), (user_id,))
    data = c.fetchall(); conn.close(); return data
def get_all_calculations():
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM calculations ORDER BY id ASC")
    data = c.fetchall(); conn.close(); return data

# --- PROJECT FUNCTIONS ---
def create_project(project_name, owner_id, owner_username):
    conn = connect_db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO projects (name, owner_id, owner_username, created_at) VALUES (?, ?, ?, ?)",
                  (project_name, owner_id, owner_username, datetime.now(timezone.utc)))
        project_id = c.lastrowid
        c.execute("""INSERT INTO project_members (project_id, user_id, username, role, status, invited_at, joined_at) VALUES (?, ?, ?, 'owner', 'joined', ?, ?)""",
                  (project_id, owner_id, owner_username, datetime.now(timezone.utc), datetime.now(timezone.utc)))
        conn.commit(); return project_id
    except sqlite3.IntegrityError: print(f"Project name '{project_name}' exists."); conn.rollback(); return None
    except Exception as e: print(f"Error creating project: {e}"); conn.rollback(); return None
    finally: conn.close()

# --- *** UPDATED get_user_projects (FIXES DUPLICATE KEY ERROR) *** ---
def get_user_projects(user_id):
    """Fetches unique projects user is in (directly or via team), returns (id, name, role) tuple."""
    conn = connect_db()
    c = conn.cursor()
    # Use parameters for user_id in all parts of the query
    c.execute("""
        SELECT id, name, MIN(role_order) as role_order_num,
               CASE MIN(role_order)
                   WHEN 1 THEN 'Owner'
                   WHEN 2 THEN 'Member'
                   ELSE 'Team Member'
               END as role
        FROM (
            -- Projects user is directly a member of, with role priority
            SELECT p.id, p.name,
                   CASE pm.role
                       WHEN 'owner' THEN 1
                       ELSE 2
                   END as role_order
            FROM projects p
            JOIN project_members pm ON p.id = pm.project_id
            WHERE pm.user_id = ? AND pm.status = 'joined'
            UNION ALL
            -- Projects user is a member of via a team
            SELECT p.id, p.name, 3 as role_order
            FROM projects p
            JOIN project_teams pt ON p.id = pt.project_id
            JOIN team_members tm ON pt.team_id = tm.team_id
            WHERE tm.user_id = ? AND pt.status = 'joined' AND tm.status = 'joined'
        ) as combined_projects
        GROUP BY id, name -- Ensures each project appears only once
        ORDER BY name
    """, (user_id, user_id)) # Pass user_id for both parts of the UNION
    projects = c.fetchall()
    conn.close()
    return projects # Returns list of tuples: (id, name, role_order_num, role_text)

def invite_project_member(project_id, inviter_id, username_to_invite):
    """Invites a user to a project."""
    user_to_invite = get_user_by_username(username_to_invite)
    if not user_to_invite: return 'not_found'
    user_id_to_invite = user_to_invite['id']
    if user_id_to_invite == inviter_id: return 'self_invite'
    conn = connect_db(); c = conn.cursor()
    try:
        c.execute("SELECT status FROM project_members WHERE project_id = ? AND user_id = ?", (project_id, user_id_to_invite))
        existing = c.fetchone();
        if existing: return 'already_member' if existing[0] == 'joined' else 'already_invited'
        c.execute("SELECT owner_id FROM projects WHERE id = ?", (project_id,))
        owner_check = c.fetchone();
        if not owner_check or owner_check[0] != inviter_id: return 'not_owner' # Only owner can invite
        c.execute("INSERT INTO project_members (project_id, user_id, username, role, status, invited_at) VALUES (?, ?, ?, 'member', 'pending', ?)",
                  (project_id, user_id_to_invite, username_to_invite, datetime.now(timezone.utc)))
        conn.commit(); return 'invited'
    except Exception as e: print(f"Error inviting proj member: {e}"); conn.rollback(); return 'error'
    finally: conn.close()
def get_user_project_invites(user_id):
    """Fetches pending project invitations for a user."""
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT p.id, p.name, p.owner_username FROM projects p JOIN project_members pm ON p.id = pm.project_id WHERE pm.user_id = ? AND pm.status = 'pending' ORDER BY pm.invited_at DESC", (user_id,))
    invites = c.fetchall(); conn.close(); return invites
def respond_to_project_invite_user(user_id, project_id, accept=True):
    """Updates a user's status for a project invite."""
    conn = connect_db(); c = conn.cursor()
    try:
        if accept:
            c.execute("SELECT 1 FROM project_members WHERE project_id = ? AND user_id = ? AND status = 'pending'", (project_id, user_id))
            if c.fetchone(): c.execute("UPDATE project_members SET status = 'joined', joined_at = ? WHERE project_id = ? AND user_id = ? AND status = 'pending'", (datetime.now(timezone.utc), project_id, user_id))
            else: return False
        else: c.execute("DELETE FROM project_members WHERE project_id = ? AND user_id = ? AND status = 'pending'", (project_id, user_id))
        conn.commit(); return c.rowcount > 0
    except Exception as e: print(f"Error responding to proj invite: {e}"); conn.rollback(); return False
    finally: conn.close()
def get_project_members(project_id):
    """Fetches JOINED user members of a specific project."""
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT user_id, username, role FROM project_members WHERE project_id = ? AND status = 'joined'", (project_id,))
    members = c.fetchall(); conn.close(); return members
def get_project_pending_invites(project_id):
    """Fetches PENDING user invites for a specific project."""
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT user_id, username, invited_at FROM project_members WHERE project_id = ? AND status = 'pending' ORDER BY invited_at DESC", (project_id,))
    pending = c.fetchall(); conn.close(); return pending
def remove_project_member(project_id, user_id_to_remove, current_user_id):
    """Removes a joined member or cancels a pending invite. Only owner."""
    conn = connect_db(); c = conn.cursor()
    try:
        c.execute("SELECT owner_id FROM projects WHERE id = ?", (project_id,))
        owner_check = c.fetchone();
        if not owner_check or owner_check[0] != current_user_id: return 'not_owner'
        if user_id_to_remove == current_user_id: return 'cannot_remove_self'
        c.execute("DELETE FROM project_members WHERE project_id = ? AND user_id = ?", (project_id, user_id_to_remove))
        conn.commit(); return 'removed' if c.rowcount > 0 else 'not_found'
    except Exception as e: print(f"Error removing/cancelling proj member: {e}"); conn.rollback(); return 'error'
    finally: conn.close()
def get_project_calculations(project_id):
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM calculations WHERE project_id = ? ORDER BY timestamp DESC", (project_id,))
    data = c.fetchall(); conn.close(); return data
def get_project_details(project_id):
     conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
     c.execute("SELECT id, name, owner_id, owner_username FROM projects WHERE id = ?", (project_id,))
     project = c.fetchone(); conn.close(); return project

# --- TEAM FUNCTIONS ---
# (Unchanged structurally)
def create_team(team_name, owner_id, owner_username):
    conn = connect_db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO teams (name, owner_id, owner_username, created_at) VALUES (?, ?, ?, ?)",
                  (team_name, owner_id, owner_username, datetime.now(timezone.utc)))
        team_id = c.lastrowid
        c.execute("""INSERT INTO team_members (team_id, user_id, username, role, status, joined_at, invited_at) VALUES (?, ?, ?, 'owner', 'joined', ?, ?)""",
                  (team_id, owner_id, owner_username, datetime.now(timezone.utc), datetime.now(timezone.utc)))
        conn.commit(); return team_id
    except sqlite3.IntegrityError: print(f"Team name '{team_name}' exists."); conn.rollback(); return None
    except Exception as e: print(f"Error creating team: {e}"); conn.rollback(); return None
    finally: conn.close()
def get_user_teams(user_id):
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT t.id, t.name, tm.role FROM teams t JOIN team_members tm ON t.id = tm.team_id WHERE tm.user_id = ? AND tm.status = 'joined' ORDER BY t.name", (user_id,))
    teams = c.fetchall(); conn.close(); return teams
def invite_team_member(team_id, inviter_id, username_to_invite):
    user_to_invite = get_user_by_username(username_to_invite)
    if not user_to_invite: return 'not_found'
    user_id_to_invite = user_to_invite['id']
    if user_id_to_invite == inviter_id: return 'self_invite'
    conn = connect_db(); c = conn.cursor()
    try:
        c.execute("SELECT status FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, user_id_to_invite))
        existing = c.fetchone();
        if existing: return 'already_member' if existing[0] == 'joined' else 'already_invited'
        c.execute("SELECT owner_id FROM teams WHERE id = ?", (team_id,)) # Check if inviter is owner
        team_owner_check = c.fetchone()
        if not team_owner_check or team_owner_check[0] != inviter_id: return 'not_owner'
        c.execute("""INSERT INTO team_members (team_id, user_id, username, role, status, invited_at) VALUES (?, ?, ?, 'member', 'invited', ?)""",
                  (team_id, user_id_to_invite, username_to_invite, datetime.now(timezone.utc)))
        conn.commit(); return 'invited'
    except Exception as e: print(f"Error inviting team member: {e}"); conn.rollback(); return 'error'
    finally: conn.close()
def get_team_members_and_pending(team_id):
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM team_members WHERE team_id = ? ORDER BY status DESC, joined_at ASC, invited_at ASC", (team_id,))
    all_rows = c.fetchall(); conn.close()
    members = [r for r in all_rows if r['status'] == 'joined']
    pending = [r for r in all_rows if r['status'] == 'invited']
    return members, pending
def get_team_members_only(team_id):
    """Fetches only JOINED members (user_id, username, role) of a specific team."""
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT user_id, username, role FROM team_members WHERE team_id = ? AND status = 'joined'", (team_id,))
    members = c.fetchall(); conn.close(); return members
def get_user_team_invites(user_id):
    """Fetches all pending invites for a user to join a team."""
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT t.id, t.name, t.owner_username FROM teams t JOIN team_members tm ON t.id = tm.team_id WHERE tm.user_id = ? AND tm.status = 'invited' ORDER BY tm.invited_at DESC", (user_id,))
    invites = c.fetchall(); conn.close(); return invites
def respond_to_team_invite(user_id, team_id, accept=True):
    conn = connect_db(); c = conn.cursor()
    try:
        if accept:
            c.execute("SELECT 1 FROM team_members WHERE team_id = ? AND user_id = ? AND status = 'invited'", (team_id, user_id))
            if c.fetchone(): c.execute("UPDATE team_members SET status = 'joined', joined_at = ? WHERE team_id = ? AND user_id = ? AND status = 'invited'", (datetime.now(timezone.utc), team_id, user_id))
            else: return False
        else: c.execute("DELETE FROM team_members WHERE team_id = ? AND user_id = ? AND status = 'invited'", (team_id, user_id))
        conn.commit(); return c.rowcount > 0
    except Exception as e: print(f"Error responding to team invite: {e}"); conn.rollback(); return False
    finally: conn.close()
def remove_team_member(team_id, user_id_to_remove, current_user_id):
    conn = connect_db(); c = conn.cursor()
    try:
        c.execute("SELECT role FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, current_user_id))
        role_result = c.fetchone();
        if not role_result or role_result[0] != 'owner': return 'not_owner'
        c.execute("SELECT role FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, user_id_to_remove))
        target_role_result = c.fetchone();
        if target_role_result and target_role_result[0] == 'owner': return 'cannot_remove_owner'
        c.execute("DELETE FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, user_id_to_remove))
        conn.commit(); return 'removed' if c.rowcount > 0 else 'not_found'
    except Exception as e: print(f"Error removing team member: {e}"); conn.rollback(); return 'error'
    finally: conn.close()
def delete_team(team_id, current_user_id):
    conn = connect_db(); c = conn.cursor()
    try:
        c.execute("SELECT owner_id FROM teams WHERE id = ?", (team_id,))
        owner_result = c.fetchone();
        if not owner_result or owner_result[0] != current_user_id: return 'not_owner'
        c.execute("DELETE FROM teams WHERE id = ?", (team_id,)) # Cascade delete handles members
        conn.commit(); return 'deleted' if c.rowcount > 0 else 'not_found'
    except Exception as e: print(f"Error deleting team: {e}"); conn.rollback(); return 'error'
    finally: conn.close()
def get_team_details(team_id):
     conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
     c.execute("SELECT id, name, owner_id, owner_username FROM teams WHERE id = ?", (team_id,))
     team = c.fetchone(); conn.close(); return team

# --- Project Team Invite Functions ---
def invite_team_to_project(project_id, inviter_user_id, team_name):
    """Invites a team (by name) to a project."""
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    try:
        c.execute("SELECT name, owner_id FROM projects WHERE id = ?", (project_id,))
        project_details = c.fetchone();
        if not project_details or project_details['owner_id'] != inviter_user_id: return 'not_owner'
        # project_name = project_details['name'] # Not needed for insert
        c.execute("SELECT id, name, owner_id FROM teams WHERE name = ?", (team_name,))
        team_details = c.fetchone();
        if not team_details: return 'not_found'
        team_id = team_details['id']; team_owner_id = team_details['owner_id']
        c.execute("SELECT status FROM project_teams WHERE project_id = ? AND team_id = ?", (project_id, team_id))
        existing_link = c.fetchone();
        if existing_link: return 'already_exists'
        c.execute("INSERT INTO project_teams (project_id, team_id, team_name, invited_by_user_id, team_owner_id, status, invited_at) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                  (project_id, team_id, team_name, inviter_user_id, team_owner_id, datetime.now(timezone.utc)))
        conn.commit(); return 'invited'
    except Exception as e: print(f"Error inviting team to proj: {e}"); conn.rollback(); return 'error'
    finally: conn.close()

# --- *** CORRECTED get_project_team_invites_for_owner *** ---
def get_project_team_invites_for_owner(team_owner_id):
    """Fetches pending project invitations for teams owned by the user."""
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    # Join with projects table to get project_name
    c.execute("""
        SELECT pt.project_id, p.name as project_name, pt.team_id, pt.team_name, pt.invited_by_user_id, pt.invited_at
        FROM project_teams pt
        JOIN projects p ON pt.project_id = p.id
        WHERE pt.team_owner_id = ? AND pt.status = 'pending'
        ORDER BY pt.invited_at DESC
    """, (team_owner_id,))
    invites = c.fetchall(); conn.close(); return invites

def respond_to_project_invite_team(team_owner_id, project_id, team_id, accept=True):
    """Team owner responds to a project invite via project_id and team_id."""
    conn = connect_db(); c = conn.cursor()
    try:
        c.execute("SELECT 1 FROM project_teams WHERE project_id = ? AND team_id = ? AND team_owner_id = ? AND status = 'pending'", (project_id, team_id, team_owner_id))
        invite_check = c.fetchone();
        if not invite_check: print("Invite check failed for team response."); return False
        response_status = 'joined' if accept else 'rejected'
        c.execute("UPDATE project_teams SET status = ?, responded_at = ? WHERE project_id = ? AND team_id = ?", (response_status, datetime.now(timezone.utc), project_id, team_id))
        conn.commit(); return c.rowcount > 0
    except Exception as e: print(f"Error responding proj team invite: {e}"); conn.rollback(); return False
    finally: conn.close()
def get_project_pending_team_invites(project_id):
     """Fetches PENDING team invites issued BY a project owner."""
     conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
     c.execute("SELECT team_id, team_name, team_owner_id, invited_at FROM project_teams WHERE project_id = ? AND status = 'pending' ORDER BY invited_at DESC", (project_id,))
     pending_teams = c.fetchall(); conn.close(); return pending_teams
def cancel_project_team_invite(project_id, team_id, current_user_id):
    """Project owner cancels a pending team invite."""
    conn = connect_db(); c = conn.cursor()
    try:
         c.execute("SELECT owner_id FROM projects WHERE id = ?", (project_id,))
         owner_check = c.fetchone();
         if not owner_check or owner_check[0] != current_user_id: return 'not_owner'
         c.execute("DELETE FROM project_teams WHERE project_id = ? AND team_id = ? AND status = 'pending'", (project_id, team_id))
         conn.commit(); return 'cancelled' if c.rowcount > 0 else 'not_found'
    except Exception as e: print(f"Error cancelling project team invite: {e}"); conn.rollback(); return 'error'
    finally: conn.close()
def get_project_teams(project_id):
    """Fetches teams that have JOINED a specific project."""
    conn = connect_db(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT pt.team_id, pt.team_name, t.owner_username FROM project_teams pt JOIN teams t ON pt.team_id = t.id WHERE pt.project_id = ? AND pt.status = 'joined' ORDER BY pt.team_name", (project_id,))
    teams = c.fetchall(); conn.close(); return teams
def remove_team_from_project(project_id, team_id, current_user_id):
    """Removes a joined team link from a project. Only project owner."""
    conn = connect_db(); c = conn.cursor()
    try:
        c.execute("SELECT owner_id FROM projects WHERE id = ?", (project_id,))
        owner_check = c.fetchone()
        if not owner_check or owner_check[0] != current_user_id: return False # Not the owner
        c.execute("DELETE FROM project_teams WHERE project_id = ? AND team_id = ? AND (status = 'joined' OR status = 'rejected')", (project_id, team_id)) # Allow removing rejected links too
        conn.commit(); return c.rowcount > 0 # True if a row was deleted
    except Exception as e: print(f"Error removing team from project: {e}"); conn.rollback(); return False
    finally: conn.close()

