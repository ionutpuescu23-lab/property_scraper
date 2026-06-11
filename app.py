import streamlit as st
from supabase import create_client

# Streamlit looks at your local .env locally, and its secure Cloud Vault in production!
url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
key = st.secrets.get("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(url, key)


# 1. Page Configuration
st.set_page_config(page_title="AlphaDeals | Premium Investor Portal", layout="wide")

# 2. Initialize Persistent Session States for Login Flow
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ──── SIDEBAR SYSTEM ────
st.sidebar.header("🔐 Member Authentication")

if not st.session_state["logged_in"]:
    # Display secure form inputs if unauthenticated
    st.sidebar.subheader("Login to Access Pipeline")
    user_input = st.sidebar.text_input("Username", placeholder="e.g. investor_alpha")
    pass_input = st.sidebar.text_input("Access Key", type="password", placeholder="••••••••")
    
    if st.sidebar.button("Verify Credentials", type="primary"):

        # Pull the safe values from your background memory environment
        if user_input == os.getenv("PORTAL_USERNAME") and pass_input == os.getenv("PORTAL_ACCESS_KEY"):
            st.session_state["logged_in"] = True
            st.sidebar.success("✅ Access Granted! Loading secure arrays...")
            st.rerun() # Refresh app to render the locked pipeline
        else:
            st.sidebar.error("❌ Invalid Credentials. Security barrier active.")
else:
    # Display profile info and logout button if authenticated
    st.sidebar.success("🔒 Secured Session Active")
    st.sidebar.markdown("**Current Account:** `Premium Tier Investor`")
    
    st.sidebar.markdown("---")
    st.sidebar.header("Pipeline Configuration")
    fee_setting = st.sidebar.slider("Sourcing Unlock Fee (£)", min_value=500, max_value=3000, value=1500, step=250)
    
    if st.sidebar.button("Log Out", type="secondary"):
        st.session_state["logged_in"] = False
        st.rerun()


# ──── MAIN PLATFORM INTERFACE ────
if not st.session_state["logged_in"]:
    # PUBLIC PAYWALL SKELETON (What non-members see)
    st.markdown("""
        <div style='background-color:#0F172A; padding:40px; border-radius:12px; border: 1px solid #1E293B; text-align:center; margin-top:50px;'>
            <h1 style='color:#F1F5F9; font-family:sans-serif;'>🌐 AlphaDeals Premium Investor Portal</h1>
            <p style='color:#64748B; font-size:18px; margin-bottom:30px;'>Proprietary High-Yield & Distressed Real Estate Sourcing Pipeline</p>
            <div style='background-color:#1E293B; padding:20px; border-radius:8px; display:inline-block; max-width:500px;'>
                <h3 style='color:#E2E8F0; margin-top:0;'>🔒 Restricted Data Stream</h3>
                <p style='color:#94A3B8; font-size:14px; margin-bottom:0;'>This dashboard broadcasts raw market anomalies, flipped options, and off-market residential assets. Use the sidebar module to verify your institutional access key.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

else:
    # PRIVATE MEMBER INTERFACE (What opens when logged_in is True)
    st.markdown("""
        <div style='background-color:#1E293B; padding:20px; border-radius:10px; margin-bottom:25px;'>
            <h1 style='color:white; margin:0; font-family:sans-serif;'>🌐 AlphaDeals Premium Investor Portal</h1>
            <p style='color:#94A3B8; margin:5px 0 0 0; font-size:16px;'>Proprietary High-Yield & Distressed Real Estate Sourcing Pipeline</p>
        </div>
    """, unsafe_allow_html=True)

    # 📡 LIVE CLOUD DATA STREAM INTEGRATION
    try:
        # Fetch the harvested records streaming directly from your Supabase backend
        # Correct line matching your package version
        response = supabase.table("property_deals").select("*").order("created_at", desc=True).execute()
        
        # Parse the response data block
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        
        if not df.empty:
            total_found = len(df)
            # Checked against the lowercased column names from your database schema
            reduced_count = len(df[df['reduced'] == 'Yes'])
            
            # Render your high-level pipeline data KPI cards
            col1, col2, col3 = st.columns(3)
            col1.metric("Active Sourced Assets", total_found)
            col2.metric("Price Reduced Opportunities", reduced_count, delta=f"{int((reduced_count/total_found)*100)}%" if total_found > 0 else "0%")
            col3.metric("Target Sourcing Premium", f"£{fee_setting:,}")
            
            st.markdown("### 📋 Active Investment Deal Pipeline")
            st.success("📡 Live Cloud Data Pipeline Active — Remote Database Synchronized")
            st.write("Review aggregated off-market profiles below. Click **'Analyze Deal Structure'** to review masked indicators.")
            
            # Loop through individual database entries to render custom property slots
            for index, row in df.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    
                    with c1:
                        st.subheader(f"🏠 {row['title']}")
                        st.markdown(f"**Target Signals Captured:** :red[{row['keywords_found']}]")
                        st.text(f"Price: {row['price']} | Reduced Status: {row['reduced']}")
                        
                    with c2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.button("🔍 Analyze Deal Structure", key=f"analysis_{index}")
                        
                    with c3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button(f"🔒 Unlock for £{fee_setting}", key=f"pay_{index}", type="primary"):
                            st.success(f"💳 Initializing secure checkout sequence...")
                            st.info(f"**Verified Asset Link Ready:** {row['link']}")
                            
        else:
            st.warning("⚠️ Cloud connection is active, but your database is currently blank. Execute your scraper pipeline to stream rows here!")
            
    except Exception as e:
        st.error(f"❌ Core Database Stream Failure: Unable to handshake with cloud repository. Details: {e}")