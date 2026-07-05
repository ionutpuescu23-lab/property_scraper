import os
import re
import time
from pathlib import Path
import tomllib

import psutil
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from supabase import create_client, Client

# Automatically load local .env definitions if present
load_dotenv()

# =========================
# SUPABASE SETUP
# =========================

secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"

secrets = {}
if secrets_path.exists():
    with open(secrets_path, "rb") as f:
        try:
            secrets = tomllib.load(f)
        except Exception:
            pass

SUPABASE_URL = secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
SUPABASE_KEY = secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY configuration credentials.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================
# TARGET AREAS - UK WIDE MAX PRICE £40,000
# =========================


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
    "Glasgow": "REGION%5E550",
}

SEARCH_TARGETS = [
    {
        "portal": "Rightmove",
        "region": "United Kingdom",
        "area": area,
        "url": (
            "https://www.rightmove.co.uk/property-for-sale/find.html"
            f"?locationIdentifier={region_code}"
            "&maxPrice=40000&sortType=6&includeSSTC=false"
        ),
    }
    for area, region_code in RIGHTMOVE_REGIONS.items()
]

DEAL_KEYWORDS = [
    "auction", "renovation", "refurbishment", "refurb", "modernisation",
    "modernization", "project", "yield", "tenant", "tenanted", "reduced",
    "price drop", "investment", "development", "potential", "cash buyers",
    "in need of", "needs work", "requires work", "no onward chain",
]

COUNCIL_INFO = {
    "Liverpool": {
        "council_name": "Liverpool City Council",
        "empty_home_signal": "Empty homes programme active",
        "grant_available": "Yes",
        "council_source_url": "https://liverpool.gov.uk/housing/report-housing-standards-and-conditions/empty-homes/",
        "council_notes": "Council operates empty homes programme. Useful as area-level investment signal only.",
    },    "Wirral": {
        "council_name": "Wirral Council",
        "empty_home_signal": "Empty property reporting active",
        "grant_available": "Unknown",
        "council_source_url": "https://www.wirral.gov.uk/housing/information-and-advice/empty-properties",
        "council_notes": "Council accepts reports of empty properties. Useful as area-level investment signal only.",
    },
}

def get_council_field(area: str, field_name: str) -> str:
    return COUNCIL_INFO.get(area, {}).get(field_name, "")


# =========================
# DATABASE SAVE
# =========================
def save_deal_to_supabase(deal_data: dict) -> None:
    try:
        supabase.table("property_deals").upsert(
            deal_data,
            on_conflict="link",
        ).execute()

        print("      ✅ Saved/updated in Supabase")

    except Exception as e:
        print(f"      ⚠️ Database save error: {e}")


# =========================
# EXTRACT HELPERS
# =========================
def extract_links(page, portal: str) -> list[str]:
    try:
        # Give the links half a second to anchor securely in DOM
        page.wait_for_timeout(500)
        all_links = page.locator("a").evaluate_all("elements => elements.map(el => el.href)")
    except Exception:
        return []

    listing_links: list[str] = []
    for href in all_links:
        if not href:
            continue

        clean_link = href.split("?")[0].split("#")[0]

        if portal == "Rightmove" and "/properties/" in href and "find.html" not in href:
            if clean_link not in listing_links:
                listing_links.append(clean_link)

        elif portal == "OnTheMarket" and "/details/" in href and "onthemarket.com" in href:
            if clean_link not in listing_links:
                listing_links.append(clean_link)

    return listing_links


def extract_image(page) -> str:
    image_selectors = [
        "meta[property='og:image']",
        ".gallery-main-img img",
        "picture img",
        "img",
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


def extract_description(page, clean_segments: list[str]) -> str:
    desc_selectors = [
        "[itemprop='description']",
        "section:has(h2:has-text('Description'))",
        "div:has-text('Description')",
        "section._3OUu9W5w07n0Z-N4sM499f",
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

    possible_descriptions = [text for text in clean_segments if len(text) > 100]
    return possible_descriptions[0] if possible_descriptions else "Description not available."


def extract_price(clean_segments: list[str]) -> str:
    text = " ".join(clean_segments)

    patterns = [
        r"Guide Price\s*£?\s*[0-9,]+",
        r"Offers Over\s*£?\s*[0-9,]+",
        r"£\s?[1-9][0-9]{1,2},[0-9]{3}(?!\d)",
        r"£\s?[1-9][0-9]{3,6}(?!\d)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0).strip()

    return "Price not available"

def extract_title(page, clean_segments: list[str], portal: str, area: str) -> str:
    # Rightmove/OnTheMarket set an accurate per-listing og:title; page chrome
    # (nav links like "Sold House Prices") pollutes clean_segments and used to
    # get picked up as the title instead of the real listing heading.
    try:
        og_title = page.locator("meta[property='og:title']").first.get_attribute("content")
        if og_title:
            cleaned = og_title.split(" | ")[0].split(" - Rightmove")[0].strip()
            cleaned = re.sub(r"^Check out this\s+", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s+on Rightmove$", "", cleaned, flags=re.IGNORECASE)
            if cleaned:
                return cleaned[0].upper() + cleaned[1:]
    except Exception:
        pass

    try:
        h1_text = page.locator("h1").first.text_content()
        if h1_text and len(h1_text.strip()) > 3:
            return h1_text.strip()
    except Exception:
        pass

    for segment in clean_segments:
        lower = segment.lower()
        if any(word in lower for word in ["house", "terrace", "bungalow"]): # removed apartment/flat
            if len(segment) < 150:
                return segment.strip().title()

    return f"{area} Investment Property - {portal}"



def extract_postcode(text: str) -> str:
    postcode_pattern = r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b"
    match = re.search(postcode_pattern, text.upper())
    return match.group(0).strip() if match else ""


def extract_address(clean_segments: list[str], postcode: str) -> str:
    if not postcode:
        return ""

    postcode_upper = postcode.upper().replace(" ", "")
    for segment in clean_segments:
        compact = segment.upper().replace(" ", "")
        if postcode_upper in compact and len(segment) < 200:
            return segment.strip()

    return ""


def extract_street(address: str) -> str:
    if not address:
        return ""
    street = re.sub(r"^\s*\d+[A-Z]?\s+", "", address.strip(), flags=re.IGNORECASE)
    return street


def calculate_deal_score(matched_keywords: list[str]) -> int:
    scoring_rules = {
        "auction": 5, "renovation": 5, "refurbishment": 5, "refurb": 4,
        "modernisation": 4, "modernization": 4, "in need of": 4, "needs work": 4,
        "requires work": 4, "project": 3, "yield": 3, "investment": 3,
        "development": 3, "tenant": 2, "tenanted": 2, "reduced": 2,
        "price drop": 2, "cash buyers": 2, "no onward chain": 1, "potential": 1,
    }

    return sum(scoring_rules.get(keyword, 0) for keyword in matched_keywords)



def is_price_under_threshold(price_text: str, max_threshold: int = 40000) -> bool:

    try:
        clean_numeric_string = re.sub(r"[^\d]", "", price_text)
        if not clean_numeric_string:
            return False
        
        numeric_price = int(clean_numeric_string)
        return numeric_price <= max_threshold
    except Exception:
        return False





def kill_stale_profile_processes(profile_dir: Path) -> None:
    """Kill leftover Chrome processes still holding a lock on this profile dir.

    A crashed or forcibly-killed prior run (e.g. a scheduled task terminated
    mid-execution) can leave orphaned chrome.exe processes bound to a specific
    .chromium_profiles/<region> directory, which then blocks the next
    launch_persistent_context() call for that same region.
    """
    profile_str = str(profile_dir).lower()
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            if "chrome" not in name:
                continue
            cmdline = " ".join(proc.info["cmdline"] or []).lower()
            if profile_str in cmdline:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


# =========================
# MAIN SCRAPER
# =========================
def scrape_target(target: dict, max_listings_to_check: int = 20) -> None:
    portal = target["portal"]
    region = target["region"]
    area = target["area"]
    search_url = target["url"]

    print(f"\n🚀 Searching {portal} | {area}, {region}")

    # Explicitly pull user profile folders into a hidden workspace folder
    profile_dir = Path(__file__).parent / ".chromium_profiles" / f"{portal.lower()}_{area.lower().replace(' ', '_')}"
    profile_dir.parent.mkdir(exist_ok=True)

    kill_stale_profile_processes(profile_dir)

    with sync_playwright() as p:
        # Launching with dedicated unique profile locations to stop file collisions
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            no_viewport=True,
            args=["--start-maximized", "--disable-infobars"],
        )


        page = context.pages[0] if context.pages else context.new_page()

        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            # Accept Cookie walls smoothly
            try:
                cookie = page.locator(
                    "button:has-text('Accept'), "
                    "button:has-text('Agree'), "
                    "#onetrust-accept-btn-handler, "
                    "#optInText"
                ).first

                if cookie.is_visible():
                    cookie.click()
                    page.wait_for_timeout(1500)
            except Exception:
                pass


            try:

                if portal == "Rightmove":
                    page.wait_for_selector("a[href*='/properties/']", timeout=15000)
                elif portal == "OnTheMarket":
                    page.wait_for_selector("a[href*='/details/']", timeout=15000)
            except Exception:
                pass

            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            page.wait_for_timeout(2000)

            listing_links = extract_links(page, portal)
            print(f"    📊 Found {len(listing_links)} listing links")

            links_to_check = listing_links[:max_listings_to_check]

            for index, link in enumerate(links_to_check, 1):
                print(f"   [{index}/{len(links_to_check)}] Checking listing...")

                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(2500)

                    content_elements = page.locator("h1, h2, h3, p, span, li").all_text_contents()
                    clean_segments = [
                        text.strip()
                        for text in content_elements
                        if text and 2 < len(text.strip()) < 1000
                    ]

                    full_text = " ".join(clean_segments)
                    full_text_lower = full_text.lower()

                    # 🚫 EXCLUDE FLATS AND APARTMENTS (Enhanced)
                    excluded_words = ["flat", "apartment", "maisonette", "studio", "block of", "plots"]
                    if any(word in full_text_lower for word in excluded_words) or any(word in link.lower() for word in ["flat", "apartment"]):
                        print("      Skipped: Excluded property type (Flat/Apartment)")
                        continue

                    matched_keywords = [keyword for keyword in DEAL_KEYWORDS if keyword in full_text_lower]
                    if not matched_keywords:
                        print("      Skipped: no investor keywords found")
                        continue


                    price = extract_price(clean_segments)
                    if not is_price_under_threshold(price, max_threshold=40000):
                        print(f"      Skipped: Price {price} exceeds £40k allocation limit.")
                        continue

                    image_url = extract_image(page)
                    description = extract_description(page, clean_segments)
                    title = extract_title(page, clean_segments, portal, area)
                    deal_score = calculate_deal_score(matched_keywords)

                    postcode = extract_postcode(full_text)
                    address = extract_address(clean_segments, postcode)
                    street = extract_street(address)

                    reduced = "Yes" if any(
                        word in full_text_lower
                        for word in ["reduced", "price drop", "dropped", "was £", "now £"]
                    ) else "No"

                    deal_data = {
                        "title": title,
                        "price": price,
                        "description": description,
                        "address": address,
                        "postcode": postcode,
                        "street": street,
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
                        "source_type": "on_market",
                    }

                    print(f"      🎉 Deal found: {price} | Score: {deal_score} | Postcode: {postcode or 'N/A'}")
                    save_deal_to_supabase(deal_data)

                except Exception as e:
                    print(f"      ⚠️ Listing error: {e}")

        except Exception as e:
            print(f"   ⚠️ Search page error: {e}")

        finally:
            # CRITICAL FIX: Shuts down context AND kills background browser processes to drop directory locks
            context.close()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    print("⚡ UK PROPERTY INVESTOR SCRAPER ACTIVE ⚡")
    print("Coverage: United Kingdom | Allocation Limit: £70,000")

    for target in SEARCH_TARGETS:
        scrape_target(target, max_listings_to_check=20)

    print("\n🎉 Finished. Check your Supabase property_deals table.")