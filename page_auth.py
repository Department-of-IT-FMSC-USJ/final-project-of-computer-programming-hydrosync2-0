import streamlit as st
import database
import re # For email validation

# --- HELPER FUNCTIONS ---
def navigate(page_name):
    """Sets the session state to navigate."""
    st.session_state.page = page_name
    # Rerun is often needed after setting state via button clicks
    st.rerun()

# --- HOME PAGE ---
def show_home():
    """Displays the main landing page with a clean, centered layout."""

    # Inject CSS for centering text and adjusting spacing
    st.markdown("""
        <style>
            /* Target the main block container USED BY COLUMNS more reliably */
            /* This targets the div Streamlit creates for the central column */
            div.st-emotion-cache-1r6slb0 { /* Adjust selector based on inspection if needed */
                display: flex;
                flex-direction: column;
                align-items: center; /* Center horizontally */
                text-align: center;  /* Center text elements within */
            }
            /* Explicitly center the image within its container */
             div[data-testid="stImage"] > img {
                display: block;
                margin-left: auto;
                margin-right: auto;
                margin-bottom: 3rem; /* More space below logo */
            }
             /* Style paragraphs */
             p.desc {
                color: #A0AEC0; /* Lighter text */
                margin-bottom: 1.5rem; /* Space below text */
                font-size: 1.1em;   /* Slightly larger text */
                line-height: 1.6;   /* Improve readability */
                max-width: 600px; /* Limit width for better reading */
            }
             /* Style prompt */
             p.prompt {
                font-weight: bold;
                color: #E2E8F0; /* Brighter text for prompt */
                margin-top: 1rem;
                margin-bottom: 2.5rem; /* More space below prompt */
                font-size: 1.1em;
            }
            /* Adjust button container spacing */
            div[data-testid="stHorizontalBlock"] {
                 gap: 1rem; /* Adjust gap between buttons */
                 justify-content: center; /* Center buttons horizontally */
                 margin-top: 1rem; /* Space above buttons */
            }
             /* Ensure buttons take appropriate width */
            .stButton>button {
                min-width: 120px; /* Give buttons a minimum width */
            }
        </style>
    """, unsafe_allow_html=True)

    # Use columns for overall centering
    col_empty1, col_main, col_empty2 = st.columns([1, 2, 1]) # Adjust ratios if needed

    with col_main:
        # Place elements directly within the centered column
        st.image("logo.png", width=350) # Centered logo via CSS

        # Description Text
        st.markdown(
            "<p class='desc'>Welcome! Access powerful water quality calculation tools, "
            "collaborate on projects, and ensure data integrity with our unique "
            "calculation ledger system.</p>", unsafe_allow_html=True
        )
        # Login/Register Prompt
        st.markdown(
            "<p class='prompt'>Please log in or register to continue.</p>", unsafe_allow_html=True
            )

        # Button row - Let Streamlit handle centering within the centered column
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("Login", use_container_width=True, key="home_login"):
                navigate("login")
        with col_btn2:
            if st.button("Register", use_container_width=True, key="home_register"):
                navigate("register")
        with col_btn3:
            if st.button("HydroScan", use_container_width=True, key="home_hydroscan"):
                navigate("hydroscan")


# --- LOGIN PAGE ---
def show_login():
    """Displays the login form."""
    col1, col2, col3 = st.columns([1, 1.5, 1]) # Center the form
    with col2:
        st.image("logo.png", width=150) # Smaller logo above form
        st.header("Login to HYDROSYNC")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    user_id = database.login_user(username, password)
                    if user_id:
                        # Success - Set session state in app.py's main logic
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_id = user_id
                        st.session_state.page = "dashboard" # Go to dashboard after login
                        st.query_params.clear() # Clear any lingering query params
                        st.rerun() # Rerun to reflect logged-in state
                    else:
                        st.error("Invalid username or password.")

        if st.button("← Back to Home", use_container_width=True):
            navigate("home")

# --- REGISTER PAGE ---
def show_register():
    """Displays the registration form."""
    col1, col2, col3 = st.columns([1, 1.5, 1]) # Center the form
    with col2:
        st.image("logo.png", width=150) # Smaller logo above form
        st.header("Register for HYDROSYNC")
        with st.form("register_form"):
            new_username = st.text_input("Create Username (min. 4 chars)")
            new_email = st.text_input("Email Address")
            new_password = st.text_input("Create Password (min. 8 chars)", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")

            if submitted:
                # Validation checks
                if not all([new_username, new_email, new_password, confirm_password]):
                    st.error("All fields are required.")
                elif len(new_username) < 4:
                    st.error("Username must be at least 4 characters long.")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", new_email): # Basic email format check
                    st.error("Please enter a valid email address.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters long.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Attempt registration
                    success = database.add_user(new_username, new_email, new_password)
                    if success:
                        st.success("Registration successful! You can now log in.")
                        # Don't navigate automatically, let user click Back
                    else:
                        st.error("Username or Email already exists. Please try another.")

        if st.button("← Back to Home", use_container_width=True):
             navigate("home")

