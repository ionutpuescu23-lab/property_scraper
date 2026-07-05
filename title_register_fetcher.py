"""
Enriches Land Registry sourcing signals (property_deals rows with
portal='Land Registry') with owner information: owner_name, owner_type,
contact_status, owner_contact_info.

STATUS: Companies House enrichment (for corporate owners) works today - it's
free and only needs a COMPANIES_HOUSE_API_KEY (instant signup at
https://developer.company-information.service.gov.uk/).

Title Register lookups (the actual owner_name source) are NOT wired up yet.
HM Land Registry doesn't offer a free/bulk API for this - it costs £3 per
property and requires a signed Business Gateway agreement, not just an API
key (see https://www.gov.uk/guidance/hm-land-registry-business-gateway).
Once you have that account, fill in find_title_number() and
fetch_official_copy_register() below using your onboarding pack's docs
(https://landregistry.github.io/bgtechdoc/services/) - the exact
request/response shape depends on which service tier you're given.

Also note: Title Registers give a name and an "address for service" (usually
just the property itself) - never a phone number, and only rarely a
voluntarily-registered email. There is no compliant free/bulk source for
individual owners' personal contact details wired up here; owner_contact_info
will stay empty for individual owners unless you plug in a specific licensed
data provider you already hold an account with.
"""

import os

import requests

from scraper import supabase

MAX_LOOKUPS_PER_RUN = 50  # hard cost cap: £3 x this = max HMLR spend per run

HMLR_API_KEY = os.environ.get("HMLR_API_KEY")
HMLR_API_BASE_URL = os.environ.get("HMLR_API_BASE_URL")

COMPANIES_HOUSE_API_KEY = os.environ.get("COMPANIES_HOUSE_API_KEY")
COMPANIES_HOUSE_BASE_URL = "https://api.company-information.service.gov.uk"

CORPORATE_INDICATORS = [
    "LTD", "LIMITED", "LLP", "PLC", "INC", "CORP", "COMPANY",
    "PROPERTIES", "HOLDINGS", "INVESTMENTS", "TRUST", "COUNCIL", "ASSOCIATION",
]


def hmlr_configured() -> bool:
    return bool(HMLR_API_KEY and HMLR_API_BASE_URL)


def find_title_number(postcode: str, address: str) -> str | None:
    """
    Requires an HM Land Registry Business Gateway account (a signed agreement,
    not just an API key). See https://landregistry.github.io/bgtechdoc/services/
    for the "Find Title Number" / property search service your onboarding pack
    grants access to, and wire the real request/response here - left
    unimplemented rather than guessed at, since the exact schema depends on
    your account tier.
    """
    raise NotImplementedError(
        "find_title_number() needs HM Land Registry Business Gateway credentials - "
        "see https://www.gov.uk/guidance/hm-land-registry-business-gateway"
    )


def fetch_official_copy_register(title_number: str) -> dict | None:
    """
    Fetches the £3 Official Copy (register) for a known title number.
    See https://landregistry.github.io/bgtechdoc/services/official_copy_title_known/
    Expected to return at least {"owner_name": ...}.
    """
    raise NotImplementedError(
        "fetch_official_copy_register() needs HM Land Registry Business Gateway credentials."
    )


def classify_owner_type(owner_name: str) -> str:
    upper = owner_name.upper()
    if any(indicator in upper for indicator in CORPORATE_INDICATORS):
        return "Corporate"
    return "Individual"


def lookup_companies_house(company_name: str) -> dict | None:
    if not COMPANIES_HOUSE_API_KEY:
        return None

    try:
        response = requests.get(
            f"{COMPANIES_HOUSE_BASE_URL}/search/companies",
            params={"q": company_name, "items_per_page": 1},
            auth=(COMPANIES_HOUSE_API_KEY, ""),
            timeout=15,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return None

        company = items[0]
        return {
            "company_number": company.get("company_number"),
            "registered_office_address": company.get("address_snippet"),
            "company_status": company.get("company_status"),
        }
    except Exception as e:
        print(f"      ⚠️ Companies House lookup error: {e}")
        return None


def lookup_individual_contact_info(owner_name: str, address: str) -> dict | None:
    """
    No compliant free/bulk source for an individual's personal email or phone
    exists from Title Register data. If you hold an account with a licensed
    people-search/data provider (e.g. one you already use for direct mail
    tracing), wire it in here - deliberately not guessing at a scraping
    target for personal data.
    """
    return None


def process_land_registry_signals() -> None:
    if not hmlr_configured():
        print("⚠️  HMLR_API_KEY / HMLR_API_BASE_URL not set in .env.")
        print("    Title register lookups need a Business Gateway account: ")
        print("    https://www.gov.uk/guidance/hm-land-registry-business-gateway")
        print("    Skipping owner_name lookups this run (nothing to enrich without it).")
        return

    rows = (
        supabase.table("property_deals")
        .select("id, postcode, address, owner_name")
        .eq("portal", "Land Registry")
        .is_("owner_name", "null")
        .limit(MAX_LOOKUPS_PER_RUN)
        .execute()
        .data
    )
    print(f"🔎 {len(rows)} Land Registry signal(s) without an owner lookup yet (capped at {MAX_LOOKUPS_PER_RUN}/run, £3 each)")

    enriched = 0
    for row in rows:
        try:
            title_number = find_title_number(row["postcode"], row["address"])
            register = fetch_official_copy_register(title_number) if title_number else None
        except NotImplementedError as e:
            print(f"      ⚠️ {e}")
            break
        except Exception as e:
            print(f"      ⚠️ Title register lookup failed for id={row['id']}: {e}")
            continue

        owner_name = register.get("owner_name") if register else None
        if not owner_name:
            continue

        owner_type = classify_owner_type(owner_name)
        contact_info = {}
        contact_status = "New"

        if owner_type == "Corporate":
            ch_info = lookup_companies_house(owner_name)
            if ch_info:
                contact_info["companies_house"] = ch_info
                contact_status = "Traced"
        else:
            individual_info = lookup_individual_contact_info(owner_name, row["address"])
            if individual_info:
                contact_info.update(individual_info)
                contact_status = "Traced"

        supabase.table("property_deals").update({
            "owner_name": owner_name,
            "owner_type": owner_type,
            "contact_status": contact_status,
            "owner_contact_info": contact_info,
        }).eq("id", row["id"]).execute()

        enriched += 1
        print(f"      ✅ id={row['id']}: {owner_name} ({owner_type}) - {contact_status}")

    print(f"✅ Enriched {enriched} propert(y/ies) with owner info this run.")


if __name__ == "__main__":
    process_land_registry_signals()
