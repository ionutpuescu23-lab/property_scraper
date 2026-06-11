import os
import pandas as pd
import streamlit as st
from supabase import create_client
import requests
from PIL import Image
from io import BytesIO
# 1. Page Configuration (Must only be called ONCE at the absolute top)
st.set_page_config(page_title="AlphaDeals | Premium Investor Portal", layout="wide")

# 2. Initialize Persistent Session State for Login Flow
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# 3. Pull Target Keys Directly from the Cloud Secrets Vault
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY")
ADMIN_USER = st.secrets.get("ADMIN_USER")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD")

# 4. SIDEBAR SYSTEM
st.sidebar.header("🔐 Member Authentication")

if not st.session_state["authenticated"]:
    # Display secure form inputs if unauthenticated
    st.sidebar.subheader("Login to Access Pipeline")
    user_input = st.sidebar.text_input("Username", placeholder="e.g. investor_alpha", key="login_user")
    pass_input = st.sidebar.text_input("Access Key", type="password", placeholder="••••••••", key="login_pass")
    
    if st.sidebar.button("Verify Credentials", type="primary"):
        # Explicit comparison against your production TOML secrets
        if user_input.strip() == ADMIN_USER and pass_input.strip() == ADMIN_PASSWORD:
            st.session_state["authenticated"] = True
            st.sidebar.success("✅ Access Granted! Loading secure arrays...")
            st.rerun() # Refresh app to render the locked pipeline
        else:
            st.sidebar.error("❌ Invalid Credentials. Security barrier active.")
else:
    # Display profile info and logout button if authenticated
    st.sidebar.success("FT-Secure Session Active")
    st.sidebar.markdown("**Current Account:** `Premium Tier Investor`")
    
    st.sidebar.markdown("---")
    st.sidebar.header("Pipeline Configuration")
    fee_setting = st.sidebar.slider("Sourcing Unlock Fee (£)", min_value=500, max_value=3000, value=1500, step=250)
    
    if st.sidebar.button("Log Out", type="secondary"):
        st.session_state["authenticated"] = False
        st.rerun()


# 5. MAIN PLATFORM INTERFACE
if not st.session_state["authenticated"]:
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
    # PRIVATE MEMBER INTERFACE (Opens when authenticated is True)
    st.markdown("""
        <div style='background-color:#1E293B; padding:20px; border-radius:10px; margin-bottom:25px;'>
            <h1 style='color:white; margin:0; font-family:sans-serif;'>🌐 AlphaDeals Premium Investor Portal</h1>
            <p style='color:#94A3B8; margin:5px 0 0 0; font-size:16px;'>Proprietary High-Yield & Distressed Real Estate Sourcing Pipeline</p>
        </div>
    """, unsafe_allow_html=True)

    # 📡 LIVE CLOUD DATA STREAM INTEGRATION
    df = pd.DataFrame()  # Initialize an empty dataframe first
    
    try:
        # Initialize Supabase dynamically using safe vault keys
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Fetch records from your live backend table
        response = supabase.table("property_deals").select("*").order("created_at", desc=True).execute()
        
        # Parse into a clean dataframe
        if response.data:
            df = pd.DataFrame(response.data)
            
    except Exception as e:
        st.error(f"❌ Core Database Stream Failure: Unable to handshake with cloud repository. Details: {e}")

    # 🏢 RENDER THE DEAL PIPELINE DISPLAY (Runs only if data was fetched successfully)
    if not df.empty:
        total_found = len(df)
        reduced_count = len(df[df['reduced'] == 'Yes']) if 'reduced' in df.columns else 0
        
        # Render live pipeline KPI widgets
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
                    st.subheader(f"🏠 {row.get('title', 'Unknown Sourced Asset')}")
                    st.markdown(f"**Target Signals Captured:** :red[{row.get('keywords_found', 'N/A')}]")
                    st.text(f"Market Price: {row.get('price', 'N/A')} | Reduced Status: {row.get('reduced', 'N/A')}")
                    
                with c2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    analyze_deal = st.checkbox("🔍 Analyze Deal Structure", key=f"analysis_{index}")
                    
                with c3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    pay_clicked = st.button(f"🔒 Unlock for £{fee_setting}", key=f"pay_{index}", type="primary")

                # 📉 DROP DOWN ANALYTICS PANEL (Triggers when check box is active)
                if analyze_deal:
                    st.markdown("---")
                    st.markdown("### 📊 Proprietary Underwriting Data Matrix")
                    
                   # 🖼️ RENDER LIVE IMAGE FROM SUPABASE INSIDE THE CARD
                    img_val = row.get('image_url')
                    if img_val and str(img_val).strip() != 'None' and str(img_val).strip() != 'NULL':
                        st.image(str(img_val).strip(), caption=f"Asset Gallery Showcase: {row.get('title')}", use_container_width=True)
                    
                    # Split details panel into two scannable columns
                    left_panel, right_panel = st.columns(2)
                    
                    with left_panel:
                        st.markdown("#### **📍 Asset Overview & Signals**")
                        st.info(f"**Target Sourcing Keywords Detected:** {row.get('keywords_found', 'N/A')}")
                        
                        # RENDER LIVE DESCRIPTION TEXT FROM SUPABASE
                        desc_val = row.get('description')
                        if desc_val and str(desc_val).strip() != 'None' and str(desc_val).strip() != 'NULL':
                            st.success(f"📋 **Underwriting Evaluation Summary:**\n\n{desc_val}")
                        else:
                            st.write("_This asset was flagged by the background scraper tracking raw market anomalies. Custom underwriting overview notes are currently pending upload for this specific record._")
                    
                    with right_panel:
                        st.markdown("#### **🧮 Live BRRRR Deal Calculator**")
                        try:
                            raw_price = float(''.join(c for c in str(row.get('price', '0')) if c.isdigit()))
                        except ValueError:
                            raw_price = 100000.0
                            
                        estimated_rehab = st.number_input("Estimated Rehab/Renovation (£)", min_value=0, value=25000, step=2500, key=f"rehab_{index}")
                        projected_rent = st.number_input("Projected Monthly Rent (£)", min_value=0, value=850, step=50, key=f"rent_{index}")
                        
                        total_capital_in = raw_price + estimated_rehab
                        annual_gross_yield = (projected_rent * 12) / total_capital_in if total_capital_in > 0 else 0
                        
                        st.metric("Estimated Total Capital Investment", f"£{total_capital_in:,}")
                        st.metric("Projected Gross Yield on Cost", f"{annual_gross_yield:.2%}")

                # 💳 UNLOCK DATA OVERLAY (Triggers when they hit the pay button)
                if pay_clicked:
                    st.markdown("---")
                    with st.container(border=True):
                        st.success(f"💳 Initializing secure checkout sequence for Sourcing Premium...")
                        st.markdown("### 🔑 Sourcing Verification Unlocked")
                        st.write(f"**Direct Secure Vendor Lead URL:**")
                        st.link_button("🌐 Open Source Listing Link", row.get('link', '#'), type="primary", use_container_width=True)
                        
    elif df.empty:
        st.warning("⚠️ Cloud connection is active, but your database is currently blank. Execute your local loader pipeline to stream records here!")