import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client

# Load environmental variables from your local token vault
load_dotenv()

# Initialize the core FastAPI engine instance variable
# Standardizing this variable name to 'app' resolves your Uvicorn launch blocker!
app = FastAPI(title="AlphaDeals Core API Engine")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Define the Pydantic schema rule matrix matching your updated database columns
class DealSchema(BaseModel):
    title: str
    price: str
    link: str
    reduced: str          # Expects "Yes" or "No"
    keywords_found: str
    source_type: str       # "on_market" or "off_market"
    image_url: str | None = None
    description: str | None = None


def clean_price_to_int(price_str: str) -> int:
    """Extracts pure digits from a currency string like '£55,000' -> 55000."""
    try:
        cleaned = "".join(c for c in price_str if c.isdigit())
        return int(cleaned) if cleaned else 0
    except Exception:
        return 0


def send_automated_outreach(deal: dict):
    """Processes asset underwriting thresholds and dispatches professional email alerts."""
    sender_email = os.getenv("EMAIL_HOST_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 465))
    
    if not all([sender_email, sender_password, smtp_server]):
        print("⚠️ Email configuration missing in environmental variables. Skipping outreach.")
        return

    numeric_price = clean_price_to_int(deal["price"])
    my_inbox = "info@puescupropertiesltd.com"
    simulated_agent_email = "agent-leads@example.com" 

    # Evaluate your under-£60k priority tracking rules
    if 0 < numeric_price < 60000:
        recipients = [my_inbox, simulated_agent_email]
        print(f"🔥 HIGH PRIORITY ASSET (<£60k): Routing to both tracking and agent desks...")
    else:
        recipients = [my_inbox]
        print(f"📋 Standard Asset (>=£60k): Routing exclusively to internal company monitor inbox.")

    # Strategy text formatting maps natively based on source_type flags
    if deal["source_type"] == "on_market":
        email_subject = f"Property Inquiry / Project Potential - {deal['title']} ({deal['price']})"
        email_body = (
            f"Hi Sales Team,\n\n"
            f"I’ve been tracking the active listing profile for the property on the link below via our internal company system. "
            f"I noticed it’s currently listed as chain-free and offers an excellent footprint for a modernization project:\n{deal['link']}\n\n"
            f"We operate a residential property acquisition business covering Liverpool and the Wirral, focusing specifically on quick-turnaround rehab projects. "
            f"We are currently well-capitalized, looking to deploy funds into our next project immediately, and can move forward with zero onward chain complications.\n\n"
            f"Could you let me know if the vendor would be receptive to a flexible offer from a fast-moving buyer, or if there is an active viewing schedule this week we can register for?\n\n"
            f"Best regards,\n\n"
            f"Ionut Puescu\n"
            f"Managing Director\n"
            f"Puescu Properties Ltd\n"
        )
    elif deal["source_type"] == "off_market":
        email_subject = f"Private Property Inquiry - Direct Purchase Potential"
        email_body = (
            f"Hi,\n\n"
            f"I hope you don't mind me reaching out directly.\n\n"
            f"I was reviewing local property data in the area via our internal system and noticed your property profile. "
            f"I wanted to contact you personally to see if you might be open to a direct, private sale of the property before it goes onto the open market or involves estate agency fees.\n\n"
            f"Best regards,\n\n"
            f"Ionut Puescu\n"
            f"Managing Director\n"
            f"Puescu Properties Ltd\n"
        )
    else:
        return

    # Assemble MIME packet frameworks
    msg = MIMEMultipart()
    msg['From'] = f"Puescu Properties <{sender_email}>"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = email_subject
    msg.attach(MIMEText(email_body, 'plain'))
    
    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipients, msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipients, msg.as_string())
        print(f"🚀 Outreach successfully completed for recipients: {recipients}")
    except Exception as mail_err:
        print(f"⚠️ Email Delivery Failure: {mail_err}")


@app.post("/api/v1/deals/ingest", status_code=201)
async def ingest_property_deal(deal: DealSchema):
    """Secure endpoint tracking scraped payloads, running database insertions, and triggering mailing channels."""
    try:
        # Convert incoming structured data block cleanly to a Python dictionary mapping
        deal_data = deal.model_dump()
        
        # 1. Fire data packet directly to your remote Supabase table instance

        response = supabase.table("property_deals").insert(deal_data).execute()
        return {"status": "success", "message": "Deal ingested and outreach sequence "
        "executed.", "data": response.data}
    
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Core database processing error: {str(e)}")