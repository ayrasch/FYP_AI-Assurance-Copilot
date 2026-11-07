"""AI Assurance Copilot — FYP UI Prototype.

Run: streamlit run app.py
The bundled services/assessment.py is a transparent DEMO adapter.
Replace it with your team's backend and verified RAG outputs when ready.
"""
from __future__ import annotations

import html
import json
import uuid
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from services.assessment import assess

st.set_page_config(page_title="AI Assurance Copilot | V2", page_icon="🛡️", layout="wide")

PAGES = ["Welcome", "Guided Intake", "Dashboard", "Human Review", "Reports"]
SEVERITIES = ["Critical", "High", "Medium", "Low"]
REVIEW_STATUSES = ["Pending", "Approved", "Rejected", "Needs Revision"]
SEVERITY_COLORS = {"Critical": "#e14e61", "High": "#f49859", "Medium": "#f0c663", "Low": "#38c3b3"}
YES_NO = ["Not sure", "Yes", "No"]

st.markdown("""
<style>
.stApp {background: #08192d; color: #e9f2ff;}
[data-testid="stSidebar"] {background: #0c233b; border-right: 1px solid #24435d;}
[data-testid="stHeader"] {background: #08192d;}
[data-testid="stMetric"] {background:#102d49;border:1px solid #274661;border-radius:14px;padding:16px;}
[data-testid="stMetricLabel"] {color:#aac3d9;}
[data-testid="stMetricValue"] {color:#fff;}
h1,h2,h3 {color:#f0f6ff !important;}
div.stButton > button[kind="primary"],div.stFormSubmitButton > button[kind="primary"]
 {background:#078b99;border:0;color:white;}
.hero {background:linear-gradient(125deg,#123b60 0%,#0d2b4a 60%,#073e4a 100%);
 border:1px solid #28617b;border-radius:20px;padding:38px 40px;margin:14px 0 22px;}
.hero-tag {color:#67e8e0;letter-spacing:.12em;font-size:.77rem;font-weight:700;text-transform:uppercase;}
.hero-title {font-size:2.55rem;line-height:1.15;color:#fff;font-weight:800;margin:14px 0;}
.hero-sub {font-size:1.06rem;color:#c4d7e8;max-width:760px;line-height:1.7;}
.step-card {background:#102d49;border:1px solid #274661;border-radius:16px;padding:22px 20px;min-height:205px;}
.step-num {display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;
 border-radius:12px;background:#076f85;color:#dffaff;font-weight:800;}
.step-title {font-weight:700;font-size:1.08rem;color:#fff;margin:16px 0 8px;}
.step-desc {font-size:.91rem;line-height:1.55;color:#b1c7dc;}
.info-strip {border:1px solid #27536b;background:#0e2942;border-radius:12px;
 padding:16px 19px;color:#c8e2ee;margin:12px 0;}
.fancy-card {border:1px solid #274661;background:#102d49;border-radius:14px;padding:18px;margin:8px 0;}
.small-label {color:#84baca;font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;}


/* 1. Sidebar Navigation 文字颜色 */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #E8F1FF !important;
}

/* 2. Sidebar 提示文字 */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #B8CCE0 !important;
}

/* 3. Secondary Button 文字及背景 */
div.stButton > button[kind="secondary"] {
    background-color: #173B59 !important;
    color: #FFFFFF !important;
    border: 1px solid #3B718D !important;
}

/* 4. Secondary Button Hover */
div.stButton > button[kind="secondary"]:hover {
    background-color: #245779 !important;
    color: #FFFFFF !important;
    border-color: #54C9D3 !important;
}

</style>


""", unsafe_allow_html=True)


# ---------- Helpers ----------
def init_state():
    defaults = {
        "assessments": {}, "draft": {}, "current_step": 1,
        "navigation": "Welcome", "nav_version": 0, "selected_assessment": None,
        "step2_cache": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go(page: str):
    st.session_state.navigation = page
    # Streamlit disallows reassigning an already instantiated widget key.
    # Incrementing the radio key remounts navigation on the destination page.
    st.session_state.nav_version += 1
    st.rerun()


def nav_changed():
    key = f"nav_{st.session_state.nav_version}"
    st.session_state.navigation = st.session_state[key]


def choose(options, val):
    return options.index(val) if val in options else 0


def safe(value):
    return html.escape(str(value or ""), quote=True)


def date_now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalized(result, profile):
    """Keep the UI contract stable when a backend returns missing optional fields."""
    if not isinstance(result, dict):
        raise ValueError("Assessment backend must return a dictionary")
    result = dict(result)
    findings = result.get("findings") or []
    if not isinstance(findings, list):
        raise ValueError("'findings' must be a list")
    cleaned = []
    for n, finding in enumerate(findings, 1):
        if not isinstance(finding, dict):
            continue
        f = dict(finding)
        f.setdefault("id", f"F-{n:03d}")
        for key in ["category", "risk", "description", "recommendation", "framework", "clause", "citation", "evidence"]:
            f.setdefault(key, "Not available")
        if f.get("severity") not in SEVERITIES:
            f["severity"] = "Unknown"
        if f.get("review_status") not in REVIEW_STATUSES:
            f["review_status"] = "Pending"
        f.setdefault("control_status", "Needs assessment")
        f.setdefault("original_recommendation", f.get("recommendation", ""))
        f.setdefault("reviewer", "")
        f.setdefault("review_date", "")
        f.setdefault("review_notes", "")
        f.setdefault("review_history", [])
        cleaned.append(f)
    result["findings"] = cleaned
    result["profile"] = profile
    return result


def is_demo(result):
    return "DEMO" in str(result.get("run_mode", "")).upper() or result.get("source_verified") is False


def ready_for_final(result):
    fs = result.get("findings", [])
    return (bool(fs) and not is_demo(result) and result.get("source_verified") is True
            and all(f.get("review_status") in ("Approved", "Rejected") for f in fs))


def assessment_options():
    return list(st.session_state.assessments.keys())


def selected_record(key="record"):
    ids = assessment_options()
    if not ids:
        st.info("No assessment yet. Start with Guided Intake or load a demo example.")
        if st.button("Go to Guided Intake →", key=f"empty_{key}", type="primary"):
            go("Guided Intake")
        return None, None
    chosen = st.selectbox("Assessment", ids,
        index=ids.index(st.session_state.selected_assessment)
        if st.session_state.selected_assessment in ids else len(ids)-1,
        format_func=lambda ident: (
            f"{st.session_state.assessments[ident]['profile'].get('system_name', 'Unnamed')}"
            f" · {ident[-8:]} · {st.session_state.assessments[ident].get('created_at', '')[:16]}"
        ), key=f"select_{key}")
    st.session_state.selected_assessment = chosen
    return chosen, st.session_state.assessments[chosen]


def demo_profile():
    return {
        "system_name": "Customer Support Chatbot (Demo)",
        "owner": "Customer Service", "purpose": "Answers retail customer questions using an LLM.",
        "industry": "Retail", "model_type": "Generative AI / LLM", "deployment": "Cloud",
        "personal_data": "Yes", "public_access": "Yes", "human_oversight": "No",
        "sensitive_decisions": "No", "data_sensitivity": "Confidential",
        "third_party_api": "Yes", "authentication": "Not sure",
        "data_storage": "Cloud database", "privacy_controls": "Not sure",
        "retention_policy": "Not sure",
    }


def seed_demo():
    st.session_state.draft = demo_profile()
    st.session_state.current_step = 1
    st.session_state.step2_cache = {}
    go("Guided Intake")


def start_assessment(profile):
    # An actual backend only needs to satisfy assess(profile) -> (result, run_mode).
    # Do not fake agent-by-agent progress when backend exposes no stage events.
    with st.status("Running assessment…", expanded=True) as status:
        st.write("1 / 4 · Intake: validating the submitted system profile")
        if not all(str(profile.get(field, "")).strip() for field in ("system_name", "owner", "purpose")):
            status.update(label="Assessment failed", state="error")
            st.error("System name, owner and purpose are required.")
            return
        st.write("2 / 4 · Mapping: passing intake data to the assessment adapter")
        try:
            result, mode = assess(profile.copy())
            result = normalized(result, profile.copy())
        except Exception as exc:
            status.update(label="Assessment failed", state="error")
            st.error(f"Assessment backend error: {exc}")
            return
        st.write("3 / 4 · Risk: findings received and normalised")
        st.write("4 / 4 · Documentation: draft report data prepared")
        if "DEMO" in str(mode).upper():
            st.caption("Demo adapter only: no real agents, RAG retrieval or framework verification ran.")
        status.update(label="Draft assessment ready", state="complete", expanded=False)
    ident = f"ASM-{uuid.uuid4().hex[:10].upper()}"
    result["assessment_id"] = ident
    result["created_at"] = date_now()
    result["run_mode"] = mode
    result["assessment_status"] = "Draft"
    st.session_state.assessments[ident] = result
    st.session_state.selected_assessment = ident
    st.session_state.draft = {}
    st.session_state.current_step = 1
    st.session_state.step2_cache = {}
    go("Dashboard")


def source_box(f):
    st.write("**Framework:**", f.get("framework", "Not available"))
    st.write("**Clause:**", f.get("clause", "Not available"))
    st.write("**Citation:**", f.get("citation", "Not available"))
    st.write("**Evidence:**", f.get("evidence", "Not available"))
    st.caption("Demo citations are placeholders. Real citations must be retrieved and verified by the Mapping/RAG agent.")


def summary_table(findings):
    return pd.DataFrame([{
        "ID": f.get("id"), "Risk": f.get("risk"), "Category": f.get("category"),
        "Severity": f.get("severity"), "Control status": f.get("control_status"),
        "Review status": f.get("review_status"),
    } for f in findings])


def html_report(record, final=False):
    """Safe HTML draft preview/export; PDF belongs to the future documentation agent."""
    profile = record.get("profile", {})
    fs = record.get("findings", [])
    reviewed = sum(f.get("review_status") in ("Approved", "Rejected") for f in fs)
    rows = "".join(
        "<tr>" + "".join(f"<td>{safe(f.get(k))}</td>" for k in
        ("id", "risk", "severity", "category", "control_status", "review_status")) + "</tr>"
        for f in fs
    ) or '<tr><td colspan="6">No findings</td></tr>'
    details = "".join(
        f"<section><h3>{safe(f.get('id'))} — {safe(f.get('risk'))}</h3>"
        f"<p><b>Description:</b> {safe(f.get('description'))}</p>"
        f"<p><b>Recommended control:</b> {safe(f.get('recommendation'))}</p>"
        f"<p><b>Control gap/status:</b> {safe(f.get('control_status'))}</p>"
        f"<p><b>Framework:</b> {safe(f.get('framework'))} | <b>Clause:</b> {safe(f.get('clause'))}</p>"
        f"<p><b>Citation:</b> {safe(f.get('citation'))}</p>"
        f"<p><b>Evidence:</b> {safe(f.get('evidence'))}</p>"
        f"<p><b>Reviewer:</b> {safe(f.get('reviewer'))} | <b>Status:</b> {safe(f.get('review_status'))}</p>"
        f"<p><b>Review notes:</b> {safe(f.get('review_notes'))}</p></section>"
        for f in fs
    )
    roadmap = "".join(
        f"<li><b>{safe(f.get('severity'))}:</b> {safe(f.get('risk'))} — "
        f"{safe(f.get('recommendation'))}</li>"
        for f in sorted(fs, key=lambda f: SEVERITIES.index(f.get('severity')) if f.get('severity') in SEVERITIES else 9)
        if f.get("review_status") != "Rejected"
    ) or "<li>No open actions from the current draft.</li>"
    title = "Final assurance report" if final else "DRAFT — illustrative assurance report"
    notice = ("Final workflow approved; source verification is indicated by the backend." if final else
              "Prototype draft. Findings may be synthetic or unverified. Not a professional audit or compliance certification.")
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
    <title>{safe(title)}</title><style>
    body{{font:15px/1.6 Arial,sans-serif;max-width:940px;margin:36px auto;color:#172b43;padding:0 18px}}
    h1,h2,h3{{color:#123b60}}h2{{border-bottom:1px solid #cfdde7;padding-bottom:6px}}
    table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{border:1px solid #cfdde7;padding:8px;text-align:left;vertical-align:top}}
    th{{background:#e7f2f5}}section{{border-bottom:1px solid #dde5ed;padding:9px 0}}
    .notice{{padding:12px;background:#fff4db;border-left:4px solid #dd9b23}}
    @media print{{body{{margin:12mm}}section{{break-inside:avoid}}}}
    </style></head><body><h1>{safe(title)}</h1><p class="notice">{safe(notice)}</p>
    <p><b>Assessment ID:</b> {safe(record.get('assessment_id'))} &nbsp; <b>Created:</b> {safe(record.get('created_at'))}</p>
    <h2>1. Executive summary</h2><p><b>System:</b> {safe(profile.get('system_name'))}</p>
    <p><b>Owner:</b> {safe(profile.get('owner'))} | <b>Industry:</b> {safe(profile.get('industry'))}</p>
    <p><b>Purpose:</b> {safe(profile.get('purpose'))}</p>
    <p>{safe(record.get('summary', 'Assessment findings require human review.'))}</p>
    <p>Findings: {len(fs)} | Reviewed: {reviewed} | Pending / revision: {len(fs)-reviewed}</p>
    <h2>2. Risk register</h2><table><thead><tr><th>ID</th><th>Risk</th><th>Severity</th><th>Category</th><th>Control status</th><th>Review</th></tr></thead><tbody>{rows}</tbody></table>
    <h2>3. Control gap analysis & citations</h2>{details}
    <h2>4. Draft remediation roadmap</h2><p>Illustrative priority order by severity; owners, dates and feasibility need validation.</p><ol>{roadmap}</ol>
    <h2>5. Human review status</h2><p>{reviewed} of {len(fs)} findings have an approval/rejection decision.</p>
    <h2>6. Limitations</h2><p>Do not treat demo outputs or citation placeholders as verified framework requirements. A qualified human reviewer remains responsible.</p>
    </body></html>'''


init_state()

with st.sidebar:
    st.title("🛡️ AI Assurance")
    st.caption("COPILOT · FYP UI PROTOTYPE V2")
    st.divider()
    st.radio("Navigation", PAGES, index=choose(PAGES, st.session_state.navigation),
             key=f"nav_{st.session_state.nav_version}", on_change=nav_changed)
    st.divider()
    st.info("Demo adapter included. RAG and AI agents require the team's backend.")
    st.caption(f"Assessments in this session: {len(st.session_state.assessments)}")
    st.caption("Session data is temporary; refresh/restart may clear it.")

page = st.session_state.navigation

# ---------- 01 / Welcome ----------
if page == "Welcome":
    st.markdown('''<div class="hero"><div class="hero-tag">AI Security · Governance · Risk Assessment</div>
    <div class="hero-title">Welcome to AI Assurance Copilot</div>
    <div class="hero-sub">Describe your AI system, assess illustrative risk indicators, review findings and prepare a draft assurance report — in one guided workspace.</div></div>''', unsafe_allow_html=True)
    st.subheader("How it works")
    steps = [
        ("01", "Tell us about your AI", "Provide system ownership, purpose, industry and model details."),
        ("02", "Answer guided questions", "Describe data, access, deployment and human oversight."),
        ("03", "Explore your dashboard", "Filter risks, inspect controls and view source fields."),
        ("04", "Review and export", "Edit findings, record decisions and preview the report."),
    ]
    for col, (num, title, desc) in zip(st.columns(4), steps):
        with col:
            st.markdown(f'<div class="step-card"><span class="step-num">{num}</span><div class="step-title">{title}</div><div class="step-desc">{desc}</div></div>', unsafe_allow_html=True)
    st.write("")
    a, b, c = st.columns([1, 1, 1.4])
    with a:
        if st.button("🚀 Start Assessment", type="primary", use_container_width=True):
            go("Guided Intake")
    with b:
        if st.button("🧪 Try Demo Scenario", use_container_width=True):
            seed_demo()
    with c:
        st.caption("Demo pre-fills a fictional retail chatbot. You can edit it before assessing.")
    st.markdown('<div class="info-strip"><b>Prototype notice:</b> Built for student demonstration. Bundled results and citations are illustrative, not verified RAG retrieval or a professional audit.</div>', unsafe_allow_html=True)
    with st.expander("Who is this tool for?"):
        st.write("AI system owners and human reviewers who want structured intake, mapped control references and a draft risk review workflow.")

# ---------- 02 / Intake ----------
elif page == "Guided Intake":
    st.title("Guided AI System Intake")
    st.caption("Three steps: system details → security questions → confirm and assess.")
    step = st.session_state.current_step
    st.progress(step / 3, text=f"Step {step} of 3")
    draft = st.session_state.draft

    if step == 1:
        st.subheader("1 · Tell us about your AI system")
        with st.form("system_details"):
            name = st.text_input("AI system name *", value=draft.get("system_name", ""), placeholder="Customer Support Chatbot")
            owner = st.text_input("Owner / department *", value=draft.get("owner", ""), placeholder="Customer Service")
            purpose = st.text_area("What does this system do? *", value=draft.get("purpose", ""), placeholder="It answers customer questions using an LLM...")
            c1, c2 = st.columns(2)
            with c1:
                industries = ["Retail", "Finance", "Healthcare", "Education", "Government", "Other"]
                industry = st.selectbox("Industry", industries, index=choose(industries, draft.get("industry", "Retail")))
            with c2:
                models = ["Generative AI / LLM", "Predictive ML", "Computer Vision", "Recommendation", "Other", "Not sure"]
                model_type = st.selectbox("AI model type", models, index=choose(models, draft.get("model_type", "Not sure")))
            next_btn = st.form_submit_button("Next →", type="primary")
            if next_btn:
                if not all(x.strip() for x in [name, owner, purpose]):
                    st.error("Complete all mandatory fields marked with *.")
                else:
                    draft.update(system_name=name.strip(), owner=owner.strip(), purpose=purpose.strip(),
                                 industry=industry, model_type=model_type)
                    st.session_state.step2_cache = {}
                    st.session_state.current_step = 2
                    st.rerun()

    elif step == 2:
        st.subheader("2 · Security and governance questions")
        st.caption("Questions update immediately so relevant follow-ups can appear.")
        # Controls here are intentionally outside a form: conditional inputs need immediate reruns.
        cache = st.session_state.step2_cache
        def pick(label, field, options, help_text=None):
            if field not in cache:
                cache[field] = draft.get(field, options[0])
            val = st.selectbox(label, options, index=choose(options, cache[field]),
                               key=f"intake_{field}", help=help_text)
            cache[field] = val
            return val

        c1, c2 = st.columns(2)
        with c1:
            personal_data = pick("Does the system process personal data?", "personal_data", YES_NO)
            public_access = pick("Can customers or the public use it?", "public_access", YES_NO)
            human_oversight = pick("Are important outputs reviewed by a human?", "human_oversight", YES_NO)
            sensitive_decisions = pick("Does it affect high-impact decisions?", "sensitive_decisions", YES_NO,
                "Examples: recruitment, lending, eligibility or medical decisions.")
            third_party_api = pick("Does it use a third-party model or API?", "third_party_api", YES_NO)
        with c2:
            data_sensitivity = pick("Data sensitivity", "data_sensitivity",
                ["Not sure", "Public", "Internal", "Confidential", "Highly sensitive"])
            authentication = pick("Is user authentication implemented?", "authentication", YES_NO)
            deployment = pick("Deployment", "deployment", ["Not sure", "Cloud", "On-premises", "Hybrid"])
            data_storage = pick("Data storage", "data_storage",
                ["Not sure", "No data stored", "Cloud database", "On-premises database", "Mixed"])
        if personal_data in ("Yes", "Not sure"):
            st.markdown("#### Additional privacy questions")
            p1, p2 = st.columns(2)
            with p1:
                pick("Are privacy safeguards documented?", "privacy_controls", YES_NO)
            with p2:
                pick("Is there a data retention policy?", "retention_policy", YES_NO)
        else:
            cache["privacy_controls"] = "Not applicable"
            cache["retention_policy"] = "Not applicable"
        st.divider()
        back_col, next_col = st.columns(2)
        if back_col.button("← Back", use_container_width=True):
            draft.update(cache)
            st.session_state.current_step = 1
            st.rerun()
        if next_col.button("Next →", type="primary", use_container_width=True):
            draft.update(cache)
            st.session_state.current_step = 3
            st.rerun()

    else:
        st.subheader("3 · Confirm and assess")
        st.write("Please review your answers before running an assessment.")
        with st.expander("Review submitted profile", expanded=True):
            st.json(draft)
        st.warning("This project includes a DEMO assessment adapter. Its findings are not real agent/RAG results.")
        c1, c2 = st.columns(2)
        if c1.button("← Back", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
        if c2.button("Run Assessment →", type="primary", use_container_width=True):
            start_assessment(draft.copy())

# ---------- 03 / Dashboard ----------
elif page == "Dashboard":
    st.title("Risk Assessment Dashboard")
    st.caption("Findings, severity, control mapping and investigation details")
    ident, record = selected_record("dashboard")
    if record:
        findings = record.get("findings", [])
        n_critical = sum(f.get("severity") in ("Critical", "High") for f in findings)
        needs_review = sum(f.get("review_status") in ("Pending", "Needs Revision") for f in findings)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Assessments", len(st.session_state.assessments))
        m2.metric("Findings", len(findings))
        m3.metric("High / Critical", n_critical)
        m4.metric("Needs Review", needs_review)
        st.caption(f"Mode: {record.get('run_mode', 'Unknown')} · Created: {record.get('created_at', '')}")
        if is_demo(record):
            st.warning("Demo findings and citations are illustrative. No RAG references have been verified.")
        if not findings:
            st.info("The assessment returned no findings. Try another scenario or check your backend.")
        else:
            left, right = st.columns([1, 1.4])
            with left:
                st.subheader("Risk severity")
                counts = pd.Series([f.get("severity", "Unknown") for f in findings]).value_counts()
                ordered = SEVERITIES + (["Unknown"] if "Unknown" in counts else [])
                chart_df = pd.DataFrame({"Severity": ordered, "Count": [int(counts.get(s, 0)) for s in ordered]})
                fig = px.bar(chart_df, x="Severity", y="Count", color="Severity",
                             color_discrete_map=SEVERITY_COLORS)
                fig.update_layout(template="plotly_dark", paper_bgcolor="#102d49", plot_bgcolor="#102d49",
                                  showlegend=False, height=320, margin=dict(l=20,r=20,t=20,b=20))
                st.plotly_chart(fig, use_container_width=True)
            with right:
                st.subheader("Filter findings")
                a, b, c = st.columns(3)
                severity_filter = a.multiselect("Severity", SEVERITIES)
                categories = sorted({str(f.get("category", "Unknown")) for f in findings})
                category_filter = b.multiselect("Risk category", categories)
                review_filter = c.multiselect("Review", REVIEW_STATUSES)
                filtered = [f for f in findings
                            if (not severity_filter or f.get("severity") in severity_filter)
                            and (not category_filter or f.get("category") in category_filter)
                            and (not review_filter or f.get("review_status") in review_filter)]
                st.dataframe(summary_table(filtered), hide_index=True, use_container_width=True)
            st.subheader("Finding details")
            if not filtered:
                st.info("No findings match the filters.")
            else:
                choice = st.selectbox("Select a finding to inspect", range(len(filtered)),
                    format_func=lambda i: f"{filtered[i].get('id')} · {filtered[i].get('risk')} ({filtered[i].get('severity')})")
                f = filtered[choice]
                st.markdown(f"### {safe(f.get('risk'))}")
                p1, p2, p3 = st.columns(3)
                p1.write(f"**Severity:** {f.get('severity')}")
                p2.write(f"**Category:** {f.get('category')}")
                p3.write(f"**Control status:** {f.get('control_status')}")
                st.write("**Description:**", f.get("description"))
                st.write("**Recommended control:**", f.get("recommendation"))
                with st.expander("Framework and citation evidence", expanded=True):
                    source_box(f)
                if st.button("Review this finding →", type="primary"):
                    st.session_state.review_target = f.get("id")
                    go("Human Review")

# ---------- 04 / Human Review ----------
elif page == "Human Review":
    st.title("Human Review")
    st.caption("Human reviewers can approve, reject or request revision before finalisation.")
    ident, record = selected_record("review")
    if record:
        findings = record.get("findings", [])
        if not findings:
            st.info("There are no findings to review.")
        else:
            target = st.session_state.get("review_target")
            idx = next((i for i,f in enumerate(findings) if f.get("id") == target), 0)
            chosen_idx = st.selectbox("Select finding", range(len(findings)), index=idx,
                format_func=lambda i: f"{findings[i].get('id')} · {findings[i].get('risk')}")
            item = findings[chosen_idx]
            st.session_state.review_target = item.get("id")
            st.write("**Severity:**", item.get("severity"))
            st.write("**Risk description:**", item.get("description"))
            a, b = st.columns(2)
            with a:
                st.markdown("#### Original AI recommendation")
                st.info(item.get("original_recommendation", "Not available"))
            with b:
                st.markdown("#### Current reviewed recommendation")
                st.info(item.get("recommendation", "Not available"))
            with st.expander("Control mapping and citation"):
                source_box(item)
            with st.form(f"review_form_{ident}_{chosen_idx}"):
                reviewer = st.text_input("Reviewer name *", value=item.get("reviewer", ""))
                revised = st.text_area("Edit recommended control *", value=item.get("recommendation", ""), height=115)
                decision = st.selectbox("Review decision", REVIEW_STATUSES,
                    index=choose(REVIEW_STATUSES, item.get("review_status", "Pending")))
                notes = st.text_area("Decision reason / reviewer notes",
                    value=item.get("review_notes", ""),
                    help="Required for Rejected or Needs Revision decisions.")
                if st.form_submit_button("Save Review", type="primary"):
                    if not reviewer.strip() or not revised.strip():
                        st.error("Reviewer name and recommendation are required.")
                    elif decision in ("Rejected", "Needs Revision") and not notes.strip():
                        st.error("Explain why this finding was rejected or needs revision.")
                    else:
                        stamp = date_now()
                        item.update(reviewer=reviewer.strip(), recommendation=revised.strip(),
                                    review_status=decision, review_notes=notes.strip(), review_date=stamp)
                        item.setdefault("review_history", []).append({
                            "reviewer": reviewer.strip(), "status": decision,
                            "date": stamp, "notes": notes.strip(), "recommendation": revised.strip(),
                        })
                        record["assessment_status"] = "Draft"
                        st.success("Review saved for this session.")
            with st.expander(f"Review history ({len(item.get('review_history', []))})"):
                if item.get("review_history"):
                    st.dataframe(pd.DataFrame(item["review_history"]), hide_index=True, use_container_width=True)
                else:
                    st.caption("No decisions recorded yet.")
            remaining = sum(f.get("review_status") in ("Pending", "Needs Revision") for f in findings)
            st.caption(f"Remaining pending / revision: {remaining}")

# ---------- 05 / Reports ----------
elif page == "Reports":
    st.title("Reports & Export")
    st.caption("Executive summary · Risk register · Control gaps · Remediation roadmap · Review status")
    ident, record = selected_record("reports")
    if record:
        findings = record.get("findings", [])
        unresolved = sum(f.get("review_status") in ("Pending", "Needs Revision") for f in findings)
        reviewed = len(findings) - unresolved
        c1, c2, c3 = st.columns(3)
        c1.metric("Total findings", len(findings))
        c2.metric("Reviewed", reviewed)
        c3.metric("Pending / revision", unresolved)
        ready = ready_for_final(record)
        if is_demo(record):
            st.warning("DEMO report: findings and citations are not RAG-verified. Final certification is disabled.")
        elif unresolved:
            st.warning("Complete the Human Review decisions before marking this report as final.")
        elif not record.get("source_verified"):
            st.warning("The backend has not confirmed verified source citations; draft only.")
        if ready:
            if st.button("Mark report as final", type="primary"):
                record["assessment_status"] = "Final"
                record["finalized_at"] = date_now()
                st.success("Report marked final based on backend verification and completed review.")
        st.divider()
        profile = record.get("profile", {})
        st.subheader("1. Executive Summary")
        st.write("**System:**", profile.get("system_name"))
        st.write("**Owner:**", profile.get("owner"))
        st.write("**Purpose:**", profile.get("purpose"))
        st.write(record.get("summary", "This assessment requires human validation."))
        st.subheader("2. Risk Register")
        if findings:
            st.dataframe(summary_table(findings), hide_index=True, use_container_width=True)
        else:
            st.info("No risk findings were returned.")
        st.subheader("3. Control Gap Analysis")
        if findings:
            for f in findings:
                with st.expander(f"{f.get('id')} · {f.get('risk')} — {f.get('control_status')}"):
                    st.write("**Control status:**", f.get("control_status"))
                    st.write("**Recommendation:**", f.get("recommendation"))
                    source_box(f)
        else:
            st.caption("No gaps are available to display.")
        st.subheader("4. Draft Remediation Roadmap")
        st.caption("Sorted by severity. Timelines and ownership need human validation.")
        roadmap = sorted([f for f in findings if f.get("review_status") != "Rejected"],
                         key=lambda f: SEVERITIES.index(f.get("severity")) if f.get("severity") in SEVERITIES else 9)
        if roadmap:
            for i, f in enumerate(roadmap, 1):
                st.write(f"**{i}. [{f.get('severity')}] {f.get('risk')}** — {f.get('recommendation')}")
        else:
            st.caption("No remediation items in the current report.")
        st.subheader("5. Human Review Status")
        if findings:
            rev_df = pd.DataFrame([{
                "Finding": f.get("id"), "Decision": f.get("review_status"),
                "Reviewer": f.get("reviewer", ""), "Date": f.get("review_date", ""),
            } for f in findings])
            st.dataframe(rev_df, hide_index=True, use_container_width=True)
        st.subheader("6. Download")
        is_final = ready and record.get("assessment_status") == "Final"
        filename = ident.lower()
        jcol, hcol = st.columns(2)
        with jcol:
            st.download_button("Download JSON", data=json.dumps(record, indent=2, ensure_ascii=False),
                file_name=f"{filename}_{'final' if is_final else 'draft'}.json", mime="application/json",
                use_container_width=True)
        with hcol:
            st.download_button("Download HTML Report", data=html_report(record, final=is_final),
                file_name=f"{filename}_{'final' if is_final else 'draft'}.html", mime="text/html",
                use_container_width=True)
        st.caption("Open the HTML file in a browser to print/save as PDF. Automated PDF export can be added by the Documentation Agent later.")
        with st.expander("Raw assessment JSON"):
            st.json(record)
        st.info("Limitations: The copilot assists human assurance work; it does not replace a qualified auditor.")
