import streamlit as st
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="OSINT Feeds | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIException:
    pass

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title, metric_card
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

# Import threat intel for reputation lookups
try:
    from services.threat_intel import threat_intel
    HAS_INTEL = True
except:
    HAS_INTEL = False

st.markdown(page_header("OSINT Threat Feeds", "Real-time actionable threat intelligence from global sources"), unsafe_allow_html=True)

import requests

@st.cache_data(ttl=300)
def fetch_urlhaus_recent():
    """Fetch recent malware URLs from abuse.ch URLhaus (free, no key)."""
    try:
        headers = {"User-Agent": "SOC-Dashboard-Client/1.0"}
        r = requests.post("https://urlhaus-api.abuse.ch/v1/urls/recent/", 
                          data={"limit": 25}, timeout=10, headers=headers)
        if r.status_code == 200:
            data = r.json()
            return data.get("urls", [])[:25]
    except Exception as e:
        print(f"URLhaus error: {e}")
    return []

@st.cache_data(ttl=300)
def fetch_threatfox_recent():
    """Fetch recent IoCs from abuse.ch ThreatFox (free, no key)."""
    try:
        headers = {"User-Agent": "SOC-Dashboard-Client/1.0"}
        r = requests.post("https://threatfox-api.abuse.ch/api/v1/",
                          json={"query": "get_iocs", "days": 1}, timeout=10, headers=headers)
        if r.status_code == 200:
            data = r.json()
            return data.get("data", [])[:25]
    except Exception as e:
        print(f"ThreatFox error: {e}")
    return []

@st.cache_data(ttl=3600)
def get_mx_records(domain):
    """Fetch MX records for a domain using Google DNS-over-HTTPS."""
    try:
        url = f"https://dns.google/resolve?name={domain}&type=MX"
        headers = {"User-Agent": "SOC-Dashboard-Client/1.0"}
        r = requests.get(url, timeout=5, headers=headers)
        if r.status_code == 200:
            data = r.json()
            # Status 0 means NOERROR
            if data.get("Status") == 0 and "Answer" in data:
                return [ans.get("data") for ans in data["Answer"]]
    except Exception as e:
        print(f"MX Lookup error: {e}")
    return []

def is_disposable(domain):
    """Check if a domain belongs to a known disposable email provider."""
    # Common ones — in production, this would be a much larger list or an API call
    DISPOSABLE_DOMAINS = {
        "mailinator.com", "guerrillamail.com", "temp-mail.org", "10minutemail.com",
        "yopmail.com", "trashmail.com", "getnada.com", "maildrop.cc",
    }
    return domain.lower() in DISPOSABLE_DOMAINS

def check_email_osint(email):
    """Perform real OSINT intelligence on an email address."""
    if not email or "@" not in email:
        return None
    
    domain = email.split("@")[-1].lower()
    intelligence = {
        "email": email,
        "domain": domain,
        "mx_records": get_mx_records(domain),
        "is_disposable": is_disposable(domain),
        "reputation": {},
        "risk_score": 0,
        "summary": []
    }

    # Verify MX Records
    if not intelligence["mx_records"]:
        intelligence["risk_score"] += 40
        intelligence["summary"].append("No valid MX records found for domain (High Risk: Identity may be fake)")
    else:
        intelligence["summary"].append(f"Domain has {len(intelligence['mx_records'])} active mail exchange servers")

    # Check Disposable
    if intelligence["is_disposable"]:
        intelligence["risk_score"] += 50
        intelligence["summary"].append("Disposable/Temporary email provider detected (High Risk)")

    # Reputation Checks (Real API data)
    if HAS_INTEL:
        vt = threat_intel.check_domain_virustotal(domain)
        if not vt.get("error"):
            intelligence["reputation"]["virustotal"] = vt
            if vt.get("is_malicious"):
                intelligence["risk_score"] += 60
                intelligence["summary"].append(f"VT Alert: Domain flagged as malicious by {vt.get('malicious_count')} vendors")
        
        otx = threat_intel.check_domain_otx(domain)
        if not otx.get("error"):
            intelligence["reputation"]["otx"] = otx
            pulse_count = otx.get("pulse_count", 0)
            if pulse_count > 5:
                intelligence["risk_score"] += 30
                intelligence["summary"].append(f"OTX Alert: Domain associated with {pulse_count} threat intelligence pulses")

    # Clamp risk score
    intelligence["risk_score"] = min(100, intelligence["risk_score"])
    return intelligence

st.markdown(section_title("Live OSINT Threat Feed"), unsafe_allow_html=True)

st.markdown("""
    <div class="glass-card" style="margin-bottom: 1.5rem;">
        <p style="color: #8B95A5; margin: 0;">
            Real-time intelligence from <strong>abuse.ch URLhaus</strong> and <strong>ThreatFox</strong>. 
            These are live malware URLs and Indicators of Compromise (IoCs) reported in the last 24 hours.
            <span style="color: #00C853;">No API key required — fully automated.</span>
        </p>
    </div>
""", unsafe_allow_html=True)

feed_tab1, feed_tab2, feed_tab3 = st.tabs(["Email OSINT Intelligence", "URLhaus (Malware URLs)", "ThreatFox (IoCs)"])

with feed_tab1:
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <p style="color: #8B95A5; margin: 0;">
                Perform real-time identity verification and reputation analysis on any email address.
                <strong>No breach data key required</strong> — uses technical indicators, DNS, and reputation feeds.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    email_q = st.text_input("Investigate Email Identity", placeholder="target@example.com")
    
    if st.button("Run OSINT Scan", type="primary"):
        if email_q and "@" in email_q:
            with st.spinner("Harvesting real-time intelligence..."):
                results = check_email_osint(email_q)
                
                if results:
                    col_metrics, col_details = st.columns([1, 2])
                    
                    with col_metrics:
                        risk = results["risk_score"]
                        risk_color = "#00C853" if risk < 20 else "#FFD700" if risk < 50 else "#FF8C00" if risk < 80 else "#FF4444"
                        st.markdown(metric_card(f"{risk}/100", "OSINT Risk Score", risk_color), unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"**Verification Status:** {'✅ ACTIVE' if results['mx_records'] else '🛑 FAILED'}")
                        st.markdown(f"**Anonymity Tool:** {'⚠️ YES' if results['is_disposable'] else '✅ NO'}")

                    with col_details:
                        st.markdown("###  Analysis Summary")
                        for item in results["summary"]:
                            icon = "✅" if "is active" in item or "active mail" in item else "⚠️" if "Disposable" in item else "🛑"
                            st.info(f"{icon} {item}")
                        
                        if results["mx_records"]:
                            with st.expander("Show Mail Servers (MX Records)"):
                                for mx in results["mx_records"]:
                                    st.code(mx, language=None)
                    
                    if results["reputation"]:
                        st.markdown("###  Domain Reputation (Live)")
                        rep_col1, rep_col2 = st.columns(2)
                        
                        with rep_col1:
                            if "virustotal" in results["reputation"]:
                                vt = results["reputation"]["virustotal"]
                                st.markdown(f"""
                                <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-left: 3px solid #00D4FF; border-radius: 4px;">
                                    <strong>VirusTotal Verdict</strong><br>
                                    <span style="color: #8B95A5; font-size: 0.8rem;">Reputation: {vt.get('reputation', 0)}</span><br>
                                    <span style="color: {'#FF4444' if vt.get('is_malicious') else '#00C853'}; font-size: 0.9rem;">
                                        Detected by {vt.get('malicious_count', 0)} security vendors
                                    </span>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with rep_col2:
                            if "otx" in results["reputation"]:
                                otx = results["reputation"]["otx"]
                                st.markdown(f"""
                                <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-left: 3px solid #bc13fe; border-radius: 4px;">
                                    <strong>AlienVault OTX Pulse Analysis</strong><br>
                                    <span style="color: #8B95A5; font-size: 0.8rem;">Pulse Count: {otx.get('pulse_count', 0)}</span><br>
                                    <span style="color: {'#FF4444' if otx.get('pulse_count', 0) > 5 else '#00C853'}; font-size: 0.9rem;">
                                        Associated with {otx.get('pulse_count', 0)} threat pulses
                                    </span>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.error("Intelligence harvest failed.")
        else:
            st.warning("Please enter a valid email address to scan.")

with feed_tab2:
    with st.spinner("Fetching live malware URLs from abuse.ch..."):
        urls = fetch_urlhaus_recent()
    
    if urls:
        st.success(f"**{len(urls)}** live malware URLs retrieved from URLhaus")
        for u in urls:
            status = u.get("url_status", "unknown")
            status_color = {"online": "#FF4444", "offline": "#00C853", "unknown": "#FF8C00"}.get(status, "#8B95A5")
            threat = u.get("threat", "Malware")
            
            st.markdown(f'''
            <div style="
                background: rgba(26,31,46,0.5);
                border-left: 4px solid {status_color};
                padding: 12px 15px;
                border-radius: 0 8px 8px 0;
                margin: 6px 0;
                font-size: 0.9rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <code style="color: #FF6B6B; font-size: 0.85rem;">{u.get("url", "N/A")[:80]}</code>
                        <div style="color: #8B95A5; font-size: 0.75rem; margin-top: 4px;">
                            {u.get("date_added", "N/A")} | Threat: <strong style="color: #00D4FF;">{threat}</strong>
                        </div>
                    </div>
                    <span style="background: {status_color}; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">{status.upper()}</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("Unable to reach URLhaus API. Try again in a moment.")

with feed_tab3:
    with st.spinner("Fetching live IoCs from ThreatFox..."):
        iocs = fetch_threatfox_recent()
    
    if iocs:
        st.success(f"**{len(iocs)}** live IoCs retrieved from ThreatFox")
        for ioc in iocs:
            ioc_type = ioc.get("ioc_type", "unknown")
            malware = ioc.get("malware_printable", "Unknown")
            confidence = ioc.get("confidence_level", 0)
            conf_color = "#FF4444" if confidence > 75 else "#FF8C00" if confidence > 50 else "#00C853"
            
            st.markdown(f'''
            <div style="
                background: rgba(26,31,46,0.5);
                border: 1px solid rgba(255,255,255,0.1);
                padding: 12px 15px;
                border-radius: 8px;
                margin: 6px 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <code style="color: #00D4FF; font-size: 0.85rem;">{ioc.get("ioc", "N/A")[:80]}</code>
                        <div style="color: #8B95A5; font-size: 0.75rem; margin-top: 4px;">
                            Type: <strong>{ioc_type}</strong> | Malware: <strong style="color: #FF6B6B;">{malware}</strong>
                        </div>
                    </div>
                    <span style="background: {conf_color}; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">{confidence}%</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("Unable to reach ThreatFox API. Try again in a moment.")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | OSINT Feeds</p></div>', unsafe_allow_html=True)
