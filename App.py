import os
import json
import urllib.request
import urllib.error
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="PropLead AI - Real Estate Lead Qualifier CRM",
    page_icon="🏢",
    layout="wide"
)

# Initialize Session State Database for Leads
if "lead_db" not in st.session_state:
    st.session_state["lead_db"] = [
        {
            "name": "Rahul Sharma",
            "phone": "+91 98765 43210",
            "inquiry": "Hi, I am looking to buy a 3BHK flat in prime location. Budget is around ₹85 Lakhs with pre-approved bank loan ready. I want to schedule a site visit this Sunday.",
            "score": 90,
            "category": "Hot",
            "reasons": ["High purchase intent detected", "Specific budget & site visit requested"],
            "action": "Schedule immediate call & book site visit.",
            "draft": "Hello Rahul! Thank you for reaching out. I'd be delighted to assist with your 3BHK search and schedule a site visit this Sunday."
        },
        {
            "name": "Amit Kumar",
            "phone": "+91 91234 56789",
            "inquiry": "Hi, looking for a room on rent for 2 days under ₹500/night.",
            "score": 20,
            "category": "Cold",
            "reasons": ["Short-term rental request below threshold", "Unsuited for long-term brokerage"],
            "action": "Politely decline or redirect to short-stay apps.",
            "draft": "Hello Amit! We specialize in long-term property sales and leases. For daily room rentals, we recommend hotel booking apps."
        }
    ]

# ------------------------------------------------------------------------------
# API Key & Logic Engine
# ------------------------------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

def evaluate_lead_locally(text: str) -> dict:
    text_lower = text.lower()
    cold_keywords = ["2 days", "500", "cheap", "short term", "room on rent", "hostel", "pg", "rent"]
    hot_keywords = ["buy", "3bhk", "2bhk", "crore", "lakhs", "site visit", "pre-approved", "loan", "ready buyer"]

    if any(kw in text_lower for kw in cold_keywords) and not any(kw in text_lower for kw in ["buy", "crore", "lakhs"]):
        return {
            "score": 20,
            "category": "Cold",
            "reasons": ["Short-term rental/micro-budget inquiry", "Not suitable for brokerage pipeline"],
            "action": "Redirect to short-stay platforms.",
            "draft": "Hello! Thanks for reaching out. We focus on long-term sales and leases. For short daily stays, please try hotel booking apps!"
        }
    elif any(kw in text_lower for kw in hot_keywords):
        return {
            "score": 90,
            "category": "Hot",
            "reasons": ["High purchase intent", "Ready budget & loan pre-approved"],
            "action": "Call immediately and arrange site visit.",
            "draft": "Hello! Thanks for reaching out. I'd love to help you find your ideal property and arrange a site visit this weekend."
        }
    else:
        return {
            "score": 55,
            "category": "Warm",
            "reasons": ["General inquiry requiring budget/timeline clarification"],
            "action": "Send catalog on WhatsApp and follow up in 24 hrs.",
            "draft": "Hello! Thanks for reaching out. I've shared our property catalog. Let me know your preferred location to share tailored listings!"
        }

def analyze_lead(inquiry: str) -> dict:
    if not api_key:
        return evaluate_lead_locally(inquiry)

    prompt = f"""
    You are an expert real estate AI lead qualifier. Analyze this inquiry: "{inquiry}"
    Respond STRICTLY in JSON format:
    {{
        "score": <0-100>,
        "category": "<Hot|Warm|Cold>",
        "reasons": ["<reason1>", "<reason2>"],
        "action": "<action>",
        "draft": "<whatsapp response draft>"
    }}
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            return json.loads(res_json["candidates"][0]["content"]["parts"][0]["text"])
    except Exception:
        return evaluate_lead_locally(inquiry)

# ------------------------------------------------------------------------------
# App Navigation Tabs (2-Actor B2B Architecture)
# ------------------------------------------------------------------------------
st.title("🏢 PropLead AI - Real Estate Lead Qualification B2B Platform")

tab1, tab2 = st.tabs(["📝 Client Inquiry Portal (Public View)", "📊 Agent CRM Dashboard (Broker View)"])

# ------------------------------------------------------------------------------
# TAB 1: Client Facing Form
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Looking for your dream property? Drop an inquiry below:")
    
    with st.form("client_form", clear_on_submit=True):
        client_name = st.text_input("Your Full Name", placeholder="e.g. Vikram Malhotra")
        client_phone = st.text_input("Phone Number / WhatsApp", placeholder="+91 9876543210")
        client_inquiry = st.text_area("How can we help you?", placeholder="Describe budget, location, requirement (e.g. 3BHK to buy or room on rent)...", height=100)
        
        submitted = st.form_submit_button("🚀 Submit Inquiry to Broker")
        
        if submitted:
            if client_name and client_inquiry:
                analysis = analyze_lead(client_inquiry)
                new_lead = {
                    "name": client_name,
                    "phone": client_phone or "N/A",
                    "inquiry": client_inquiry,
                    "score": analysis.get("score", 50),
                    "category": analysis.get("category", "Warm"),
                    "reasons": analysis.get("reasons", []),
                    "action": analysis.get("action", "Follow up"),
                    "draft": analysis.get("draft", "Thank you for contacting us.")
                }
                st.session_state["lead_db"].insert(0, new_lead)
                st.success("✅ Your inquiry has been submitted! Our real estate advisor will get back to you shortly.")
            else:
                st.error("Please enter your name and inquiry message.")

# ------------------------------------------------------------------------------
# TAB 2: Broker CRM Dashboard
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("👔 Broker Portal: Live Incoming Leads Pipeline")
    
    # Metrics
    total_leads = len(st.session_state["lead_db"])
    hot_leads = sum(1 for item in st.session_state["lead_db"] if item["category"] == "Hot")
    cold_leads = sum(1 for item in st.session_state["lead_db"] if item["category"] == "Cold")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Inquiries", total_leads)
    m2.metric("🔥 Hot Leads (High Priority)", hot_leads)
    m3.metric("❄️ Cold Leads (Filtered Out)", cold_leads)
    
    st.markdown("---")
    
    for idx, lead in enumerate(st.session_state["lead_db"]):
        cat = lead["category"]
        color = "red" if cat == "Hot" else ("orange" if cat == "Warm" else "gray")
        
        with st.expander(f"[{cat.upper()} LEAD - {lead['score']}/100] {lead['name']} ({lead['phone']})", expanded=(idx==0)):
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"**Client Inquiry:** *\"{lead['inquiry']}\"*")
                st.markdown(f"**AI Score:** `{lead['score']}/100`")
                st.markdown(f"**Recommended Action:** {lead['action']}")
                st.markdown("**Key Reasons:**")
                for r in lead["reasons"]:
                    st.markdown(f"- {r}")
            with c2:
                st.markdown("**Automated WhatsApp Reply Draft:**")
                st.text_area("Ready to send:", value=lead["draft"], height=100, key=f"draft_{idx}")
                st.button(f"📲 Send Auto-Reply to {lead['name']}", key=f"btn_{idx}")
