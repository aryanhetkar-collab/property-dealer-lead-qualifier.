import os
import json
import streamlit as st
import google.generativeai as genai

# Page Configuration
st.set_page_config(
    page_title="Property Dealer AI Lead Qualifier",
    page_icon="🏠",
    layout="wide"
)

# ------------------------------------------------------------------------------
# 1. API Key Handling
# ------------------------------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

st.sidebar.title("Settings ⚙️")
manual_key = st.sidebar.text_input("Gemini API Key", value="", type="password")

if manual_key:
    api_key = manual_key

if api_key:
    genai.configure(api_key=api_key)

# ------------------------------------------------------------------------------
# 2. Heuristic Local Fallback Engine
# ------------------------------------------------------------------------------
def evaluate_lead_locally(text: str) -> dict:
    """Fallback logic when Gemini API key is missing or unavailable."""
    text_lower = text.lower()
    
    # Specific keywords for classification
    cold_keywords = ["2 days", "500", "cheap", "short term", "room on rent", "hostel", "pg", "rent"]
    hot_keywords = ["buy", "3bhk", "2bhk", "crore", "lakhs", "site visit", "pre-approved", "loan", "ready buyer"]

    # Cold Lead Logic
    if any(kw in text_lower for kw in cold_keywords) and not any(kw in text_lower for kw in ["buy", "crore", "lakhs"]):
        return {
            "score": 20,
            "category": "Cold",
            "reasons": [
                "Short-term rental or micro-budget request",
                "Unsuited for long-term real estate brokerage services"
            ],
            "action": "Politely decline or redirect to short-stay booking platforms.",
            "draft": "Hello! Thanks for reaching out. We specialize in long-term sales and leases. For daily room rentals, we recommend checking hospitality booking apps!"
        }
    
    # Hot Lead Logic
    elif any(kw in text_lower for kw in hot_keywords):
        return {
            "score": 90,
            "category": "Hot",
            "reasons": [
                "High purchase/investment intent detected",
                "Specific budget and site visit request"
            ],
            "action": "Schedule immediate phone call & book site visit within 2 hours.",
            "draft": "Hello! Thank you for reaching out. I'd be delighted to assist you with your property search and schedule a site visit this Sunday. When would be a good time to connect?"
        }
    
    # Warm Lead Logic (Default)
    else:
        return {
            "score": 55,
            "category": "Warm",
            "reasons": [
                "General inquiry about property listings",
                "Budget and timeline require further clarification"
            ],
            "action": "Send digital property catalog on WhatsApp and follow up in 24 hours.",
            "draft": "Hello! Thanks for reaching out. I've shared our latest property catalog. Please let me know your preferred location and budget so I can share matching options!"
        }

# ------------------------------------------------------------------------------
# 3. AI Lead Analysis Engine (Gemini)
# ------------------------------------------------------------------------------
def analyze_lead_with_gemini(inquiry: str) -> dict:
    if not api_key:
        return evaluate_lead_locally(inquiry)

    prompt = f"""
    You are an expert real estate AI lead qualifier. Analyze the following client inquiry:
    
    Inquiry: "{inquiry}"
    
    Respond STRICTLY with a valid JSON object matching this structure:
    {{
        "score": <integer from 0 to 100>,
        "category": "<Hot|Warm|Cold>",
        "reasons": ["<reason 1>", "<reason 2>"],
        "action": "<recommended action for real estate broker>",
        "draft": "<short follow-up message ready to send on WhatsApp/email>"
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        result = evaluate_lead_locally(inquiry)
        result["api_error"] = str(e)
        return result

# ------------------------------------------------------------------------------
# 4. Streamlit UI (With State Syncing)
# ------------------------------------------------------------------------------
st.title("🏠 Property Dealer AI Lead Qualifier")
st.caption("Automated Lead Triage & Response System for Real Estate Agents & Brokers")

scenarios = {
    "🔥 Hot Lead (Ready Buyer & Site Visit)": "Hi, I am looking to buy a 3BHK flat in prime location. Budget is around ₹85 Lakhs with pre-approved bank loan ready. I want to schedule a site visit this Sunday.",
    "🌤️ Warm Lead (General Catalog Request)": "Hi, can you share available 2BHK listings near HSR Layout along with price details?",
    "❄️ Cold Lead (Short Rental / Low Intent)": "Hi, looking for a room on rent for 2 days under ₹500/night."
}

def update_inquiry_text():
    st.session_state["inquiry_text"] = scenarios[st.session_state["selected_scenario"]]

if "inquiry_text" not in st.session_state:
    st.session_state["inquiry_text"] = scenarios["🔥 Hot Lead (Ready Buyer & Site Visit)"]

selected_scenario = st.selectbox(
    "Choose a sample scenario or enter custom text below:",
    list(scenarios.keys()),
    key="selected_scenario",
    on_change=update_inquiry_text
)

client_inquiry = st.text_area("Client Inquiry:", key="inquiry_text", height=120)

if st.button("🚀 Analyze Lead"):
    with st.spinner("Analyzing inquiry..."):
        result = analyze_lead_with_gemini(client_inquiry)

    if not api_key:
        st.info("⚡ Running in Local Fallback Engine (No API Key provided).")
    elif "api_error" in result:
        st.warning("⚡ Cloud API busy or key invalid. Activated Local Fallback Engine.")

    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    score = result.get("score", 50)
    category = result.get("category", "Warm")

    with col1:
        st.subheader("Lead Score")
        st.markdown(f"# {score} / 100")
        
        if category == "Hot":
            st.success("🔥 Category: Hot")
        elif category == "Warm":
            st.warning("🌤️ Category: Warm")
        else:
            st.error("❄️ Category: Cold")

        st.subheader("📋 Recommended Action")
        st.info(result.get("action", "Follow up with client."))

    with col2:
        st.subheader("💡 Key Reasons")
        for reason in result.get("reasons", []):
            st.markdown(f"• {reason}")

        st.subheader("✉️ Automated Follow-up Draft")
        st.text_area("Copy and send to client:", value=result.get("draft", ""), height=100)
