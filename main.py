import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def clean_price_to_int(price_str: str) -> int:
    """Extracts digits from a currency string like '£55,000' -> 55000."""
    try:
        cleaned = "".join(c for c in price_str if c.isdigit())
        return int(cleaned) if cleaned else 0
    except Exception:
        return 0

def send_automated_outreach(deal: dict):
    sender_email = os.getenv("EMAIL_HOST_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 465))
    
    # 1. Parse the numerical price to evaluate your criteria
    numeric_price = clean_price_to_int(deal["price"])
    
    # 2. Establish recipient routing logic based on your £60k rule
    my_inbox = "info@puescupropertiesltd.com"
    
    # Placeholder: In a fully public scraper, 'deal["agent_email"]' would be scraped. 
    # For now, we use a placeholder or test email destination for the agent side.
    simulated_agent_email = "agent-leads@example.com" 

    if numeric_price > 0 and numeric_price < 60000:
        # Under £60k: Send to BOTH you and the agent simultaneously
        recipients = [my_inbox, simulated_agent_email]
        print(f"🔥 HIGH PRIORITY ASSET (<£60k): Routing to both tracking and agent desks...")
    else:
        # Over £60k: ONLY send to you (Internal monitoring only)
        recipients = [my_inbox]
        print(f"📋 Standard Asset (>=£60k): Routing exclusively to internal company monitor inbox.")

    # Strategy text assignment based on source_type
    if deal["source_type"] == "on_market":
        email_subject = f"Property Inquiry / Project Potential - {deal['title']} ({deal['price']})"
        email_body = f"Hi Sales Team,\n\nI’ve been tracking the active listing profile for the property on the link below via our internal company system. I noticed it’s currently listed as chain-free and offers an excellent footprint for a modernization project:\n{deal['link']}\n\nWe operate a residential property acquisition business covering Liverpool and the Wirral, focusing specifically on quick-turnaround rehab projects. We are currently well-capitalized, looking to deploy funds into our next project immediately, and can move forward with zero onward chain complications.\n\nCould you let me know if the vendor would be receptive to a flexible offer from a fast-moving buyer, or if there is an active viewing schedule this week we can register for?\n\nBest regards,\n\nIonut Puescu\nMining Director\nPuescu Properties Ltd\n"
    elif deal["source_type"] == "off_market":
        email_subject = f"Private Property Inquiry - Direct Purchase Potential"
        email_body = f"Hi,\n\nI hope you don't mind me reaching out directly.\n\nI was reviewing local property data in the area via our internal system and noticed your property profile. I wanted to contact you personally to see if you might be open to a direct, private sale of the property before it goes onto the open market or involves estate agency fees.\n\nBest regards,\n\nIonut Puescu\nManaging Director\nPuescu Properties Ltd\n"
    else:
        return

    # Assemble and fire email packets to all assigned recipients
    msg = MIMEMultipart()
    msg['From'] = f"Puescu Properties <{sender_email}>"
    msg['To'] = ", ".join(recipients)  # Standard formatting string for multi-delivery
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