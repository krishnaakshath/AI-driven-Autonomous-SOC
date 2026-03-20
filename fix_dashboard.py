with open("dashboard.py", "r") as f:
    lines = f.readlines()

out = []
skip = False
for line in lines:
    if "if not logged_in:" in line:
        skip = True
        out.append(line)
        out.append('    # ── Not logged in: only show Login & Register ──\n')
        out.append('    pg = st.navigation({\n')
        out.append('        "Account": [\n')
        out.append('            st.Page("pages/_Login.py", title="Login"),\n')
        out.append('            st.Page("pages/_Register.py", title="Register"),\n')
        out.append('        ],\n')
        out.append('    }, position="sidebar")\n')
        out.append('\n')
        out.append('else:\n')
        out.append('    # ── Authenticated User Streamlined Hero Workflow ──\n')
        out.append('    workspace_pages = [\n')
        out.append('        st.Page("pages/01_Dashboard.py", title="SOC Dashboard", default=True),\n')
        out.append('        st.Page("pages/02_Alert_Triage.py", title="Alert Triage"),\n')
        out.append('        st.Page("pages/03_Investigation.py", title="Forensic Investigation"),\n')
        out.append('        st.Page("pages/04_SOAR_Response.py", title="SOAR Response"),\n')
        out.append('        st.Page("pages/05_Executive_Report.py", title="Executive Report"),\n')
        out.append('    ]\n')
        out.append('    config_pages = [\n')
        out.append('        st.Page("pages/06_Settings.py", title="Platform Settings"),\n')
        out.append('    ]\n')
        out.append('    pg = st.navigation({\n')
        out.append('        "Core Workflow": workspace_pages,\n')
        out.append('        "Configuration": config_pages,\n')
        out.append('    }, position="sidebar")\n')
        
    elif "# SIDEBAR LOGOUT BUTTON" in line:
        skip = False
        out.append(line)
    elif not skip:
        out.append(line)

with open("dashboard.py", "w") as f:
    f.writelines(out)
