import streamlit as st
import pandas as pd  # Import pandas to create the dataframe


def show_page():
    st.header("About Our Team")
    st.write(
        "This project was developed by a passionate team of first-year undergraduates from the "
        "Business Information Systems (Special) Degree program at the University of Sri Jayewardenepura."
    )
    st.markdown("---")

    # --- REMOVED: Old column-specific CSS ---
    # st.markdown(""" ... """)

    # --- Team Member Details ---
    # Create a list of dictionaries for the team data
    team_data = [
        {"Name": "Lahiru Lakmina", "CPM Number": "CPM 26989"},
        {"Name": "Nethmi Praneesha", "CPM Number": "CPM 27025"},
        {"Name": "Tishani Nethmini", "CPM Number": "CPM 27022"},
        {"Name": "Kaveesha Nethmini", "CPM Number": "CPM 27030"},
        {"Name": "Rivindu Rathnayake", "CPM Number": "CPM 26984"},
    ]

    # Create a pandas DataFrame from the data
    df = pd.DataFrame(team_data)

    st.subheader("Team Members")

    # Display the data in a clean, styled table
    st.dataframe(
        df,
        use_container_width=True,  # Make the table fit the page width
        hide_index=True,  # Remove the default row index
        column_config={  # Configure column headers for a cleaner look
            "Name": st.column_config.TextColumn("Name"),
            "CPM Number": st.column_config.TextColumn("CPM Number"),
        }
    )



