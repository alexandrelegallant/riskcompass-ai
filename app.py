"""
RiskCompass AI
WA Government Cyber Threat Prioritisation Tool
Bloom × CyberWest Hub × WA Office of Digital Government Hackathon
"""

import streamlit as st
import anthropic
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, io, sys, pathlib
from datetime import datetime

# Make scoring module importable from same directory
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from scoring import score_batch, ESSENTIAL_EIGHT, WA_POLICY_MAP

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RiskCompass AI · WA Government",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
  --navy:  #003865;
  --gold:  #D4A820;
  --red:   #C8102E;
  --orange:#E85D04;
  --teal:  #00857C;
}
[data-testid="stAppViewContainer"] { background: #F2F5F9; }

/* ── Main content — force dark text everywhere ── */
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] div,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] .stMarkdown,
[data-testid="stAppViewContainer"] .stRadio label,
[data-testid="stAppViewContainer"] .stTextArea label,
[data-testid="stAppViewContainer"] .stFileUploader label,
[data-testid="stAppViewContainer"] .stExpander summary,
[data-testid="stAppViewContainer"] [data-testid="stTab"] { color: #1a1a2e !important; }

/* Tab labels */
button[data-baseweb="tab"] { color: #003865 !important; font-weight: 600 !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: #003865 !important; border-bottom: 3px solid #003865 !important; }

/* Radio buttons */
.stRadio > div label { color: #1a1a2e !important; }

/* Expander header */
details summary p { color: #1a1a2e !important; }

/* ── Sidebar — white text on navy ── */
[data-testid="stSidebar"] { background: #003865 !important; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { color: #cce0f5 !important; }
[data-testid="stSidebar"] hr { border-color: #ffffff33; }

/* Sidebar selectbox dropdown — white background with dark text */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
  background-color: white !important;
  color: #1a1a2e !important;
}
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span {
  color: #1a1a2e !important;
}
[data-testid="stSidebar"] .stSelectbox svg { fill: #003865 !important; }

/* Sidebar expander content — dark text on white background */
[data-testid="stSidebar"] div[data-testid="stExpander"] {
  background: white !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] div[data-testid="stExpander"] * {
  color: #1a1a2e !important;
}
[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
  background: #f0f4f8 !important;
  color: #003865 !important;
  font-weight: 600 !important;
}
[data-testid="stSidebar"] div[data-testid="stExpander"] summary p,
[data-testid="stSidebar"] div[data-testid="stExpander"] summary span {
  color: #003865 !important;
}

/* Dataframe toolbar buttons — make them visible */
[data-testid="stDataFrame"] button,
[data-testid="stDataFrame"] [data-testid="StyledFullScreenButton"],
div[data-testid="stDataFrameResizable"] button { 
  color: #003865 !important;
  background: white !important;
  border: 1px solid #dde3ec !important;
}

/* Plotly legend text — force dark */
.js-plotly-plot .legendtext { fill: #1a1a2e !important; }
.js-plotly-plot .gtitle { fill: #003865 !important; }
.js-plotly-plot .xtitle, .js-plotly-plot .ytitle { fill: #1a1a2e !important; }
.js-plotly-plot .xtick text, .js-plotly-plot .ytick text { fill: #1a1a2e !important; }

.rc-banner {
  background: linear-gradient(135deg, #003865, #005B8E);
  color: white;
  padding: 1.4rem 2rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  display: flex; align-items: center; gap: 1.2rem;
}
.rc-banner h1 { margin:0; font-size:1.7rem; letter-spacing:-0.5px; }
.rc-banner p  { margin:0; opacity:0.8; font-size:0.88rem; }

.metric-card {
  background: white;
  border-radius: 10px;
  padding: 1.1rem 1rem;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  border-top: 4px solid #003865;
}
.metric-card .val  { font-size: 2.1rem; font-weight: 800; }
.metric-card .lbl  { font-size: 0.8rem; color: #777; margin-top: 0.15rem; }

.alert-row {
  background: white;
  border-radius: 8px;
  padding: 1rem 1.3rem;
  margin-bottom: 0.7rem;
  box-shadow: 0 1px 5px rgba(0,0,0,0.07);
  border-left: 5px solid #003865;
}
.alert-row.CRITICAL { border-left-color: #C8102E; }
.alert-row.HIGH     { border-left-color: #E85D04; }
.alert-row.MEDIUM   { border-left-color: #D4A820; }
.alert-row.LOW      { border-left-color: #00857C; }

.pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 0.77rem;
  font-weight: 700;
  margin-right: 4px;
}
.pill-CRITICAL { background:#C8102E; color:white; }
.pill-HIGH     { background:#E85D04; color:white; }
.pill-MEDIUM   { background:#D4A820; color:white; }
.pill-LOW      { background:#00857C; color:white; }
.pill-outline  { border:1px solid #003865; color:#003865; background:white; }

.stButton > button {
  background: #003865 !important;
  color: white !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  border: none !important;
}
.stButton > button * { color: white !important; }
.stButton > button p { color: white !important; }
.stButton > button:hover { background: #005B8E !important; }

div[data-testid="stExpander"] { 
  border-radius: 8px; 
  border: 1px solid #dde3ec;
  background: white !important;
}
div[data-testid="stExpander"] summary {
  background: white !important;
  color: #1a1a2e !important;
}
div[data-testid="stExpander"] summary:hover {
  background: #f0f4f8 !important;
}
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span {
  color: #1a1a2e !important;
  font-weight: 600 !important;
}
div[data-testid="stExpander"] > div {
  background: white !important;
}
/* File uploader — navy outer box, solid border, white text */
[data-testid="stFileUploader"],
[data-testid="stFileUploader"] > div,
[data-testid="stFileUploader"] > div > div,
[data-testid="stFileUploaderDropzone"],
section[data-testid="stFileUploaderDropzone"] {
  background: #003865 !important;
  background-color: #003865 !important;
  border: 2px solid #5a9fd4 !important;
  border-radius: 8px !important;
}
[data-testid="stFileUploader"] *,
[data-testid="stFileUploaderDropzone"] * { 
  color: white !important; 
}
/* Label "Upload .csv or .txt" and helper "200MB per file..." */
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] label *,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] > div > small,
[data-testid="stFileUploader"] span:not(button span) {
  color: white !important;
}
[data-testid="stFileUploader"] button,
[data-testid="stFileUploaderDropzone"] button {
  background: white !important;
  background-color: white !important;
  color: #003865 !important;
  border-radius: 6px !important;
  border: none !important;
}
[data-testid="stFileUploader"] button span,
[data-testid="stFileUploaderDropzone"] button span {
  color: #003865 !important;
}
.stDownloadButton > button { background: #00857C !important; }
</style>
""", unsafe_allow_html=True)

# ── Colour maps ───────────────────────────────────────────────────────────────
P_COLOUR = {"CRITICAL":"#C8102E","HIGH":"#E85D04","MEDIUM":"#D4A820","LOW":"#00857C"}

def pill(text, cls="outline"):
    c = {"CRITICAL":"#C8102E","HIGH":"#E85D04","MEDIUM":"#D4A820","LOW":"#00857C"}.get(cls)
    if c:
        return f'<span class="pill pill-{cls}">{text}</span>'
    return f'<span class="pill pill-outline">{text}</span>'

# ── Sample data ───────────────────────────────────────────────────────────────
SAMPLE_CSV = """title,cvss,category,internet_facing,exploit_available,active_exploitation,sensitive_data,business_criticality,patch_available,essential_eight_gap,affected_systems,agency,asset_owner,date_detected,affected_users,current_control,description
PAN-OS GlobalProtect RCE (CVE-2024-3400),10.0,Active Exploitation,True,True,True,True,high,True,Patch Applications,All Palo Alto firewalls,Dept of Finance,Network Team,2024-06-01,All remote staff,Perimeter firewall,Critical command injection in GlobalProtect VPN – actively exploited in the wild
Ransomware countdown posted by LockBit,9.5,Ransomware,True,True,True,True,high,False,,Potentially whole-of-agency,WA Health,CISO,2024-06-02,15000,Endpoint AV,LockBit posted a 72-hour countdown with WA Gov branding – unconfirmed if breach occurred
Phishing campaign targeting @wa.gov.au,7.5,Phishing,True,False,True,True,high,False,,23 staff accounts,Dept of Transport,IT Security,2024-06-02,23,Email filtering,23 employees clicked malicious links in 48 hrs – credential harvesting suspected
Suspicious PowerShell on DEPT-PC-0442,8.2,Active Exploitation,False,True,True,False,high,False,,Single workstation,Dept of Education,SOC Team,2024-06-02,1,EDR (contained),EDR flagged and auto-contained – possible lateral movement attempt
Third-party VPN login from Eastern Europe,8.0,Supply Chain,True,False,True,True,high,False,,Procurement system,Dept of Treasury,Vendor Management,2024-06-01,500,VPN access logs,Vendor account showing anomalous geolocation – access to procurement data
USB bypass on air-gapped critical systems,8.5,Insider Threat,False,False,True,True,high,False,,3 critical infrastructure systems,Water Corporation,OT Security,2024-05-31,3 systems,Physical security,USB policy bypassed on air-gapped zone – insider threat risk
Unpatched Windows Server 2019 (47 hosts),7.8,Vulnerability,False,False,False,False,medium,True,Patch Operating Systems,47 internal servers,Dept of Mines,IT Operations,2024-05-28,47 servers,Internal firewall,Missing MS24-003 patch on internal servers – no public exploit yet
No MFA on legacy LDAP directory,7.0,Access Control,False,False,False,True,medium,True,Multi-Factor Authentication,1200 service accounts,Main Roads WA,Identity Team,2024-05-25,1200,Password policy,Weak password policy + no MFA on 1200 service accounts
Log4Shell on legacy HR system (internal),6.5,Vulnerability,False,True,False,True,low,False,Patch Applications,Legacy HR system,Public Transport Authority,HR IT Team,2024-04-10,200,Network segmentation,CVE-2021-44228 – internal only firewall-segmented vendor patch Q3 2025
Expired SSL cert on Finance portal,3.5,Compliance,True,False,False,False,low,True,,Public-facing Finance portal,Dept of Finance,Web Team,2024-06-01,Public,HTTPS monitoring,Certificate expires in 3 days – no direct exploit but public trust risk
"""

WA_POLICY_CONTEXT = """
WA Government Cyber Security Policy 2024 key obligations:
- 1.7 Vulnerability Management: critical CVEs must be remediated within 48 hours of notification
- 3.1.1 Essential Eight: patch applications (48hrs critical), patch OS (48hrs critical), MFA mandatory for all privileged/remote access
- 3.4 Information Secure Procurement: third-party and supply chain risks must be assessed and managed
- 3.6 Identity and Access Management: MFA required for all privileged accounts and remote access
- 4.1 Adverse Event Analysis: all security events must be triaged and escalated appropriately
- 5.1 Incident Management: ransomware, active exploitation, and data breach require immediate escalation to DGov
- 5.3 Ransomware Position: do not pay ransoms; isolate affected systems; notify DGov immediately
- DGov Cyber Security Unit coordinates inter-entity responses and ACSC liaison
"""

# ── Claude client ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    try:
        return anthropic.Anthropic()
    except Exception:
        return None

client = get_client()

# ── AI enrichment (optional layer on top of rule-based scores) ────────────────
def ai_enrich(alerts_df: pd.DataFrame, agency_context: str) -> dict:
    """Ask Claude to add executive summary, action plan, and per-alert explanations."""
    alerts_json = alerts_df[["title","priority","priority_score","category",
                              "wa_policy_reference","timeframe","escalate_to_dgov",
                              "description","affected_systems"]].to_dict(orient="records")

    prompt = f"""You are RiskCompass AI, a cyber security decision-support tool for WA Government agencies.
The rule-based scoring engine has already ranked these alerts. Your job is to enrich with human-readable output.

AGENCY: {agency_context}

WA POLICY CONTEXT:
{WA_POLICY_CONTEXT}

SCORED ALERTS (already ranked):
{json.dumps(alerts_json, indent=2)}

Return ONLY valid JSON with this structure:
{{
  "executive_summary": "<3 sentences for a non-technical Director General — what is happening and what needs to happen now>",
  "immediate_action_required": <true|false>,
  "per_alert": {{
    "<alert title>": {{
      "recommended_action": "<specific actionable step>",
      "business_impact": "<consequence if not addressed>",
      "owner": "<Security Team|IT Team|Executive|DGov|Vendor>"
    }}
  }},
  "action_plan": [
    {{
      "step": 1,
      "timeframe": "<Immediate|24hrs|48hrs|2 weeks>",
      "action": "<specific action>",
      "owner": "<owner>"
    }}
  ]
}}

Return ONLY the JSON. No markdown. No preamble."""

    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = resp.content[0].text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)


def ai_chat(question: str, triage_df: pd.DataFrame, ai_data: dict, agency: str) -> str:
    alerts_summary = triage_df[["title","priority","priority_score","timeframe",
                                 "wa_policy_reference","escalate_to_dgov"]].to_dict(orient="records")
    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=f"""You are RiskCompass AI, a WA Government cyber security analyst assistant.
Agency: {agency}
WA Policy: {WA_POLICY_CONTEXT}
Triage results: {json.dumps(alerts_summary)}
AI enrichment: {json.dumps(ai_data)}
Answer concisely and practically. Use bullet points where helpful.""",
        messages=[{"role": "user", "content": question}]
    )
    return resp.content[0].text


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rc-banner">
  <div style="font-size:2.8rem; line-height:1">🧭</div>
  <div>
    <h1>RiskCompass AI</h1>
    <p>WA Government · Cyber Threat Prioritisation · Office of Digital Government</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    agency_name = st.text_input("Agency Name", placeholder="e.g. Dept of Health")
    agency_type = st.selectbox("Agency Type", [
        "General Government Agency",
        "Critical Infrastructure",
        "Health Service Provider",
        "Law Enforcement / WA Police",
        "University",
        "Government Trading Enterprise",
    ])
    agency_context = f"{agency_name} ({agency_type})" if agency_name else agency_type

    use_ai = st.toggle("✨ AI Enrichment (Claude)", value=(client is not None),
                       disabled=(client is None),
                       help="Adds AI explanations, actions & executive summary on top of rule-based scoring")
    if client is None:
        st.caption("⚠️ No API key — running in rule-based mode only")

    st.divider()
    st.markdown("### 📋 WA Policy Quick Ref")
    with st.expander("Essential Eight SLAs"):
        st.markdown("""
| Control | SLA |
|---------|-----|
| Patch Apps (critical) | **48 hrs** |
| Patch OS (critical) | **48 hrs** |
| MFA | Immediate |
| Admin Privileges | 2 weeks |
| App Control | 2 weeks |
| Backups | Immediate |
        """)
    with st.expander("When to escalate to DGov"):
        st.markdown("""
- Ransomware confirmed/suspected  
- Active exploitation underway  
- Citizen data breach  
- Critical infrastructure affected  
- Multi-agency impact  
        """)
    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%d %b %Y, %H:%M')} AWST")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔍  Triage", "📊  Dashboard", "💬  Ask RiskCompass"])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — INPUT & TRIAGE RESULTS
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("#### Upload or paste your vulnerability / alert data")

    input_mode = st.radio("Input method", ["📋 Paste CSV", "📁 Upload file", "🧪 Use sample data"],
                          horizontal=True)

    raw_csv = ""
    if input_mode == "📋 Paste CSV":
        raw_csv = st.text_area("Paste CSV data (with header row)", height=220,
                               placeholder="title,cvss,category,internet_facing,exploit_available,active_exploitation,sensitive_data,business_criticality,patch_available,essential_eight_gap,affected_systems,description\n...")
    elif input_mode == "📁 Upload file":
        f = st.file_uploader("Upload .csv or .txt", type=["csv","txt"])
        if f:
            raw_csv = f.read().decode("utf-8")
            st.success(f"Loaded: {f.name}")
    else:
        raw_csv = SAMPLE_CSV
        st.info("Using 10 sample WA Government vulnerability alerts.")

    with st.expander("📌 Expected CSV columns"):
        st.markdown("""
| Column | Type | Description |
|--------|------|-------------|
| `title` | text | Short alert name |
| `cvss` | 0–10 | CVSS base score |
| `category` | text | Active Exploitation / Ransomware / Phishing / Vulnerability / Insider Threat / Supply Chain / Access Control / Compliance |
| `internet_facing` | True/False | Is the system publicly exposed? |
| `exploit_available` | True/False | Known exploit exists? |
| `active_exploitation` | True/False | Actively being exploited in the wild? |
| `sensitive_data` | True/False | Sensitive or citizen data at risk? |
| `business_criticality` | high/medium/low | Asset criticality |
| `patch_available` | True/False | Fix available? |
| `essential_eight_gap` | text | Which E8 control does this affect? (optional) |
| `affected_systems` | text | What is affected? |
| `description` | text | Full description (optional, shown in detail) |
        """)

    run_btn = st.button("🚀  Run RiskCompass Triage", use_container_width=False)

    if run_btn and raw_csv.strip():
        try:
            df_input = pd.read_csv(io.StringIO(raw_csv))

            # Normalise boolean columns
            bool_cols = ["internet_facing","exploit_available","active_exploitation",
                         "sensitive_data","patch_available"]
            for c in bool_cols:
                if c in df_input.columns:
                    df_input[c] = df_input[c].map(
                        lambda x: str(x).strip().lower() in ("true","yes","1","y")
                    )

            alerts_list = df_input.to_dict(orient="records")
            scored = score_batch(alerts_list)
            result_df = pd.DataFrame(scored)
            st.session_state["triage_df"] = result_df
            st.session_state["ai_data"] = {}
            st.session_state["last_run"] = datetime.now().strftime("%H:%M:%S")

            # Optional AI enrichment
            if use_ai and client:
                with st.spinner("✨ Enriching with Claude AI explanations…"):
                    try:
                        ai_data = ai_enrich(result_df, agency_context)
                        st.session_state["ai_data"] = ai_data
                    except Exception as e:
                        st.warning(f"AI enrichment skipped (rule-based results still shown): {e}")

        except Exception as e:
            st.error(f"Could not parse data: {e}")

    elif run_btn:
        st.warning("Please provide some alert data first.")

    # ── Results ───────────────────────────────────────────────────────────────
    if "triage_df" in st.session_state:
        df = st.session_state["triage_df"]
        ai = st.session_state.get("ai_data", {})

        st.divider()
        st.caption(f"Last run: {st.session_state.get('last_run','')}")

        # Escalation / immediate banner
        dgov_count = df["escalate_to_dgov"].sum() if "escalate_to_dgov" in df.columns else 0
        crit_count  = (df["priority"] == "CRITICAL").sum()
        if crit_count > 0:
            st.error(f"🚨 **{crit_count} CRITICAL alert(s)** require immediate action."
                     + (f"  🔺 **{dgov_count} must be escalated to DGov.**" if dgov_count else ""))

        # Executive summary (AI)
        if ai.get("executive_summary"):
            st.info(f"📋 **Executive Summary:** {ai['executive_summary']}")

        # KPI cards
        counts = df["priority"].value_counts().to_dict()
        cols = st.columns(5)
        for col, (lbl, key, colour) in zip(cols, [
            ("Total",    None,       "#003865"),
            ("🔴 Critical","CRITICAL","#C8102E"),
            ("🟠 High",   "HIGH",    "#E85D04"),
            ("🟡 Medium", "MEDIUM",  "#D4A820"),
            ("🟢 Low",    "LOW",     "#00857C"),
        ]):
            val = len(df) if key is None else counts.get(key, 0)
            col.markdown(f"""
            <div class="metric-card" style="border-top-color:{colour}">
              <div class="val" style="color:{colour}">{val}</div>
              <div class="lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # ── Prioritised alert list ─────────────────────────────────────────────
        st.markdown("### 📋 Prioritised Alerts")
        for _, row in df.sort_values("priority_score", ascending=False).iterrows():
            p = row["priority"]
            title = row.get("title", "Unnamed alert")
            per = ai.get("per_alert", {}).get(title, {})
            with st.expander(
                f"#{int(row.get('id', row.name))+1 if 'id' not in row else row.name+1}  ·  "
                f"[{p}]  {title}  —  Score: {row['priority_score']}/100",
                expanded=(p == "CRITICAL")
            ):
                c1, c2 = st.columns([2,1])
                with c1:
                    if row.get("description"):
                        st.markdown(f"**Description:** {row['description']}")
                    if row.get("affected_systems"):
                        st.markdown(f"**Affected Systems:** {row['affected_systems']}")
                    if per.get("recommended_action"):
                        st.markdown(f"**Recommended Action:** {per['recommended_action']}")
                    if per.get("business_impact"):
                        st.markdown(f"**Business Impact:** {per['business_impact']}")
                with c2:
                    st.markdown(f"**Priority:** {pill(p, p)}", unsafe_allow_html=True)
                    st.markdown(f"**Score:** `{row['priority_score']}/100`")
                    st.markdown(f"**Timeframe:** `{row.get('timeframe','–')}`")
                    st.markdown(f"**Category:** `{row.get('category','–')}`")
                    st.markdown(f"**WA Policy:** `{row.get('wa_policy_reference','–')}`")
                    if per.get("owner"):
                        st.markdown(f"**Owner:** `{per['owner']}`")
                    if row.get("escalate_to_dgov"):
                        st.error("🔺 Escalate to DGov")

                    # ── Score breakdown ──────────────────────────────────────
                    cvss = float(row.get("cvss", 5.0))
                    cvss_pts = round((cvss / 10.0) * 40)
                    exploit_pts = 20 if row.get("active_exploitation") else (12 if row.get("exploit_available") else 0)
                    exposure_pts = 15 if row.get("internet_facing") else 0
                    data_pts = 10 if row.get("sensitive_data") else 0
                    crit_map = {"high":10,"medium":5,"low":2}
                    crit_pts = crit_map.get(str(row.get("business_criticality","medium")).lower(), 5)
                    patch_pts = 5 if not row.get("patch_available", True) else 0

                    with st.expander("🔢 Score breakdown"):
                        breakdown_rows = []
                        breakdown_rows.append(f"| CVSS {cvss} severity | +{cvss_pts} |")
                        if exploit_pts == 20:
                            breakdown_rows.append(f"| Active exploitation | +{exploit_pts} |")
                        elif exploit_pts == 12:
                            breakdown_rows.append(f"| Known exploit available | +{exploit_pts} |")
                        if exposure_pts:
                            breakdown_rows.append(f"| Internet-facing exposure | +{exposure_pts} |")
                        if data_pts:
                            breakdown_rows.append(f"| Sensitive data at risk | +{data_pts} |")
                        breakdown_rows.append(f"| {str(row.get('business_criticality','medium')).title()} business criticality | +{crit_pts} |")
                        if patch_pts:
                            breakdown_rows.append(f"| No patch available | +{patch_pts} |")
                        breakdown_rows.append(f"| **Total** | **{row['priority_score']}/100** |")
                        st.markdown("| Factor | Points |\n|--------|--------|\n" + "\n".join(breakdown_rows))

        # ── Action plan ───────────────────────────────────────────────────────
        if ai.get("action_plan"):
            st.markdown("---")
            st.markdown("### 🗓️ AI-Recommended Action Plan")
            plan_df = pd.DataFrame(ai["action_plan"])
            plan_df.columns = [c.title() for c in plan_df.columns]
            st.dataframe(plan_df, use_container_width=True, hide_index=True)

        # ── Export ────────────────────────────────────────────────────────────
        st.markdown("---")
        export_cols = [c for c in ["title","priority","priority_score","category",
                                    "timeframe","wa_policy_reference","escalate_to_dgov",
                                    "affected_systems","description"] if c in df.columns]
        csv_out = df[export_cols].sort_values("priority_score", ascending=False).to_csv(index=False)
        st.download_button("⬇️  Export Results CSV",
                           data=csv_out,
                           file_name=f"riskcompass_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                           mime="text/csv")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    if "triage_df" not in st.session_state:
        st.info("Run a triage first to see the dashboard.")
    else:
        df = st.session_state["triage_df"]
        st.markdown("### 📊 Threat Landscape Dashboard")

        c1, c2 = st.columns(2)

        # Shared layout defaults for all charts
        CHART_LAYOUT = dict(
            paper_bgcolor="white",
            font=dict(color="#1a1a2e", family="sans-serif", size=12),
            title_font=dict(color="#003865", size=14),
            margin=dict(t=45, b=15, l=10, r=10),
        )

        with c1:
            # Priority donut
            p_counts = df["priority"].value_counts().reset_index()
            p_counts.columns = ["Priority","Count"]
            fig = px.pie(p_counts, names="Priority", values="Count",
                         color="Priority", color_discrete_map=P_COLOUR,
                         hole=0.52, title="Alerts by Priority")
            fig.update_layout(**CHART_LAYOUT,
                              legend=dict(font=dict(color="#1a1a2e")))
            fig.update_traces(textfont_color="white")
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            # Category horizontal bar
            if "category" in df.columns:
                cat = df["category"].value_counts().reset_index()
                cat.columns = ["Category","Count"]
                fig2 = px.bar(cat, x="Count", y="Category", orientation="h",
                              color="Count",
                              color_continuous_scale=["#4a90d9","#C8102E"],
                              title="Alerts by Category")
                fig2.update_layout(**CHART_LAYOUT,
                                   coloraxis_showscale=False,
                                   yaxis=dict(title="", color="#1a1a2e", tickfont=dict(color="#1a1a2e")),
                                   xaxis=dict(title="Count", color="#1a1a2e", tickfont=dict(color="#1a1a2e")))
                st.plotly_chart(fig2, use_container_width=True)

        # Score scatter
        df_plot = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
        df_plot["#"] = df_plot.index + 1
        fig3 = px.scatter(df_plot, x="#", y="priority_score",
                          color="priority", size="priority_score",
                          hover_data=["title","category","timeframe"],
                          color_discrete_map=P_COLOUR,
                          title="Alert Priority Scores (ranked)",
                          labels={"#":"Alert Rank","priority_score":"Score (0–100)"})
        fig3.update_layout(**CHART_LAYOUT,
                           plot_bgcolor="#F9FAFB",
                           xaxis=dict(color="#1a1a2e", tickfont=dict(color="#1a1a2e"), gridcolor="#e0e0e0"),
                           yaxis=dict(color="#1a1a2e", tickfont=dict(color="#1a1a2e"), gridcolor="#e0e0e0"),
                           legend=dict(font=dict(color="#1a1a2e")))
        st.plotly_chart(fig3, use_container_width=True)

        # Timeframe distribution
        tf_order = ["Immediate (now)","Within 24 hours","Within 48 hours","Within 2 weeks","Scheduled"]
        if "timeframe" in df.columns:
            tf = df["timeframe"].value_counts().reindex(tf_order).dropna().reset_index()
            tf.columns = ["Timeframe","Count"]
            colours_tf = ["#C8102E","#E85D04","#D4A820","#00857C","#6c757d"][:len(tf)]
            fig4 = px.bar(tf, x="Timeframe", y="Count",
                          color="Timeframe",
                          color_discrete_sequence=colours_tf,
                          title="Remediation Urgency — How Many Need Action When?")
            fig4.update_layout(**CHART_LAYOUT,
                               plot_bgcolor="#F9FAFB",
                               showlegend=False,
                               xaxis=dict(color="#1a1a2e", tickfont=dict(color="#1a1a2e"), gridcolor="#e0e0e0"),
                               yaxis=dict(color="#1a1a2e", tickfont=dict(color="#1a1a2e"), gridcolor="#e0e0e0"))
            st.plotly_chart(fig4, use_container_width=True)

        # DGov escalation table
        if "escalate_to_dgov" in df.columns:
            esc = df[df["escalate_to_dgov"] == True]
            if not esc.empty:
                st.markdown("### 🔺 DGov Escalation Required")
                show_cols = [c for c in ["title","priority","category","timeframe","wa_policy_reference"]
                             if c in esc.columns]
                st.dataframe(esc[show_cols].sort_values("priority", key=lambda x: x.map(
                    {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3})),
                    use_container_width=True, hide_index=True)

        # Essential Eight gap analysis
        if "essential_eight_gap" in df.columns:
            e8 = df[df["essential_eight_gap"].notna() & (df["essential_eight_gap"] != "")]
            if not e8.empty:
                st.markdown("### 🔐 Essential Eight Gap Analysis")
                gap_counts = e8["essential_eight_gap"].value_counts().reset_index()
                gap_counts.columns = ["Control","Alert Count"]
                fig5 = px.bar(gap_counts, x="Control", y="Alert Count",
                              color="Alert Count",
                              color_continuous_scale=["#4a90d9","#C8102E"],
                              title="Alerts Mapped to Essential Eight Controls")
                fig5.update_layout(**{**CHART_LAYOUT, "margin": dict(t=45, b=100)},
                                   plot_bgcolor="#F9FAFB",
                                   coloraxis_showscale=False,
                                   xaxis=dict(tickangle=-30, color="#1a1a2e", tickfont=dict(color="#1a1a2e")),
                                   yaxis=dict(color="#1a1a2e", tickfont=dict(color="#1a1a2e"), gridcolor="#e0e0e0"))
                st.plotly_chart(fig5, use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — AI CHAT
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 💬 Ask RiskCompass AI")
    st.markdown("Get briefings, incident checklists, policy guidance, or ask anything about your results.")

    if "triage_df" not in st.session_state:
        st.info("Run a triage first, then ask follow-up questions here.")
    elif not client:
        st.warning("AI chat requires an Anthropic API key. Set `ANTHROPIC_API_KEY` and restart.")
    else:
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        # ── One-click DG Brief ────────────────────────────────────────────────
        st.markdown("#### 📄 One-Click Reports")
        dg_col, ir_col, policy_col = st.columns(3)
        if dg_col.button("🏛️ Generate DG Brief", use_container_width=True, type="primary"):
            st.session_state["pending_q"] = """Generate a formal Director General Brief with these exact sections:
**SITUATION:** What is happening right now (2 sentences)
**TOP ISSUE:** The single most critical threat and why
**IMMEDIATE ACTION REQUIRED:** What must happen in the next 24 hours
**DGOV ESCALATION:** Which issues require escalation to the Office of Digital Government and why
**BUSINESS IMPACT:** What happens if we don't act
**RECOMMENDED DECISION:** What the DG should approve or authorise
**NEXT 48 HOURS:** The prioritised action list with owners
Keep it concise, non-technical, and suitable for a Director General."""

        if ir_col.button("🚨 Incident Response Checklist", use_container_width=True):
            st.session_state["pending_q"] = "Give me a step-by-step incident response checklist for the highest priority CRITICAL alert. Include who does each step, in what order, and what to document."

        if policy_col.button("📋 WA Policy Obligations", use_container_width=True):
            st.session_state["pending_q"] = "List all my WA Cyber Security Policy 2024 obligations based on these alerts. For each obligation, state the policy section, what I must do, and by when."

        st.divider()

        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        st.markdown("**💬 Or ask your own question:**")
        suggestions = [
            "Which alerts must I escalate to DGov and what do I say?",
            "Summarise HIGH and CRITICAL alerts for my security team standup",
            "What are my Essential Eight gaps from these alerts?",
        ]
        cols = st.columns(3)
        for i, s in enumerate(suggestions):
            if cols[i].button(s, key=f"sug_{i}", use_container_width=True):
                st.session_state["pending_q"] = s

        prompt = st.chat_input("Ask about your triage results…")
        if "pending_q" in st.session_state:
            prompt = st.session_state.pop("pending_q")

        if prompt:
            st.session_state["chat_history"].append({"role":"user","content":prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    try:
                        answer = ai_chat(
                            prompt,
                            st.session_state["triage_df"],
                            st.session_state.get("ai_data", {}),
                            agency_context
                        )
                        st.markdown(answer)
                    except anthropic.AuthenticationError:
                        answer = (
                            "Claude AI is currently unavailable because the API key is invalid. "
                            "The core RiskCompass triage, scoring, policy mapping, dashboard, "
                            "and DGov escalation logic still work offline. Please check your "
                            "ANTHROPIC_API_KEY and restart the app."
                        )
                        st.error(answer)
                    except Exception as e:
                        answer = f"AI assistant unavailable, but rule-based triage still works. Error: {e}"
                        st.warning(answer)
            st.session_state["chat_history"].append({"role":"assistant","content":answer})
            st.rerun()

        if st.session_state.get("chat_history"):
            if st.button("🗑️ Clear chat"):
                st.session_state["chat_history"] = []
                st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#aaa;font-size:0.78rem;">'
    '🧭 RiskCompass AI · Human-in-the-loop cyber decision support · '
    'Bloom × CyberWest Hub × WA Office of Digital Government Hackathon'
    '</p>',
    unsafe_allow_html=True
)
