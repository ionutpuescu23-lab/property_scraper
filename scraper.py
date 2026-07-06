import os
import re
import time
from datetime import datetime
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
# TARGET AREAS - UK WIDE MAX PRICE £70,000
# =========================

MAX_PRICE = 70000

TARGET_AREAS = [
    "Liverpool", "Wirral", "Manchester", "Leeds", "Sheffield",
    "Birmingham", "Nottingham", "Newcastle", "Cardiff", "Glasgow",
]


def build_search_targets() -> list[dict]:
    targets = []

    for area in TARGET_AREAS:
        slug = area.lower().replace(" ", "-")
        targets.append({
            "portal": "Zoopla",
            "region": "United Kingdom",
            "area": area,
            "url": f"https://www.zoopla.co.uk/for-sale/property/{slug}/?price_max={MAX_PRICE}&q={area}",
        })
        targets.append({
            "portal": "OnTheMarket",
            "region": "United Kingdom",
            "area": area,
            "url": f"https://www.onthemarket.com/for-sale/property/{slug}/?max-price={MAX_PRICE}",
        })

    return targets


SEARCH_TARGETS = build_search_targets()

SOLD_STATUS_PHRASES = [
    "sold subject to contract",
    "sold stc",
    "sstc",
    "under offer",
    "sold, further details",
    "no longer being marketed",
    "property is no longer available",
]

# A motivated-seller signal, not a status to skip - checked BEFORE
# SOLD_STATUS_PHRASES so "no longer under offer" doesn't get wrongly
# excluded by the bare "under offer" substring check.
BACK_ON_MARKET_PHRASES = [
    "back on the market", "back on market", "chain broken", "chain has broken",
    "sale fell through", "previous sale fell through", "no longer under offer",
    "buyer pulled out", "buyer withdrew",
]

DEAL_KEYWORDS = [
    "renovation", "refurbishment", "refurb", "modernisation",
    "modernization", "project", "yield", "tenant", "tenanted", "reduced",
    "price drop", "investment", "development", "potential", "cash buyers",
    "in need of", "needs work", "requires work", "no onward chain",
] + BACK_ON_MARKET_PHRASES

# 90-120+ days on market is the "slow burn" motivated-seller signal
SLOW_BURN_DAYS_THRESHOLD = 90

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

        if portal == "OnTheMarket" and "/details/" in href and "onthemarket.com" in href:
            if clean_link not in listing_links:
                listing_links.append(clean_link)

        elif portal == "Zoopla" and "/for-sale/details/" in href and "/contact/" not in href:
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


def calculate_deal_score(
    matched_keywords: list[str],
    days_on_market: int | None = None,
    price_reduction_count: int = 0,
) -> int:
    scoring_rules = {
        "renovation": 5, "refurbishment": 5, "refurb": 4,
        "modernisation": 4, "modernization": 4, "in need of": 4, "needs work": 4,
        "requires work": 4, "project": 3, "yield": 3, "investment": 3,
        "development": 3, "tenant": 2, "tenanted": 2, "reduced": 2,
        "price drop": 2, "cash buyers": 2, "no onward chain": 1, "potential": 1,
        "back on the market": 5, "back on market": 5, "chain broken": 5,
        "chain has broken": 5, "sale fell through": 5, "previous sale fell through": 5,
        "no longer under offer": 4, "buyer pulled out": 4, "buyer withdrew": 4,
    }

    score = sum(scoring_rules.get(keyword, 0) for keyword in matched_keywords)

    if days_on_market is not None and days_on_market >= SLOW_BURN_DAYS_THRESHOLD:
        score += 3

    score += min(price_reduction_count, 3) * 2  # up to +6 for repeated reductions

    return score


def extract_listing_age(page_text_lower: str) -> dict:
    """
    Parses "Added on DD/MM/YYYY" and counts "Reduced on DD/MM/YYYY" occurrences
    directly from a single page visit - no historical tracking needed to spot
    a stale, repeatedly-reduced "slow burn" listing.
    """
    added_match = re.search(r"added on (\d{2}/\d{2}/\d{4})", page_text_lower)
    reduction_dates = re.findall(r"reduced on (\d{2}/\d{2}/\d{4})", page_text_lower)

    listed_date = None
    days_on_market = None
    if added_match:
        try:
            listed_date = datetime.strptime(added_match.group(1), "%d/%m/%Y").date()
            days_on_market = (datetime.now().date() - listed_date).days
        except ValueError:
            pass

    return {
        "listed_date": listed_date.isoformat() if listed_date else None,
        "days_on_market": days_on_market,
        "price_reduction_count": len(reduction_dates),
    }



def is_price_under_threshold(price_text: str, max_threshold: int = MAX_PRICE) -> bool:

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

                if portal == "OnTheMarket":
                    page.wait_for_selector("a[href*='/details/']", timeout=15000)
                elif portal == "Zoopla":
                    page.wait_for_selector("a[href*='/for-sale/details/']", timeout=15000)
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

                    # h1/h2/h3/p/span/li misses text that only lives inside a <div>
                    # (e.g. "PROPERTY TYPE Apartment" widgets), which let real flats
                    # slip past the exclusion check below. Scan the whole rendered
                    # body for these two hard-block checks instead.
                    try:
                        page_text_lower = page.inner_text("body").lower()
                    except Exception:
                        page_text_lower = full_text_lower

                    # 🚫 EXCLUDE FLATS AND APARTMENTS (Enhanced)
                    excluded_words = ["flat", "apartment", "maisonette", "studio", "block of", "plots"]
                    if any(word in page_text_lower for word in excluded_words) or any(word in link.lower() for word in ["flat", "apartment"]):
                        print("      Skipped: Excluded property type (Flat/Apartment)")
                        continue

                    # 🚫 EXCLUDE SHARED OWNERSHIP
                    if "shared ownership" in page_text_lower or "shared-ownership" in link.lower():
                        print("      Skipped: Shared ownership")
                        continue

                    # 🚫 EXCLUDE AUCTIONS
                    if "auction" in page_text_lower or "auction" in link.lower():
                        print("      Skipped: Auction listing")
                        continue

                    # 🚫 EXCLUDE PARKING SPACES/GARAGES LISTED AS THE PROPERTY ITSELF
                    # ("parking" alone is too generic - it's a standard amenity field
                    # on almost every listing - so match the specific for-sale phrasing.
                    parking_phrases = ["parking space", "garage for sale", "lock-up garage"]
                    if any(phrase in page_text_lower for phrase in parking_phrases) or "parking-space" in link.lower():
                        print("      Skipped: Parking space/garage listing")
                        continue

                    # A "back on market" listing is a motivated-seller signal, not
                    # a status to skip - check first so phrases like "no longer
                    # under offer" don't trip the sold/under-offer exclusion below.
                    back_on_market_reason = next(
                        (phrase for phrase in BACK_ON_MARKET_PHRASES if phrase in page_text_lower),
                        None,
                    )
                    is_back_on_market = back_on_market_reason is not None

                    # 🚫 EXCLUDE SOLD / UNDER OFFER (backup to includeSSTC=false, which can lag)
                    if not is_back_on_market and any(phrase in page_text_lower for phrase in SOLD_STATUS_PHRASES):
                        print("      Skipped: Already sold / under offer")
                        continue

                    matched_keywords = [keyword for keyword in DEAL_KEYWORDS if keyword in full_text_lower]
                    # Back-on-market phrases can live in div-only widgets full_text_lower
                    # misses (same class of issue as the flat/apartment check above).
                    matched_keywords += [
                        phrase for phrase in BACK_ON_MARKET_PHRASES
                        if phrase in page_text_lower and phrase not in matched_keywords
                    ]
                    if not matched_keywords:
                        print("      Skipped: no investor keywords found")
                        continue


                    price = extract_price(clean_segments)
                    if not is_price_under_threshold(price):
                        print(f"      Skipped: Price {price} exceeds £{MAX_PRICE:,} allocation limit.")
                        continue

                    image_url = extract_image(page)
                    description = extract_description(page, clean_segments)
                    title = extract_title(page, clean_segments, portal, area)
                    listing_age = extract_listing_age(page_text_lower)
                    deal_score = calculate_deal_score(
                        matched_keywords,
                        days_on_market=listing_age["days_on_market"],
                        price_reduction_count=listing_age["price_reduction_count"],
                    )

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
                        "listed_date": listing_age["listed_date"],
                        "days_on_market": listing_age["days_on_market"],
                        "price_reduction_count": listing_age["price_reduction_count"],
                        "is_back_on_market": is_back_on_market,
                        "back_on_market_reason": back_on_market_reason,
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
    print(f"Coverage: United Kingdom | Allocation Limit: £{MAX_PRICE:,}")

    for target in SEARCH_TARGETS:
        scrape_target(target, max_listings_to_check=20)

    print("\n🎉 Finished. Check your Supabase property_deals table.")