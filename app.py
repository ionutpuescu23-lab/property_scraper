import os
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

st.set_page_config(
    page_title="AlphaDeals | Premium Investor Portal",
    layout="wide"
)

load_dotenv()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

SUPABASE_URL = (
    st.secrets.get("SUPABASE_URL", None)
    or os.environ.get("SUPABASE_URL")
)

SUPABASE_KEY = (
    st.secrets.get("SUPABASE_KEY", None)
    or st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", None)
    or os.environ.get("SUPABASE_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

st.sidebar.header("🔐 Member Authentication")

if not st.session_state["authenticated"]:
    st.sidebar.subheader("Login to Access Pipeline")
    user_input = st.sidebar.text_input("Username", placeholder="e.g. investor_alpha", key="login_user")
    pass_input = st.sidebar.text_input("Access Key", type="password", placeholder="••••••••", key="login_pass")

    if st.sidebar.button("Verify Credentials", type="primary"):
        if user_input == "admin" and pass_input == "liverpool2026":
            st.session_state["authenticated"] = True
            st.sidebar.success("✅ Access Granted! Loading secure arrays...")
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Credentials. Security barrier active.")
else:
    st.sidebar.success("FT-Secure Session Active")
    st.sidebar.markdown("**Current Account:** `Premium Tier Investor`")
    st.sidebar.markdown("---")
    st.sidebar.header("Pipeline Configuration")

    fee_setting = st.sidebar.slider(
        "Sourcing Unlock Fee (£)",
        min_value=700,
        max_value=3000,
        value=1500,
        step=250
    )

    if st.sidebar.button("Log Out", type="secondary"):
        st.session_state["authenticated"] = False
        st.rerun()


def is_real_value(value):
    return value is not None and str(value).strip() not in ["", "None", "NULL", "nan"]


def build_maps_url(row):
    address = str(row.get("address", "")).strip()
    postcode = str(row.get("postcode", "")).strip()

    if is_real_value(address) and is_real_value(postcode) and postcode not in address:
        query = f"{address}, {postcode}"
    elif is_real_value(address):
        query = address
    elif is_real_value(postcode):
        query = postcode
    else:
        return None

    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def clean_source_url(raw_url):
    if not is_real_value(raw_url):
        return None

    raw_url = str(raw_url).strip()

    if raw_url == "#" or "google.com/maps" in raw_url:
        return None

    if not raw_url.startswith(("http://", "https://")):
        raw_url = f"https://{raw_url}"

    return raw_url


if not st.session_state["authenticated"]:
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
    st.markdown("""
        <div style='background-color:#1E293B; padding:20px; border-radius:10px; margin-bottom:25px;'>
            <h1 style='color:white; margin:0; font-family:sans-serif;'>🌐 AlphaDeals Premium Investor Portal</h1>
            <p style='color:#94A3B8; margin:5px 0 0 0; font-size:16px;'>Proprietary High-Yield & Distressed Real Estate Sourcing Pipeline</p>
        </div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame()

    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("❌ Supabase keys missing. Check your .streamlit/secrets.toml or .env file.")
        else:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            response = (
                supabase
                .table("property_deals")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )

            if response.data:
                df = pd.DataFrame(response.data)

    except Exception as e:
        st.error(f"❌ Core Database Stream Failure: Unable to handshake with cloud repository. Details: {e}")


    if not df.empty:
        total_found = len(df)
        reduced_count = len(df[df["reduced"] == "Yes"]) if "reduced" in df.columns else 0
        reduced_percentage = (reduced_count / total_found) * 100 if total_found > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Active Sourced Assets", total_found)
        col2.metric("Price Reduced Opportunities", reduced_count, delta=f"{reduced_percentage:.1f}%")
        col3.metric("Target Sourcing Fee", f"£{fee_setting:,}")

        st.markdown("### 📋 Active Investment Deal Pipeline")
        st.success("📡 Live Cloud Data Pipeline Active — Remote Database Synchronized")
        st.write("Review aggregated off-market profiles below. Click **'Analyze Deal Structure'** to review masked indicators.")

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
                    pay_clicked = st.button(
                        f"🔒 Unlock for £{fee_setting}",
                        key=f"pay_{index}",
                        type="primary"
                    )

                if analyze_deal:
                    st.markdown("---")
                    st.markdown("### 📊 Proprietary Underwriting Data Matrix")

                    img_val = row.get("image_url")
                    if is_real_value(img_val):
                        clean_url = str(img_val).strip()
                        try:
                            if clean_url.startswith(("http://", "https://")):
                                st.image(
                                    clean_url,
                                    caption=f"Asset Gallery Showcase: {row.get('title')}",
                                    use_container_width=True
                                )
                            else:
                                st.write("📷 _Invalid image URL format stored in database._")
                        except Exception:
                            st.write("📷 _Image asset temporarily unavailable or link format invalid._")

                    left_panel, right_panel = st.columns(2)

                    with left_panel:
                        st.markdown("#### **📍 Asset Overview & Signals**")
                        st.info(f"**Target Sourcing Keywords Detected:** {row.get('keywords_found', 'N/A')}")

                        if is_real_value(row.get("address")):
                            st.write(f"**Address:** {row.get('address')}")
                        if is_real_value(row.get("postcode")):
                            st.write(f"**Postcode:** {row.get('postcode')}")
                        if is_real_value(row.get("street")):
                            st.write(f"**Street:** {row.get('street')}")

                        desc_val = row.get("description")
                        if is_real_value(desc_val):
                            st.success(f"📋 **Underwriting Evaluation Summary:**\n\n{desc_val}")
                        else:
                            st.write("_Custom underwriting overview notes are currently pending upload for this record._")

                    with right_panel:
                        st.markdown("#### **🧮 Live BRRRR Deal Calculator**")
                        try:
                            raw_price = float("".join(c for c in str(row.get("price", "0")) if c.isdigit()))
                        except ValueError:
                            raw_price = 100000.0

                        estimated_rehab = st.number_input(
                            "Estimated Rehab/Renovation (£)",
                            min_value=0,
                            value=25000,
                            step=2500,
                            key=f"rehab_{index}"
                        )
                        projected_rent = st.number_input(
                            "Projected Monthly Rent (£)",
                            min_value=0,
                            value=850,
                            step=50,
                            key=f"rent_{index}"
                        )

                        total_capital_in = raw_price + estimated_rehab
                        annual_gross_yield = (projected_rent * 12) / total_capital_in if total_capital_in > 0 else 0

                        st.metric("Estimated Total Capital Investment", f"£{total_capital_in:,.0f}")
                        st.metric("Projected Gross Yield on Cost", f"{annual_gross_yield:.2%}")

                if pay_clicked:
                    st.markdown("---")
                    with st.container(border=True):
                        st.success("💳 Initializing secure checkout sequence for Sourcing Premium...")
                        st.markdown("### 🔑 Sourcing Verification Unlocked")

                        maps_url = build_maps_url(row)
                        source_url = clean_source_url(row.get("link"))

                        if maps_url:
                            st.link_button(
                                "📍 Open Address in Google Maps",
                                maps_url,
                                type="primary",
                                use_container_width=True
                            )

                        if source_url:
                            st.link_button(
                                "🔗 Open Original Source Listing",
                                source_url,
                                use_container_width=True
                            )

                        if not maps_url and not source_url:
                            st.warning("No usable address or original source link is stored for this record yet.")

    else:
        st.warning("⚠️ Cloud connection is active, but your database is currently blank. Execute your local loader pipeline to stream records here!")
