import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv, load_load_env # Import the env loader

# Load your hidden vault values into Python's memory
load_dotenv()


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
        # DEMO CREDENTIALS: You can change these to whatever you like
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

    # Load the scraped data pipeline
    try:
        df = pd.read_csv("distressed_property_deals.csv")
        
        if not df.empty:
            total_found = len(df)
            reduced_count = len(df[df['Reduced'] == 'Yes'])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Active Sourced Assets", total_found)
            col2.metric("Price Reduced Opportunities", reduced_count, delta=f"{int((reduced_count/total_found)*100)}%" if total_found > 0 else "0%")
            col3.metric("Target Sourcing Premium", f"£{fee_setting:,}")
            
            st.markdown("### 📋 Active Investment Deal Pipeline")
            st.write("Review aggregated off-market profiles below. Click **'Analyze Deal Structure'** to review masked indicators.")
            
            for index, row in df.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    
                    with c1:
                        st.subheader(f"🏠 {row['Title']}")
                        st.markdown(f"**Target Signals Captured:** :red[{row['Keywords Found']}]")
                        st.text(f"Price: {row['Price']} | Reduced Status: {row['Reduced']}")
                        
                    with c2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.button("🔍 Analyze Deal Structure", key=f"analysis_{index}")
                        
                    with c3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button(f"🔒 Unlock for £{fee_setting}", key=f"pay_{index}", type="primary"):
                            st.success(f"💳 Initializing secure checkout sequence...")
                            st.info(f"**Verified Asset Link Ready:** {row['Link']}")
                            
        else:
            st.warning("⚠️ Database is active, but no records currently match inside 'distressed_property_deals.csv'.")
    except FileNotFoundError:
        st.error("❌ Source Pipeline Missing: 'distressed_property_deals.csv' not found. Run 'python scraper.py' first.")