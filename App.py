import os
import json
import urllib.request
import urllib.parse
import urllib.error
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Helpreneur AI - Pune Real Estate Portal & Broker CRM",
    page_icon="🏙️",
    layout="wide"
)

# ------------------------------------------------------------------------------
# 1. Pune Real Estate Inventory Database
# ------------------------------------------------------------------------------
PUNE_INVENTORY = [
    {
        "id": "PUNE-BNR-101",
        "title": "VTP Earth One - Luxury 3BHK",
        "location": "Baner",
        "bhk": "3BHK",
        "price_lakhs": 95,
        "possession": "Ready to Move",
        "image": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=500&q=80"
    },
    {
        "id": "PUNE-WKD-102",
        "title": "Kolte Patil Life Republic - Smart 2BHK",
        "location": "Wakad",
        "bhk": "2BHK",
        "price_lakhs": 62,
        "possession": "Under Construction (Dec 2025)",
        "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=500&q=80"
    },
    {
        "id": "PUNE-KHD-103",
        "title": "Gera World of Joy - Premium 3BHK",
        "location": "Kharadi",
        "bhk": "3BHK",
        "price_lakhs": 110,
        "possession": "Ready to Move",
        "image": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=500&q=80"
    },
    {
        "id": "PUNE-HNJ-104",
        "title": "Godrej Elements - Affordable 1BHK",
        "location": "Hinjewadi",
        "bhk": "1BHK",
        "price_lakhs": 42,
        "possession": "Ready to Move",
        "image": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=500&q=80"
    },
    {
        "id": "PUNE-KTR-105",
        "title": "Sobha Nesara - Horizon 4BHK Villa/Apartment",
        "location": "Kothrud",
        "bhk": "4BHK",
        "price_lakhs": 220,
        "possession": "Under Construction",
        "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=500&q=80"
    },
    {
        "id": "PUNE-VMN-106",
        "title": "Lunkad Sky Vie - Executive 2BHK",
        "location": "Viman Nagar",
        "bhk": "2BHK",
        "price_lakhs": 88,
        "possession": "Ready to Move",
        "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500&q=80"
    }
]

# Initialize Session State Database
if "lead_db" not in st.session_state:
    st.session_state["lead_db"] = [
        {
            "id": "LEAD-101",
            "name": "Vikram Malhotra",
            "phone": "+91 98765 43210",
            "flat_applied": "VTP Earth One - Luxury 3BHK (Baner)",
            "budget": "₹95 Lakhs",
            "location": "Baner",
            "source": "Website Portal",
            "score": 95,
            "category": "Hot",
            "intent": "High Intent Purchase - Direct Flat Application",
            "reasons": ["Applied for specific listed flat", "Pre-approved loan ready"],
            "action": "Schedule site visit for Baner flat within 24 hrs.",
            "draft": "Hello Vikram! Thank you for applying for VTP Earth One 3BHK in Baner. We have your ₹95L budget profile logged. When can we arrange your private site visit?",
            "status": "Pending",
            "best_time": "Evening (5:00 PM - 7:00 PM)",
            "best_channel": "WhatsApp"
        }
    ]

# ------------------------------------------------------------------------------
# 2. Logic Engine
# ------------------------------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

def evaluate_lead_locally(flat_title: str, budget: int, user_msg: str, loan_status: str) -> dict:
    text_lower = user_msg.lower()
    
    if budget >= 60 or loan_status == "Pre-Approved" or "ready" in text_lower or "visit" in text_lower:
        return {
            "score": 90,
            "category": "Hot",
            "intent": f"Direct Flat Interest: {flat_title}",
            "reasons": [f"Target budget ₹{budget} Lakhs matches listing", f"Loan Status: {loan_status}"],
            "action": "Immediate phone call and site visit booking.",
            "draft": f"Hello! Thanks for applying for {flat_title}. I have noted your target budget of ₹{budget} Lakhs. Let's schedule a site visit this weekend!",
            "best_time": "Evening (5:00 PM - 7:00 PM)",
            "best_channel": "WhatsApp"
        }
    elif budget >= 35:
        return {
            "score": 60,
            "category": "Warm",
            "intent": f"General Flat Application: {flat_title}",
            "reasons": ["Valid budget parameter", "Follow-up required for timeline"],
            "action": "Send floor plans and brochure on WhatsApp.",
            "draft": f"Hello! Thanks for your interest in {flat_title}. I've attached the detailed floor plan and brochure. Let me know if you have any questions!",
            "best_time": "Afternoon (2:00 PM - 4:00 PM)",
            "best_channel": "WhatsApp"
        }
    else:
        return {
            "score": 25,
            "category": "Cold",
            "intent": "Budget Below Available Inventory",
            "reasons": ["Budget lower than property baseline"],
            "action": "Redirect to budget rental/PG options.",
            "draft": "Hello! Thank you for reaching out. Our current property listings start from ₹40 Lakhs. Let us know if you would like options in alternative locations!",
            "best_time": "Morning (10:00 AM - 12:00 PM)",
            "best_channel": "Email"
        }

def analyze_lead(flat_title: str, budget: int, user_msg: str, loan_status: str) -> dict:
    if not api_key:
        return evaluate_lead_locally(flat_title, budget, user_msg, loan_status)

    prompt = f"""
    Analyze this real estate lead application for property '{flat_title}' in Pune:
    - Budget: ₹{budget} Lakhs
    - Loan Status: {loan_status}
    - Client Message: "{user_msg}"

    Respond STRICTLY in JSON format:
    {{
        "score": <0-100 integer>,
        "category": "<Hot|Warm|Cold>",
        "intent": "<short extracted intent>",
        "reasons": ["<reason1>", "<reason2>"],
        "action": "<recommended next action>",
        "draft": "<whatsapp draft response>",
        "best_time": "<predicted best time>",
        "best_channel": "<WhatsApp|Phone Call|Email>"
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
        return evaluate_lead_locally(flat_title, budget, user_msg, loan_status)

# ------------------------------------------------------------------------------
# 3. Main Navigation
# ------------------------------------------------------------------------------
st.title("🏙️ Helpreneur AI — Pune Property Portal & Lead CRM")

tab1, tab2, tab3 = st.tabs([
    "🏡 1. Browse Pune Flats & Apply", 
    "📊 2. Broker CRM Pipeline", 
    "📦 3. Property Inventory DB"
])

# ------------------------------------------------------------------------------
# TAB 1: Pune Flat Finder & Application
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Find Your Flat in Pune & Apply Directly")
    
    # Filter Controls (Area Selection + Budget Slider)
    col_a, col_b, col_c = st.columns([1, 1, 1])
    
    with col_a:
        selected_area = st.multiselect(
            "📍 Select Flat Area in Pune:",
            ["Baner", "Wakad", "Kharadi", "Hinjewadi", "Kothrud", "Viman Nagar"],
            default=["Baner", "Wakad", "Kharadi", "Hinjewadi", "Kothrud", "Viman Nagar"]
        )
    with col_b:
        selected_bhk = st.multiselect(
            "🛏️ Property Configuration:",
            ["1BHK", "2BHK", "3BHK", "4BHK"],
            default=["1BHK", "2BHK", "3BHK", "4BHK"]
        )
    with col_c:
        max_budget = st.slider("💰 Set Max Budget (in ₹ Lakhs):", min_value=30, max_value=250, value=150, step=5)

    st.markdown("---")
    
    # Filter inventory based on controls
    filtered_flats = [
        f for f in PUNE_INVENTORY 
        if f["location"] in selected_area 
        and f["bhk"] in selected_bhk 
        and f["price_lakhs"] <= max_budget
    ]
    
    st.markdown(f"### Available Listings ({len(filtered_flats)} flats match your filter)")
    
    if not filtered_flats:
        st.warning("No flats match your exact budget and location criteria. Try increasing the budget slider!")
    else:
        for flat in filtered_flats:
            with st.container():
                fc1, fc2, fc3 = st.columns([1, 2, 1])
                
                with fc1:
                    st.image(flat["image"], use_column_width=True)
                with fc2:
                    st.markdown(f"### {flat['title']}")
                    st.markdown(f"📍 **Location:** {flat['location']} | 🛏️ **Type:** {flat['bhk']}")
                    st.markdown(f"💰 **Price:** **₹{flat['price_lakhs']} Lakhs** | 🔑 **Status:** {flat['possession']}")
                with fc3:
                    st.write("")
                    st.write("")
                    if st.button(f"📝 Apply for Flat", key=f"apply_{flat['id']}"):
                        st.session_state["selected_flat"] = flat

    # Modal Application Form when a flat is selected
    if "selected_flat" in st.session_state and st.session_state["selected_flat"]:
        s_flat = st.session_state["selected_flat"]
        st.markdown("---")
        st.success(f"📋 **Submit Interested Lead Form for: {s_flat['title']} ({s_flat['location']})**")
        
        with st.form("application_form"):
            ac1, ac2 = st.columns(2)
            with ac1:
                applicant_name = st.text_input("Full Name", placeholder="e.g. Rahul Deshmukh")
                applicant_phone = st.text_input("WhatsApp / Phone Number", placeholder="+91 9876543210")
                user_budget = st.number_input("Your Specific Budget (in ₹ Lakhs)", value=s_flat["price_lakhs"])
            with ac2:
                loan_req = st.selectbox("Home Loan Requirement", ["Loan Required & Ready", "Pre-Approved Loan", "Self-Funded / Cash", "Loan Required"])
                client_msg = st.text_area("Additional Requirements or Site Visit Request", placeholder="e.g. Want to schedule site visit this Sunday...")
            
            submit_app = st.form_submit_button("🚀 Submit Application to Broker")
            
            if submit_app:
                if applicant_name and applicant_phone:
                    res = analyze_lead(s_flat["title"], user_budget, client_msg, loan_req)
                    
                    new_lead = {
                        "id": f"LEAD-{101 + len(st.session_state['lead_db'])}",
                        "name": applicant_name,
                        "phone": applicant_phone,
                        "flat_applied": f"{s_flat['title']} ({s_flat['location']})",
                        "budget": f"₹{user_budget} Lakhs",
                        "location": s_flat["location"],
                        "source": "Website Portal",
                        "score": res.get("score", 85),
                        "category": res.get("category", "Hot"),
                        "intent": res.get("intent", f"Interest in {s_flat['title']}"),
                        "reasons": res.get("reasons", []),
                        "action": res.get("action", "Schedule site visit"),
                        "draft": res.get("draft", "Thank you for applying."),
                        "status": "Pending",
                        "best_time": res.get("best_time", "Evening (5-7 PM)"),
                        "best_channel": res.get("best_channel", "WhatsApp")
                    }
                    st.session_state["lead_db"].insert(0, new_lead)
                    st.session_state["selected_flat"] = None
                    st.balloons()
                    st.success("✅ Application Submitted! Our Pune broker will contact you on WhatsApp shortly.")
                else:
                    st.error("Please enter your name and phone number.")

# ------------------------------------------------------------------------------
# TAB 2: Broker CRM Dashboard
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("👔 Broker Portal: Live Pune Lead Applications")
    
    total_leads = len(st.session_state["lead_db"])
    hot_leads = sum(1 for item in st.session_state["lead_db"] if item["category"] == "Hot")
    warm_leads = sum(1 for item in st.session_state["lead_db"] if item["category"] == "Warm")
    cold_leads = sum(1 for item in st.session_state["lead_db"] if item["category"] == "Cold")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Applications", total_leads)
    m2.metric("🔥 Hot Leads", hot_leads)
    m3.metric("🌤️ Warm Leads", warm_leads)
    m4.metric("❄️ Cold Leads", cold_leads)
    
    st.markdown("---")
    
    for idx, lead in enumerate(st.session_state["lead_db"]):
        cat = lead["category"]
        badge = "🔴 HOT" if cat == "Hot" else ("🟡 WARM" if cat == "Warm" else "⚪ COLD")
        
        with st.expander(f"{badge} [{lead['score']}/100] {lead['name']} | Flat: {lead.get('flat_applied', 'General Inquiry')} | Status: {lead['status']}", expanded=(idx==0)):
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"**Applied Flat:** `{lead.get('flat_applied', 'N/A')}`")
                st.markdown(f"**Client Budget:** `{lead.get('budget', 'N/A')}` | **Location:** `{lead.get('location', 'Pune')}`")
                st.markdown(f"**Extracted AI Intent:** {lead['intent']}")
                st.markdown(f"**AI Qualification Score:** `{lead['score']}/100`")
                st.markdown(f"**Recommended Action:** {lead['action']}")
                
                st.info(f"💡 **Predictive Best Follow-Up Window:**\n- **Time:** {lead['best_time']}\n- **Channel:** {lead['best_channel']}")
            
            with c2:
                st.markdown("**Auto-Generated WhatsApp Reply:**")
                draft_msg = st.text_area("Ready to send:", value=lead["draft"], height=100, key=f"draft_{lead['id']}")
                
                # Status tracking
                lead["status"] = st.selectbox("Update Status:", ["Pending", "Followed Up", "Converted", "Closed"], index=["Pending", "Followed Up", "Converted", "Closed"].index(lead["status"]), key=f"st_{lead['id']}")
                
                raw_phone = lead["phone"].replace("+", "").replace(" ", "").replace("-", "")
                if not raw_phone.isdigit():
                    raw_phone = "919876543210"
                encoded_msg = urllib.parse.quote(draft_msg)
                whatsapp_url = f"https://wa.me/{raw_phone}?text={encoded_msg}"
                
                st.link_button(f"📲 Contact {lead['name']} on WhatsApp", whatsapp_url)

# ------------------------------------------------------------------------------
# TAB 3: Property Inventory Database
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("📦 Broker Property Inventory Database (Pune)")
    st.dataframe(PUNE_INVENTORY, use_container_width=True)
