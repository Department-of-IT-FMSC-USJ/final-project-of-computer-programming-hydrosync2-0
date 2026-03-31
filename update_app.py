import re

with open('app.py', 'r') as f:
    code = f.read()

# 1. Add generate_template helper
template_helper = '''
import io
def generate_template(columns):
    df = pd.DataFrame(columns=columns)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return buffer.getvalue()
'''
if 'def generate_template' not in code:
    code = code.replace('import pandas as pd', 'import pandas as pd' + template_helper)

# 2. Update selectbox
selectbox_old = '''["Shannon-Wiener Index", "Pielou’s Evenness", "Simpson’s Diversity Index",
                                        "Margalef’s Richness Index", "Plankton Abundance",
                                        "Biodiversity (Advanced)", "Plankton (Advanced)", 
                                        "Water Quality & TSI", "Correlation & Heatmap"]'''
selectbox_new = '''["Shannon-Wiener Index", "Pielou’s Evenness", "Simpson’s Diversity Index",
                                        "Margalef’s Richness Index", "Plankton Abundance",
                                        "Water Quality & TSI"]'''
code = code.replace(selectbox_old, selectbox_new)

# 3. Add templates to file uploads
bio_upload_old = '''else:
                uploaded_file = st.file_uploader("Upload Excel/CSV (Must contain 'Count' column)")'''
bio_upload_new = '''else:
                st.download_button(label=" Download Empty Template", data=generate_template(["Species Name", "Count"]), file_name="biodiversity_template.xlsx", mime="application/vnd.ms-excel")
                uploaded_file = st.file_uploader("Upload filled Excel/CSV (Must contain 'Count' column)")'''
code = code.replace(bio_upload_old, bio_upload_new)

plankton_upload_old = '''else:
                uploaded_file = st.file_uploader("Upload Excel/CSV (Columns: n, V, V_src, A_src, A_a, V_d)")'''
plankton_upload_new = '''else:
                st.download_button(label=" Download Empty Template", data=generate_template(["n", "V", "V_src", "A_src", "A_a", "V_d"]), file_name="plankton_template.xlsx", mime="application/vnd.ms-excel")
                uploaded_file = st.file_uploader("Upload filled Excel/CSV")'''
code = code.replace(plankton_upload_old, plankton_upload_new)

wq_upload_old = '''else:
                uploaded_file = st.file_uploader("Upload Water Quality Excel File")'''
wq_upload_new = '''else:
                st.download_button(label=" Download Empty Template", data=generate_template(["Site_Name", "Chlorophyll-a", "Phosphorus", "Secchi_Depth", "Nitrogen"]), file_name="water_quality_template.xlsx", mime="application/vnd.ms-excel")
                uploaded_file = st.file_uploader("Upload filled Water Quality Excel File")'''
code = code.replace(wq_upload_old, wq_upload_new)

# 4. Remove advanced blocks using regex or string splitting
# We want to remove from 'elif function_choice == "Biodiversity (Advanced)":' 
# down to the end of 'elif function_choice == "Correlation & Heatmap":' block.
# Which ends right before 'elif current_page == "profile":' or similar.

# Let's use string split to drop the whole section.
parts = code.split('elif function_choice == "Biodiversity (Advanced)":')
if len(parts) == 2:
    start_code = parts[0]
    # find where 'elif current_page == "profile":' or similar starts
    end_idx = parts[1].find('elif current_page == "profile":')
    if end_idx != -1:
        end_code = parts[1][end_idx:]
        code = start_code + end_code

with open('app.py', 'w') as f:
    f.write(code)

print("Patch complete.")
