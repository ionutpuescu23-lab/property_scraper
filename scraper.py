import re
import time
from pathlib import Path
import tomllib
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright
from supabase import create_client, Client


# =========================
# SUPABASE SETUP
# =========================

secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"

with open(secrets_path, "rb") as f:
    secrets = tomllib.load(f)

SUPABASE_URL = secrets.get("SUPABASE_URL")
SUPABASE_KEY = secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .streamlit/secrets.toml")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================
# TARGET AREAS - UK WIDE (MAX PRICE £70,000)
# =========================

# Fixed: Mapped exact internal Rightmove location identifier codes
RIGHTMOVE_REGIONS = {
    "Liverpool": "REGION%5E813",
    "Wirral": "REGION%5E1443",
    "Manchester": "REGION%5E904",
    "Leeds": "REGION%5E724",
    "Sheffield": "REGION%5E1196",
    "Birmingham": "REGION%5E152",
    "Nottingham": "REGION%5E1019",
    "Newcastle": "REGION%5E984",
    "Cardiff": "REGION%5E271",
    "Glasgow": "REGION%5E550"
}

SEARCH_TARGETS = []

# Build Rightmove Targets with maxPrice=70000
for area, region_code in RIGHTMOVE_REGIONS.items():
    SEARCH_TARGETS.append({
        "portal": "Rightmove",
        "region": "United Kingdom",
        "area": area,
        "url": f"https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier={region_code}&maxPrice=70000&sortType=6&includeSSTC=false"
    })

TARGET_SEARCHES = {
    "Liverpool": {
        "rightmove": "https://www.rightmove.co.uk/property-for-sale/Liverpool.html",
        "onthemarket": "https://www.onthemarket.com/for-sale/property/liverpool/",
        "zoopla": "https://www.zoopla.co.uk/for-sale/property/liverpool/"
    },

    "Wirral": {
        "rightmove": "https://www.rightmove.co.uk/property-for-sale/Wirral.html",
        "onthemarket": "https://www.onthemarket.com/for-sale/property/wirral/",
        "zoopla": "https://www.zoopla.co.uk/for-sale/property/wirral/"
    },

    "Manchester": {
        "rightmove": "https://www.rightmove.co.uk/property-for-sale/Manchester.html",
        "onthemarket": "https://www.onthemarket.com/for-sale/property/manchester/",
        "zoopla": "https://www.zoopla.co.uk/for-sale/property/manchester/"
    },

    "Leeds": {
        "rightmove": "https://www.rightmove.co.uk/property-for-sale/Leeds.html",
        "onthemarket": "https://www.onthemarket.com/for-sale/property/leeds/",
        "zoopla": "https://www.zoopla.co.uk/for-sale/property/leeds/"
    },

    "Sheffield": {
        "rightmove": "https://www.rightmove.co.uk/property-for-sale/Sheffield.html",
        "onthemarket": "https://www.onthemarket.com/for-sale/property/sheffield/",
        "zoopla": "https://www.zoopla.co.uk/for-sale/property/sheffield/"
    }
}
AUCTION_SOURCES = [
    "https://www.sdlauctions.co.uk",
    "https://www.auctionhouse.co.uk",
    "https://www.pattinson.co.uk/auctions",
    "https://www.barnardmarcusauctions.co.uk"
]

DEAL_KEYWORDS = [
    "auction",
    "renovation",
    "refurbishment",
    "refurb",
    "modernisation",
    "modernization",
    "project",
    "yield",
    "tenant",
    "tenanted",
    "reduced",
    "price drop",
    "investment",
    "development",
    "potential",
    "cash buyers",
    "in need of",
    "needs work",
    "requires work",
    "no onward chain",
]


# =========================
# DATABASE SAVE
# =========================

def save_deal_to_supabase(deal_data: dict):
    try:
        supabase.table("property_deals").upsert(
            deal_data,
            on_conflict="link"
        ).execute()

        print("      ✅ Saved/updated in Supabase")

    except Exception as e:
        print(f"      ⚠️ Database save error: {e}")


# =========================
# EXTRACT HELPERS
# =========================

def extract_links(page, portal):
    all_links = page.locator("a").evaluate_all(
        "elements => elements.map(el => el.href)"
    )

    listing_links = []

    for href in all_links:
        if not href:
            continue

        if portal == "Rightmove":
            if "/properties/" in href and "find.html" not in href:
                clean_link = href.split("?")[0].split("#")[0]

                if clean_link not in listing_links:
                    listing_links.append(clean_link)
        elif portal == "OnTheMarket":
            if "/details/" in href and "onthemarket.com" in href:
                clean_link = href.split("?")[0].split("#")[0]
                if clean_link not in listing_links:
                    listing_links.append(clean_link)

    return listing_links


def extract_image(page):
    image_selectors = [
        "meta[property='og:image']",
        ".gallery-main-img img",
        "picture img",
        "img"
    ]

    for selector in image_selectors:
        try:
            element = page.locator(selector).first

            if selector.startswith("meta"):
                img_url = element.get_attribute("content")
            else:
                if not element.is_visible():
                    continue

                img_url = element.get_attribute("src")

            if img_url and not img_url.startswith("data:"):
                return img_url

        except Exception:
            continue

    return "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=800&q=80"


def extract_description(page):
    desc_selectors = [
        "[itemprop='description']",
        "section:has(h2:has-text('Description'))",
        "div:has-text('Description')",
        "section._3OUu9W5w07n0Z-N4sM499f"
    ]

    for selector in desc_selectors:
        try:
            element = page.locator(selector).first

            if element.is_visible():
                text = element.text_content().strip()

                if len(text) > 80:
                    return text

        except Exception:
            continue

    return ""


def extract_price(clean_segments):
    text = " ".join(clean_segments)

    patterns = [
    # 1. Matches "Guide Price £70,000" or "Guide Price 70000"
    r"Guide Price\s*£?\s*[0-9,]+",
    # 2. Matches "Offers Over £70,000" or "Offers Over 70000"
    r"Offers Over\s*£?\s*[0-9,]+",
    # 3. Matches explicit prices over £10k with commas (e.g., £70,000) but stops at spaces/lines
    r"£\s?[1-9][0-9]{1,2},[0-9]{3}(?!\d)",
    # 4. Fallback for clean flat numbers like £70000
    r"£\s?[1-9][0-9]{3,6}(?!\d)",
]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0).strip()

    return "Price not available"


def extract_title(clean_segments, portal, area):
    for segment in clean_segments:
        lower = segment.lower()

        if any(word in lower for word in ["house", "terrace", "apartment", "bungalow"]):
            if len(segment) < 150:
                return segment.strip().title()

    return f"{area} Investment Property - {portal}"


def calculate_deal_score(matched_keywords):
    scoring_rules = {
        "auction": 5,
        "renovation": 5,
        "refurbishment": 5,
        "refurb": 4,
        "modernisation": 4,
        "modernization": 4,
        "in need of": 4,
        "needs work": 4,
        "requires work": 4,
        "project": 3,
        "yield": 3,
        "investment": 3,
        "development": 3,
        "tenant": 2,
        "tenanted": 2,
        "reduced": 2,
        "price drop": 2,
        "cash buyers": 2,
        "no onward chain": 1,
        "potential": 1,
    }

    return sum(scoring_rules.get(keyword, 0) for keyword in matched_keywords)


def is_price_under_threshold(price_text: str, max_threshold: int = 70000) -> bool:
    """Verifies extracted numeric contents fall cleanly below target ceiling parameters."""
    try:
        clean_numeric_string = re.sub(r"[^\d]", "", price_text)
        if not clean_numeric_string:
            return False
        
        numeric_price = int(clean_numeric_string)
        return numeric_price <= max_threshold
    except Exception:
        return False


# =========================
# COUNCIL INTELLIGENCE
# =========================

COUNCIL_INFO = {
    "Liverpool": {
        "council_name": "Liverpool City Council",
        "empty_home_signal": "Empty homes programme active",
        "grant_available": "Yes",
        "council_source_url": "https://liverpool.gov.uk/housing/report-housing-standards-and-conditions/empty-homes/",
        "council_notes": "Council operates empty homes programme. Useful as area-level investment signal only."
    },
    "Wirral": {
        "council_name": "Wirral Council",
        "empty_home_signal": "Empty property reporting active",
        "grant_available": "Unknown",
        "council_source_url": "https://www.wirral.gov.uk/housing/information-and-advice/empty-properties",
        "council_notes": "Council accepts reports of empty properties. Useful as area-level investment signal only."
    },
    "Manchester": {
        "council_name": "Manchester City Council",
        "empty_home_signal": "Council empty homes intelligence to verify",
        "grant_available": "Unknown",
        "council_source_url": "",
        "council_notes": "Council information not yet linked. Add official source later."
    },
    "Leeds": {
        "council_name": "Leeds City Council",
        "empty_home_signal": "Council empty homes intelligence to verify",
        "grant_available": "Unknown",
        "council_source_url": "",
        "council_notes": "Council information not yet linked. Add official source later."
    },
    "Sheffield": {
        "council_name": "Sheffield City Council",
        "empty_home_signal": "Council empty homes intelligence to verify",
        "grant_available": "Unknown",
        "council_source_url": "",
        "council_notes": "Council information not yet linked. Add official source later."
    },
    "Birmingham": {
        "council_name": "Birmingham City Council",
        "empty_home_signal": "Council empty homes intelligence to verify",
        "grant_available": "Unknown",
        "council_source_url": "",
        "council_notes": "Council information not yet linked. Add official source later."
    },
    "Nottingham": {
        "council_name": "Nottingham City Council",
        "empty_home_signal": "Council empty homes intelligence to verify",
        "grant_available": "Unknown",
        "council_source_url": "",
        "council_notes": "Council information not yet linked. Add official source later."
    },
    "Newcastle": {
        "council_name": "Newcastle City Council",
        "empty_home_signal": "Council empty homes intelligence to verify",
        "grant_available": "Unknown",
        "council_source_url": "",
        "council_notes": "Council information not yet linked. Add official source later."
    },
    "Cardiff": {
        "council_name": "Cardiff Council",
        "empty_home_signal": "Council empty homes intelligence to verify",
        "grant_available": "Unknown",
        "council_source_url": "",
        "council_notes": "Council information not yet linked. Add official source later."
    },
    "Glasgow": {
        "council_name": "Glasgow City Council",
        "empty_home_signal": "Council empty homes intelligence to verify",
        "grant_available": "Unknown",
        "council_source_url": "",
        "council_notes": "Council information not yet linked. Add official source later."
    },
}


def get_council_field(area, field_name):
    return COUNCIL_INFO.get(area, {}).get(field_name, "")


# =========================
# MAIN SCRAPER
# =========================

def scrape_target(target, max_listings_to_check=20):
    portal = target["portal"]
    region = target["region"]
    area = target["area"]
    search_url = target["url"]

    print(f"\n🚀 Searching {portal} | {area}, {region}")

    with sync_playwright() as p:
        profile_dir = Path(__file__).parent / f"chrome_{portal.lower()}_{area.lower().replace(' ', '_')}_profile"

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            no_viewport=True,
            args=[
                "--start-maximized",
                "--disable-infobars"
            ]
        )
        

        page = context.pages[0] if context.pages else context.new_page()

        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

            try:
                cookie = page.locator(
                    "button:has-text('Accept'), "
                    "button:has-text('Agree'), "
                    "#onetrust-accept-btn-handler, "
                    "#optInText"
                ).first

                if cookie.is_visible():
                    cookie.click()
                    time.sleep(2)

            except Exception:
                pass

            # Fixed: Conditional selector wait thresholds mapped precisely per portal
            try:
                if portal == "Rightmove":
                    page.wait_for_selector(".propertyCard-properties", timeout=10000)
                elif portal == "OnTheMarket":
                    page.wait_for_selector(".property-card", timeout=10000)
            except Exception:
                pass

            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            time.sleep(3)

            listing_links = extract_links(page, portal)

            print(f"   📊 Found {len(listing_links)} listing links")

            links_to_check = listing_links[:max_listings_to_check]

            for index, link in enumerate(links_to_check, 1):
                print(f"   [{index}/{len(links_to_check)}] Checking listing...")

                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(3)

                    image_url = extract_image(page)
                    description = extract_description(page)

                    content_elements = page.locator(
                        "h1, h2, h3, p, span, li"
                    ).all_text_contents()

                    clean_segments = [
                        text.strip()
                        for text in content_elements
                        if text and 2 < len(text.strip()) < 1000
                    ]

                    full_text = " ".join(clean_segments)
                    full_text_lower = full_text.lower()

                    if not description:
                        possible_descriptions = [
                            text for text in clean_segments
                            if len(text) > 100
                        ]

                        description = possible_descriptions[0] if possible_descriptions else "Description not available."

                    matched_keywords = [
                        keyword for keyword in DEAL_KEYWORDS
                        if keyword in full_text_lower
                    ]

                    if not matched_keywords:
                        print("      Skipped: no investor keywords found")
                        continue

                    # Fixed: Integrated backend data ceiling filter verification block
                    price = extract_price(clean_segments)
                    if not is_price_under_threshold(price, max_threshold=70000):
                        print(f"      Skipped: Price {price} exceeds £70k maximum allocation limit.")
                        continue

                    print("      📸 Using original property image URL")

                    title = extract_title(clean_segments, portal, area)
                    deal_score = calculate_deal_score(matched_keywords)

                    reduced = "Yes" if any(
                        word in full_text_lower
                        for word in ["reduced", "price drop", "dropped", "was £", "now £"]
                    ) else "No"

                    deal_data = {
                        "title": title,
                        "price": price,
                        "description": description,
                        "image_url": image_url,
                        "link": link,
                        "portal": portal,
                        "region": region,
                        "area": area,
                        "reduced": reduced,
                        "keywords_found": ", ".join(matched_keywords),
                        "deal_score": deal_score,
                        "council_name": get_council_field(area, "council_name"),
                        "empty_home_signal": get_council_field(area, "empty_home_signal"),
                        "grant_available": get_council_field(area, "grant_available"),
                        "council_source_url": get_council_field(area, "council_source_url"),
                        "council_notes": get_council_field(area, "council_notes"),
                        "source_type": "on_market"
                    }

                    print(
                        f"      🎉 Deal found: {price} | "
                        f"Score: {deal_score} | "
                        f"{', '.join(matched_keywords[:4])}"
                    )

                    save_deal_to_supabase(deal_data)

                except Exception as e:
                    print(f"      ⚠️ Listing error: {e}")

        except Exception as e:
            print(f"   ⚠️ Search page error: {e}")

        context.close()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    print("⚡ UK PROPERTY INVESTOR SCRAPER ACTIVE ⚡")
    print("Coverage: United Kingdom")

    for target in SEARCH_TARGETS:
        scrape_target(target, max_listings_to_check=20)

    print("\n🎉 Finished. Check your Supabase property_deals table.")