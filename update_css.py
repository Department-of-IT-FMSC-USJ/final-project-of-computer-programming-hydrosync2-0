import sys

new_css = '''st.markdown(
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
    """
)'''

with open('app.py', 'r') as f:
    lines = f.readlines()

with open('app.py', 'w') as f:
    f.writelines(lines[:25])
    f.write(new_css + "\n")
    f.writelines(lines[105:])
