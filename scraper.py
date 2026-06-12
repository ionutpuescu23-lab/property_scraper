import os
import re
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load your hidden cloud keys into memory
load_dotenv()

def scrape_investor_deals(search_url, max_listings_to_check=10):
    listing_links = []
    deals = []
    
    with sync_playwright() as p:
        print("🚀 Step 1: Deploying Stealth Crawler to harvest property links...")
        
        human_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        
        context = browser.new_context(
            user_agent=human_user_agent,
            no_viewport=True
        )
        
        page = context.new_page()
        
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)   
        
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        
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
                
                # 🖼️ AUTOMATED EXTRACTION: Target the primary property showcase image link
                # Zoopla uses standard picture/img tags inside their main banner slider
                scraped_image = "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=800&q=80" # High-quality fallback
                try:
                    img_element = page.locator("picture img, [data-testid='hero-image']").first
                    if img_element.is_visible():
                        img_url = img_element.get_attribute("src")
                        if img_url:
                            scraped_image = img_url
                except Exception:
                    pass

                # 📋 AUTOMATED EXTRACTION: Target the actual property description description text block
                scraped_description = ""
                try:
                    # Target common description containers or look for text blocks under main headers
                    desc_element = page.locator("[data-testid='description-section'], section:has(h2:has-text('Description'))").first
                    if desc_element.is_visible():
                        scraped_description = desc_element.text_content().strip()
                except Exception:
                    pass

                # Structural text collection for keyword detection
                content_elements = page.locator("h1, h2, h3, p, span, li").all_text_contents()
                clean_segments = [txt.strip() for txt in content_elements if txt and len(txt.strip()) < 1000]
                page_text = " ".join(clean_segments)
                page_text_lower = page_text.lower()
                
                # Fallback text assignment if specialized container wasn't hit
                if not scraped_description:
                    longest_segments = sorted([s for s in clean_segments if len(s) > 100], key=len, reverse=True)
                    scraped_description = longest_segments[0] if longest_segments else "Off-market deal metrics extracted from background pipeline data streams."

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
                    
                    # ⚡ DYNAMIC PRODUCTION PAYLOAD (Fully unified to feed your schema)
                    payload = {
                        "title": title_found,
                        "price": price_found,
                        "link": link,
                        "reduced": "Yes" if "reduced" in page_text_lower else "No", # Synchronized with your app metrics checker logic
                        "keywords_found": ", ".join(matched_keywords),
                        "source_type": "on_market",
                        "image_url": scraped_image,          # Automatically injects scraped listing photo link
                        "description": scraped_description    # Automatically injects full brochure text blocks
                    }
                    
                    # Direct data stream to your centralized FastAPI backend endpoint
                    backend_url = "http://127.0.0.1:8000/api/v1/deals/ingest"
                    
                    try:
                        api_response = requests.post(backend_url, json=payload)
                        if api_response.status_code == 200 or api_response.status_code == 201:
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