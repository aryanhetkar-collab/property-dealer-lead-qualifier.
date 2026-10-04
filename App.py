import os
import json
import urllib.request
import urllib.parse
import urllib.error
import streamlit as st

# ------------------------------------------------------------------------------
# Page Setup & Styling
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Pune Real Estate AI Portal",
    page_icon="🏙️",
    layout="wide"
)

# Custom CSS for polished UI
st.markdown("""
<style>
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    .flat-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        background-color: #ffffff;
    }
    .badge {
        background-color: #eef2ff;
        color: #4f46e5;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Data Layer (Simulated Backend Database)
# ------------------------------------------------------------------------------
PUNE_DATABASE = [
    {
        "id": "PUNE-BNR-101",
        "title": "VTP Earth One",
        "developer": "VTP Realty",
        "location": "Baner",
        "bhk": "3BHK",
        "price_lakhs": 95,
        "carpet_area": "1050 sq.ft.",
        "possession": "Ready to Move",
        "amenities": ["Swimming Pool", "Clubhouse", "Gym", "EV Charging"],
        "image": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=500&q=80"
    },
    {
        "id": "PUNE-BNR-102",
        "title": "Kasturi Apostrophe",
        "developer": "Kasturi Housing",
        "location": "Baner",
        "bhk": "2BHK",
        "price_lakhs": 78,
        "carpet_area": "820 sq.ft.",
        "possession": "Dec 2025",
        "amenities": ["Rooftop Park", "Squash Court", "Smart Home"],
        "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=500&q=80"
    },
    {
        "id": "PUNE-WKD-103",
        "title": "Kolte Patil Life Republic",
        "developer": "Kolte Patil",
        "location": "Wakad",
        "bhk": "2BHK",
        "price_lakhs": 62,
        "carpet_area": "740 sq.ft.",
        "possession": "Ready to Move",
        "amenities": ["Township Amenities", "School", "Shopping Plaza"],
        "image": "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=500&q=80"
    },
    {
        "id": "PUNE-WKD-104",
        "title": "Mahindra Happinest",
        "developer": "Mahindra Lifespaces",
        "location": "Wakad",
        "bhk": "1BHK",
        "price_lakhs": 42,
        "carpet_area": "480 sq.ft.",
        "possession": "Ready to Move",
        "amenities": ["Solar Power", "Jogging Track", "24x7 Security"],
        "image": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=500&q=80"
    },
    {
        "id": "PUNE-KHD-105",
        "title": "Gera World of Joy",
        "developer": "Gera Developments",
        "location": "Kharadi",
        "bhk": "3BHK",
        "price_lakhs": 115,
        "carpet_area": "1120 sq.ft.",
        "possession": "June 2026",
        "amenities": ["Child Centric Homes", "Badminton Court", "Creche"],
        "image": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=500&q=80"
    },
    {
        "id": "PUNE-KHD-106",
        "title": "Panchshil Towers",
        "developer": "Panchshil Realty",
        "location": "Kharadi",
        "bhk": "4BHK",
        "price_lakhs": 240,
        "carpet_area": "2200 sq.ft.",
        "possession": "Ready to Move",
        "amenities": ["Private Elevator", "Infinity Pool", "Concierge"],
        "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=500&q=80"
    },
    {
        "id": "PUNE-HNJ-107",
        "title": "Godrej Elements",
        "developer": "Godrej Properties",
        "location": "Hinjewadi",
        "bhk": "2BHK",
        "price_lakhs": 68,
        "carpet_area": "780 sq.ft.",
        "possession": "Ready to Move",
        "amenities": ["Proximity to IT Park", "Gym", "Co-working Space"],
        "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500&q=80"
    },
    {
        "id": "PUNE-KTR-108",
        "title": "Sobha Nesara",
        "developer": "Sobha Limited",
        "location": "Kothrud",
        "bhk": "3BHK",
        "price_lakhs": 165,
        "carpet_area": "1350 sq.ft.",
        "possession": "Dec 2026",
        "amenities": ["Hill Views", "Clubhouse", "Tennis Court"],
        "image": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=500&q=80"
    }
]

# Initialize Session Persistence
if "inquiries_db" not in st.session_state:
    st.session_state["inquiries_db"] = [
        {
            "id": "INQ-2026-01",
            "name": "Aniket Shinde",
            "phone": "+91 98230 11223",
            "flat": "VTP Earth One (Baner)",
            "offered_budget": "₹95 Lakhs",
            "loan_status": "Pre-Approved",
            "visit_pref": "Looking to visit this Saturday morning around 11 AM.",
            "score": 92,
            "category": "Hot",
            "intent": "High Intent Buyer — Site Visit Requested",
            "suggested_reply": "Hello Aniket! Thank you for inquiring about VTP Earth One in Baner. We have scheduled your site visit for Saturday at 11 AM. Our relationship manager will meet you at the site.",
            "owner_status": "New Inquiry"
        }
    ]

# ------------------------------------------------------------------------------
# Backend Microservice: Gemini AI Inquiry Processor
# ------------------------------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

def process_inquiry_with_ai(flat_title: str, user_budget: int, loan_status: str, message: str) -> dict:
    if not api_key:
        # Local rule-based fallback microservice
        is_high = user_budget >= 60 or loan_status == "Pre-Approved"
        return {
            "score": 88 if is_high else 55,
            "category": "Hot" if is_high else "Warm",
            "intent": f"Site Visit Inquiry for {flat_title}",
            "suggested_reply": f"Hello! Thanks for your interest in {flat_title}. We received your inquiry with budget ₹{user_budget} Lakhs ({loan_status}). Our team will arrange a site tour shortly."
        }

    prompt = f"""
    Analyze this real estate inquiry for project '{flat_title}' in Pune:
    - User Offered Budget: ₹{user_budget} Lakhs
    - Loan Status: {loan_status}
    - Message: "{message}"

    Output JSON strictly in this structure:
    {{
        "score": <0-100 integer>,
        "category": "<Hot|Warm|Cold>",
        "intent": "<1-sentence intent summary>",
        "suggested_reply": "<professional owner response to user>"
    }}
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return json.loads(res["candidates"][0]["content"]["parts"][0]["text"])
    except Exception:
        return {
            "score": 80,
            "category": "Hot",
            "intent": "Inquiry submitted successfully",
            "suggested_reply": f"Hello! Thank you for inquiring about {flat_title}. We will contact you soon."
        }

# ------------------------------------------------------------------------------
# UI Layout
# ------------------------------------------------------------------------------
st.title("🏙️ Pune Real Estate Portal & Owner Dashboard")

tab_buyer, tab_owner = st.tabs([
    "🔍 Find Flats & Submit Inquiry", 
    "📬 Owner & Broker Inbox (Respond to Leads)"
])

# ------------------------------------------------------------------------------
# TAB 1: Buyer Search & Application Flow
# ------------------------------------------------------------------------------
with tab_buyer:
    st.subheader("Step 1: Set Your Requirements")
    
    with st.container():
        c1, c2, c3 = st.columns([1.5, 1.5, 1])
        
        all_locations = sorted(list(set(item["location"] for item in PUNE_DATABASE)))
        all_bhk = ["1BHK", "2BHK", "3BHK", "4BHK"]
        
        with c1:
            req_areas = st.multiselect("📍 Desired Area(s):", options=all_locations, default=["Baner", "Kharadi"])
        with c2:
            req_bhk = st.multiselect("🛏️ Configuration:", options=all_bhk, default=["2BHK", "3BHK"])
        with c3:
            max_budget = st.slider("💰 Max Budget (₹ Lakhs):", min_value=30, max_value=250, value=120, step=5)
            
        search_clicked = st.button("🔍 Search Available Flats", type="primary", use_container_width=True)

    if "has_searched" not in st.session_state:
        st.session_state["has_searched"] = False

    if search_clicked:
        st.session_state["has_searched"] = True

    st.markdown("---")

    # Step 2: Show flat inventory only after search action
    if st.session_state["has_searched"]:
        matched_flats = [
            f for f in PUNE_DATABASE
            if f["location"] in req_areas
            and f["bhk"] in req_bhk
            and f["price_lakhs"] <= max_budget
        ]
        
        st.subheader(f"Step 2: Available Options ({len(matched_flats)} found)")
        
        if not matched_flats:
            st.info("No properties match your current filters. Try increasing your max budget or adding more localities.")
        else:
            for flat in matched_flats:
                col_img, col_info, col_act = st.columns([1, 2, 1])
                
                with col_img:
                    st.image(flat["image"], use_column_width=True)
                with col_info:
                    st.markdown(f"### {flat['title']} `{flat['developer']}`")
                    st.markdown(f"📍 **{flat['location']}** | 🛏️ **{flat['bhk']}** ({flat['carpet_area']})")
                    st.markdown(f"💵 **Price: ₹{flat['price_lakhs']} Lakhs** | 🔑 **Status: {flat['possession']}**")
                    st.caption("✨ " + " • ".join(flat["amenities"]))
                with col_act:
                    st.write("")
                    st.write("")
                    if st.button(f"📝 Apply Now", key=f"btn_apply_{flat['id']}"):
                        st.session_state["active_flat"] = flat

        # Application Form Drawer
        if "active_flat" in st.session_state and st.session_state["active_flat"]:
            a_flat = st.session_state["active_flat"]
            st.markdown("---")
            st.success(f"📋 **Submit Official Inquiry for {a_flat['title']} ({a_flat['location']})**")
            
            with st.form("inquiry_form"):
                ic1, ic2 = st.columns(2)
                with ic1:
                    b_name = st.text_input("Full Name", placeholder="e.g. Ramesh Kulkarni")
                    b_phone = st.text_input("WhatsApp / Contact Number", placeholder="+91 98220 12345")
                    b_budget = st.number_input("Offered / Target Budget (₹ Lakhs)", value=a_flat["price_lakhs"])
                with ic2:
                    b_loan = st.selectbox("Funding / Loan Status", ["Pre-Approved Loan", "Loan Needed", "Self-Funded"])
                    b_msg = st.text_area("Site Visit Request & Notes", placeholder="e.g. Looking to visit this Sunday morning.")
                
                sub_btn = st.form_submit_button("🚀 Submit Inquiry to Owner/Broker")
                
                if sub_btn:
                    if b_name and b_phone:
                        ai_eval = process_inquiry_with_ai(a_flat["title"], b_budget, b_loan, b_msg)
                        
                        new_inquiry = {
                            "id": f"INQ-2026-{len(st.session_state['inquiries_db'])+1:02d}",
                            "name": b_name,
                            "phone": b_phone,
                            "flat": f"{a_flat['title']} ({a_flat['location']})",
                            "offered_budget": f"₹{b_budget} Lakhs",
                            "loan_status": b_loan,
                            "visit_pref": b_msg,
                            "score": ai_eval.get("score", 85),
                            "category": ai_eval.get("category", "Hot"),
                            "intent": ai_eval.get("intent", f"Inquiry for {a_flat['title']}"),
                            "suggested_reply": ai_eval.get("suggested_reply", "Thank you for reaching out."),
                            "owner_status": "New Inquiry"
                        }
                        
                        st.session_state["inquiries_db"].insert(0, new_inquiry)
                        st.session_state["active_flat"] = None
                        st.balloons()
                        st.success("✅ Inquiry submitted successfully! The property owner will review and respond in Tab 2.")
                    else:
                        st.error("Please fill in your Name and Phone Number.")
    else:
        st.info("👆 Please select your area and budget preferences above and click **Search Available Flats**.")

# ------------------------------------------------------------------------------
# TAB 2: Property Owner / Broker Response Inbox
# ------------------------------------------------------------------------------
with tab_owner:
    st.subheader("📬 Property Owner Response Center")
    st.caption("Review incoming buyer inquiries, edit AI-generated responses, and update deal statuses.")
    
    inquiries = st.session_state["inquiries_db"]
    
    if not inquiries:
        st.info("No incoming inquiries yet.")
    else:
        for idx, inq in enumerate(inquiries):
            badge_color = "🔴" if inq["category"] == "Hot" else ("🟡" if inq["category"] == "Warm" else "⚪")
            
            with st.expander(f"{badge_color} [{inq['score']}/100 Score] {inq['name']} — Interested in {inq['flat']} | Status: {inq['owner_status']}", expanded=(idx==0)):
                rc1, rc2 = st.columns([1, 1])
                
                with rc1:
                    st.markdown(f"**Buyer Contact:** {inq['name']} (`{inq['phone']}`)")
                    st.markdown(f"**Target Flat:** `{inq['flat']}`")
                    st.markdown(f"**Offered Budget:** `{inq['offered_budget']}` | **Loan Status:** `{inq['loan_status']}`")
                    st.markdown(f"**Buyer Notes:** _{inq['visit_pref'] or 'None provided'}_\n")
                    st.info(f"🧠 **AI Intent Tag:** {inq['intent']}")
                
                with rc2:
                    st.markdown("**Compose Response to Buyer:**")
                    reply_text = st.text_area("Response Message:", value=inq["suggested_reply"], height=100, key=f"reply_text_{inq['id']}")
                    
                    status_opts = ["New Inquiry", "Contacted / In Discussion", "Site Visit Scheduled", "Deal Closed"]
                    inq["owner_status"] = st.selectbox("Update Deal Status:", status_opts, index=status_opts.index(inq["owner_status"]), key=f"status_sel_{inq['id']}")
                    
                    # Direct WhatsApp link for owner response
                    clean_phone = inq["phone"].replace("+", "").replace(" ", "").replace("-", "")
                    encoded_msg = urllib.parse.quote(reply_text)
                    wa_link = f"https://wa.me/{clean_phone}?text={encoded_msg}"
                    
                    st.link_button(f"📲 Send Response to {inq['name']} via WhatsApp", wa_link)
