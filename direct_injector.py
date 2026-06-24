import os
from dotenv import load_dotenv
import streamlit as st
from supabase import create_client, Client

# Load your local .env file
load_dotenv()

# Check Streamlit secrets first, then fall back to your .env file
SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")

# Make sure this searches for the EXACT name you used in your files!
SUPABASE_KEY = (
    st.secrets.get("SUPABASE_KEY") or 
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or 
    st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing database URL or Secret Key credentials.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# 2. Hardcoded Off-Market Leads targeting your core columns
off_market_records = [
    {
        "title": "3 Bed Terrace - Anfield, Liverpool",
        "price": "£85,000",
        "link": "https://www.google.com/maps/search/?api=1&query=Anfield+Liverpool+Postcode",
        "reduced": "No",
        "keywords_found": "absentee landlord, empty home",
        "source_type": "off_market",  # 🔥 This fixes the filter split!
        "description": "Direct outreach target. Structural brickwork looks solid but needs complete modernization internally. High yield potential close to stadium.",
        "image_url": "None",
        "area": "Liverpool",
        "portal": "Direct Mail",
        "region": "Merseyside"
    },
    
       {
        "title": "Semi-Detached Project - Birkenhead, Wirral",
        "price": "£110,000",
        "reduced": "No",  # 👈 ADD THIS LINE BACK IN
        # Instantly opens the exact house in street view or maps
        "link": "https://www.google.com/maps/search/?api=1&query=Birkenhead+Wirral+Postcode",
        "keywords_found": "probate lead, tlc needed",
        "source_type": "off_market", # 🔥 This fixes the filter split!
        "description": "Deceased estate tracking. High-motivated executor looking for...",
        "image_url": "None",
        "area": "Wirral",
        "portal": "Direct Mail",
        "region": "Merseyside"
    }
    
]

print("🚀 Injecting un-brokered off-market records directly to cloud table...")
for record in off_market_records:
    try:
        response = supabase.table("property_deals").insert(record).execute()
        print(f"✅ Successfully inserted: {record['title']}")
    except Exception as e:
        print(f"❌ Failed to insert: {e}")