import time
import re
import pandas as pd
from playwright.sync_api import sync_playwright
# Import our new stealth evasion engine
import playwright_stealth.stealth

def scrape_investor_deals(search_url, max_listings_to_check=10):
    listing_links = []
    deals = []
    
    with sync_playwright() as p:
        print("🚀 Step 1: Deploying Stealth Crawler to harvest property links...")
        
        # Launch Chrome with arguments that bypass bot flags
       # --- NEW PERSISTENT SHIELD REPLACEMENT ---
        import os
        user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
        
        print("Launching secure human-simulated profile...")
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            no_viewport=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        # --- END OF REPLACEMENT ---
        
        page = context.new_page()
        
        # ACTIVATE SHIELD: Apply stealth injections to the page canvas
        playwright_stealth.stealth
        
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
                    
                    deals.append({
                        "Title": title_found,
                        "Price": price_found,
                        "Link": link,
                        "Reduced": "Yes" if "reduced" in page_text_lower else "No",
                        "Keywords Found": ", ".join(matched_keywords)
                    })
            except Exception as e:
                    print(f"   ⚠️ Could not load listing details page: {e}")
                    continue
                
        context.close()
    return deals

if __name__ == "__main__":
    TARGET_SEARCH = "https://www.zoopla.co.uk/for-sale/property/liverpool/?page_size=25&sort_by=most_reduced"
    
    verified_deals = scrape_investor_deals(TARGET_SEARCH, max_listings_to_check=10)
    
    if verified_deals:
        df = pd.DataFrame(verified_deals)
        df.to_csv("distressed_property_deals.csv", index=False)
        print(f"\n📊 Strategic analysis complete! {len(verified_deals)} clean deals saved.")
        print(df)
    else:
        print("\nAnalysis cycle complete. No target keywords identified inside property description deep layers.")