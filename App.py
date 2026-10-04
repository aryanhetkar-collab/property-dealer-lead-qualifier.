import os
import json
import urllib.request
import urllib.parse
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
    
    # Cold triggers (Short stays, cheap, rental rooms, hostels, PG, low budget)
    cold_keywords = ["rent", "pg", "hostel", "cheap", "2 days", "daily", "500", "short term", "room on rent", "1 day", "flatmate"]
    
    # Hot triggers (High purchase/investment intent, specific buying budget, site visit)
    hot_keywords = ["buy", "purchase", "invest", "crore", "lakhs", "pre-approved", "loan", "site visit", "ready buyer", "booking", "3bhk", "2bhk"]

    # 1. Cold Check (If rental/short-stay keywords are present and NO purchase keywords exist)
    if any(kw in text_lower for kw in cold_keywords) and not any(kw in text_lower for kw in ["buy", "purchase", "invest", "crore"]):
        return {
            "score": 20,
            "category": "Cold",
            "reasons": [
                "Rental or short-term stay request detected",
                "Unsuited for high-value property sales pipeline"
            ],
            "action": "Politely decline or redirect to rental/PG platforms.",
            "draft": "Hello! Thank you for reaching out. We specialize in property sales and long-term purchases. For short-term room rentals or PGs, we recommend checking dedicated rental apps!"
        }
    
    # 2. Hot Check (If explicit buying/investment intent is present)
    elif any(kw in text_lower for kw in hot_keywords):
        return {
            "score": 90,
            "category": "Hot",
            "reasons": [
                "High purchase/investment intent detected",
                "Buying budget or site visit request present"
            ],
            "action": "Schedule immediate phone call & book site visit within 2 hours.",
            "draft": "Hello! Thank you for reaching out. I'd be delighted to assist you with your property purchase and schedule a site visit this weekend. When is a good time to connect?"
        }
    
    # 3. Warm Check (General inquiries, missing specific buying/rental commitment)
    else:
        return {
            "score": 55,
            "category": "Warm",
            "reasons": [
                "General property inquiry detected",
                "Requires further clarification on budget and purchase timeline"
            ],
            "action": "Send digital property catalog on WhatsApp and follow up in 24 hours.",
            "draft": "Hello! Thanks for reaching out. I've noted your inquiry. Could you share your preferred location and target budget so I can send tailored listings?"
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
                draft_msg = st.text_area("Ready to send:", value=lead["draft"], height=100, key=f"draft_{idx}")
                
                # Format phone number for WhatsApp URL (clean non-digits)
                raw_phone = lead["phone"].replace("+", "").replace(" ", "").replace("-", "")
                if not raw_phone.isdigit():
                    raw_phone = "919876543210" # Default fallback number for demo
                
                encoded_msg = urllib.parse.quote(draft_msg)
                whatsapp_url = f"https://wa.me/{raw_phone}?text={encoded_msg}"
                
                st.link_button(f"📲 Send Auto-Reply to {lead['name']} via WhatsApp", whatsapp_url)
