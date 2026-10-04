import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
import time

# --- Page Config ---
st.set_page_config(
    page_title="Property Dealer AI Lead Qualifier",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Property Dealer AI Lead Qualifier")
st.caption("Automated Lead Triage & Response System for Real Estate Agents & Brokers")

# --- Pydantic Data Contract ---
class LeadEvaluation(BaseModel):
    lead_score: int = Field(description="Score from 0 to 100 based on buyer/seller readiness and budget.")
    category: str = Field(description="Lead tier: 'Hot', 'Warm', or 'Cold'.")
    key_reasons: list[str] = Field(description="3-4 concise bullet points explaining the score.")
    dealer_action: str = Field(description="Immediate action for the property dealer (e.g., 'Schedule site visit within 1 hour').")
    draft_response: str = Field(description="A professional email/WhatsApp message draft tailored to the client.")

# --- Local Heuristic Fallback Engine ---
def local_heuristic_fallback(text: str) -> LeadEvaluation:
    text_lower = text.lower()
    
    # Keywords indicating high intent / Indian real estate terminology
    hot_keywords = ["buy", "purchase", "site visit", "pre-approved", "ready to close", "cash buyer", "booking", "3bhk", "2bhk", "plot", "flat", "lakh", "lakhs", "crore", "cr"]
    cold_keywords = ["rent for 1 day", "cheap rent", "free consultation", "jobs", "hiring", "spam", "daily rent"]
    
    if any(k in text_lower for k in cold_keywords):
        return LeadEvaluation(
            lead_score=20,
            category="Cold",
            key_reasons=["Low-budget rental or non-buyer inquiry", "Out of primary property sales scope"],
            dealer_action="Auto-reply with FAQ link or standard rental brochure.",
            draft_response="Namaste! Thank you for reaching out. We specialize in property sales and long-term deals. For short-term rental queries, please visit our website FAQ."
        )
    elif any(k in text_lower for k in hot_keywords):
        return LeadEvaluation(
            lead_score=85,
            category="Hot",
            key_reasons=["High purchase intent detected", "Explicit property interest or site visit request with budget"],
            dealer_action="Call client immediately to schedule a property site visit.",
            draft_response="Namaste! Thank you for contacting us regarding our property listings. I would love to arrange a site visit for you this weekend. When are you available for a quick call?"
        )
        
    return LeadEvaluation(
        lead_score=55,
        category="Warm",
        key_reasons=["General inquiry about listings", "Budget and timeline require further clarification"],
        dealer_action="Send digital property catalog on WhatsApp and follow up in 24 hours.",
        draft_response="Hello! Thanks for reaching out. I've shared our latest property catalog. Please let me know your preferred location and budget (in Lakhs/Crores) so I can share matching options!"
    )

# --- Sidebar API Key Input ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password")

# --- UI Input Options (INR Values) ---
sample_inquiries = {
    "Select a pre-loaded property inquiry...": "",
    "🔥 Hot Lead (Ready Buyer & Site Visit)": "Hi, I am looking to buy a 3BHK flat in prime location. Budget is around ₹85 Lakhs with pre-approved bank loan ready. I want to schedule a site visit this Sunday.",
    "🌤️ Warm Lead (Exploring Options)": "Hello, my family is looking for commercial plots or residential flats for investment in the next quarter. Budget is ₹1.5 Crore. Can you send over available options and pricing details?",
    "❄️ Cold Lead (Short Rental / Low Intent)": "Hi, looking for a room on rent for 2 days under ₹500/night."
}

selected_sample = st.selectbox("Choose a sample scenario or enter custom text below:", list(sample_inquiries.keys()))

if selected_sample and sample_inquiries[selected_sample]:
    user_input = st.text_area("Client Inquiry:", value=sample_inquiries[selected_sample], height=120)
else:
    user_input = st.text_area("Client Inquiry:", placeholder="Paste incoming customer message, email, or WhatsApp text here (e.g. 2BHK in Mumbai, budget ₹75 Lakhs)...", height=120)

# --- Process Inquiry ---
if st.button("🚀 Analyze Lead"):
    if not user_input.strip():
        st.warning("Please enter a message to analyze.")
    else:
        result = None
        
        if api_key:
            try:
                client = genai.Client(api_key=api_key)
                system_prompt = """
                You are an AI Lead Triage Assistant for an Indian Property Dealer and Real Estate Broker.
                Evaluate incoming buyer, seller, or investor inquiries.
                
                Scoring Guidelines (in INR - Lakhs & Crores):
                - Hot (80-100): Clear intent to buy/sell, budget defined (e.g. ₹50L+, ₹1Cr+), pre-approved loan/cash ready, or site visit requested within 7-14 days.
                - Warm (40-79): Exploring options for 1-3 months out, asking for catalogs or brochures, flexible budget.
                - Cold (0-39): Extremely low budget, short-term daily rental queries (e.g. under ₹1,000/night), vendor spam, or general non-prospects.
                """
                
                # Resilient execution with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=f"Analyze this inquiry: {user_input}",
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                response_mime_type="application/json",
                                response_schema=LeadEvaluation,
                                temperature=0.2
                            )
                        )
                        result = LeadEvaluation.model_validate_json(response.text)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            st.info("⚡ Cloud API busy. Activated Local Fallback Engine.")
                            result = local_heuristic_fallback(user_input)
                        else:
                            time.sleep(2 ** attempt)
            except Exception:
                st.info("⚡ API execution failed. Activated Local Fallback Engine.")
                result = local_heuristic_fallback(user_input)
        else:
            st.info("⚡ Running in Local Fallback Mode (No API Key provided).")
            result = local_heuristic_fallback(user_input)
            
        # --- Display Results ---
        if result:
            st.markdown("---")
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric(label="Lead Score", value=f"{result.lead_score} / 100")
                if result.category == "Hot":
                    st.error(f"🔥 Category: {result.category}")
                elif result.category == "Warm":
                    st.warning(f"🌤️ Category: {result.category}")
                else:
                    st.info(f"❄️ Category: {result.category}")
                    
                st.subheader("📋 Recommended Action")
                st.info(result.dealer_action)

            with col2:
                st.subheader("💡 Key Reasons")
                for reason in result.key_reasons:
                    st.write(f"• {reason}")
                    
                st.subheader("✉️ Automated Follow-up Draft")
                st.text_area("Copy and send to client:", value=result.draft_response, height=130)