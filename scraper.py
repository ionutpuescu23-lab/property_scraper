import requests
import re
import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load your hidden cloud keys into memory
load_dotenv()

def scrape_investor_deals(search_url, max_listings_to_check=10):
    listing_links = []
    deals = []
    
    with sync_playwright() as p:
        print("🚀 Step 1: Deploying Stealth Crawler to harvest property links...")
        
        # Define a premium, clean human identity matrix
        human_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        
        # Launch a single, independent browser engine instance
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        
        # Spin up a completely fresh, isolated in-memory user context profile
        context = browser.new_context(
            user_agent=human_user_agent,
            no_viewport=True
        )
        
        page = context.new_page()
        
        # NATIVE STEALTH SHIELD: Erase automated testing fingerprints instantly
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)   
        
        # Open main search results page with human navigation timing
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        
        # Bypass Cookie Popup natively
        try:
            cookie_button = page.locator("button:has-text('Accept'), button:has-text('Manage')").first
            if cookie_button.is_visible():
                cookie_button.click()
                time.sleep(2)
        except Exception:
            pass
            
        print("Extracting all page hyperlinks natively...")
        all_links = page.locator("a").evaluate_all("elements => elements.map(el => el.href)")
        
        for href in all_links:
            if href and "/for-sale/details/" in href and href not in listing_links:
                listing_links.append(href)
                
        print(f"Harvest complete. Discovered {len(listing_links)} unique property links.")
        
        links_to_check = listing_links[:max_listings_to_check]
        print(f"\n🔍 Step 2: Initiating Deep-Dive on top {len(links_to_check)} properties...")
        
        target_keywords = [
            "modernisation", "modernization", "refurb", "tlc", "updating", 
            "repaired", "structural", "auction", "cash buyers", "motivated", 
            "chain free", "investment", "yield", "hmo", "tenant"
        ]
        
        for idx, link in enumerate(links_to_check, 1):
            print(f"[{idx}/{len(links_to_check)}] Analyzing listing data profile...")
            try:
                page.goto(link, wait_until="domcontentloaded", timeout=45000)
                
                # Human reading behavior emulations
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 4);")
                time.sleep(2)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(2)
                
                # Structural text collection
                content_elements = page.locator("h1, h2, h3, p, span, li").all_text_contents()
                clean_segments = [txt.strip() for txt in content_elements if txt and len(txt.strip()) < 1000]
                page_text = " ".join(clean_segments)
                page_text_lower = page_text.lower()
                
                matched_keywords = [kw for kw in target_keywords if kw in page_text_lower]
                
                if matched_keywords:
                    price_found = "Price on Application"
                    for segment in clean_segments:
                        if "£" in segment:
                            match = re.search(r'£[0-9,]+', segment)
                            if match:
                                price_found = match.group(0)
                                break
                    
                    title_found = "Residential Investment Property"
                    for segment in clean_segments:
                        seg_lower = segment.lower()
                        if "bedroom" in seg_lower and ("sale" in seg_lower or "house" in seg_lower or "flat" in seg_lower):
                            if len(segment) < 100:
                                title_found = segment.strip().title()
                                break
                    
                    print(f"   🎉 Investor Deal Found! Price: {price_found} | Signals: {', '.join(matched_keywords)}")
                    
                    # Map boolean status cleanly to your database text settings ("Yes" / "No")
                    is_reduced = "Yes" if "reduced" in page_text_lower else "No"

                   # Formulate payload exactly matching your FastAPI Pydantic schema rules
                    payload = {
                        "title": title_found,
                        "price": price_found,
                        "link": link,
                        "reduced": "reduced" in page_text_lower,  # Sends pure True or False boolean natively
                        "keywords_found": ", ".join(matched_keywords),
                        "source_type": "on_market"  # Since we're scraping an on-market portal
                    }
                    payload = {
                        "title": "Direct Vendor Lead - 3 Bed Terrace",
                        "price": "£120,000",
                        "link": "https://puescupropertiesltd.com/internal-id-102",
                        "reduced": False,
                        "keywords_found": "motivated seller",
                        "source_type": "off_market"  # This flags the direct-to-vendor pitch!
                    }
                    # Direct data stream to your centralized FastAPI backend endpoint
                    backend_url = "http://127.0.0.1:8000/api/v1/deals/ingest"
                    
                    try:
                        api_response = requests.post(backend_url, json=payload)
                        if api_response.status_code == 200:
                            print("   📡 Asset routed through FastAPI core and synchronized to the cloud safely.")
                        else:
                            print(f"   ⚠️ Backend validation rejected the deal: {api_response.text}")
                    except Exception as api_err:
                        print(f"   ⚠️ Could not establish connection to the FastAPI server: {api_err}")
            
            except Exception as scrape_err:
                print(f"   ⚠️ Failed to scrape listing: {scrape_err}")
                
        # Gracefully disconnect core automated engine pieces
        page.close()
        context.close()
        browser.close()
        
    return deals
    

if __name__ == "__main__":
    TARGET_SEARCH = "https://www.zoopla.co.uk/for-sale/property/liverpool/?page_size=25&sort_by=most_reduced&pn=1"
    
    print("\n⚡ Starting Sourcing Pipeline Loop ⚡")
    scrape_investor_deals(TARGET_SEARCH, max_listings_to_check=5)
    print("\n🎉 Cloud Harvest Cycle Complete!")