"""
Pulls HM Land Registry's official Price Paid Data (free, open, England & Wales
only — Scotland/NI are not covered) and surfaces recent sub-£70k HOUSE sales in
target cities as off-market sourcing signals.

This is completed SALE data, not live leads: there is no vendor name/contact
in this dataset by law. Use it to spot cheap-sale streets/postcodes worth
researching further (e.g. checking who owns the property now) or as a target
list for "Dear Owner"-style direct mail — not as ready-to-call contacts.
"""

import io
from datetime import datetime, timedelta

import pandas as pd
import requests

from scraper import supabase

PPD_COLUMNS = [
    "transaction_id", "price", "date_of_transfer", "postcode",
    "property_type", "old_new", "duration", "paon", "saon",
    "street", "locality", "town_city", "district", "county",
    "ppd_category_type", "record_status",
]

MAX_PRICE = 70000
LOOKBACK_DAYS = 180

TARGET_CITIES = {
    "liverpool", "wirral", "manchester", "leeds", "sheffield",
    "birmingham", "nottingham", "newcastle upon tyne", "cardiff",
}

PROPERTY_TYPE_LABELS = {
    "D": "Detached House",
    "S": "Semi-Detached House",
    "T": "Terraced House",
}


def ppd_url_for_year(year: int) -> str:
    return f"https://price-paid-data.publicdata.landregistry.gov.uk/pp-{year}.csv"


def download_price_paid_data() -> pd.DataFrame:
    url = ppd_url_for_year(datetime.now().year)
    print(f"⬇️  Downloading Land Registry price paid data from {url} ...")
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    df = pd.read_csv(io.BytesIO(response.content), header=None, names=PPD_COLUMNS)
    df["date_of_transfer"] = pd.to_datetime(df["date_of_transfer"])
    print(f"    Loaded {len(df)} transactions")
    return df


def filter_target_deals(df: pd.DataFrame) -> pd.DataFrame:
    cutoff = datetime.now() - timedelta(days=LOOKBACK_DAYS)

    in_target_city = (
        df["district"].str.lower().isin(TARGET_CITIES)
        | df["town_city"].str.lower().isin(TARGET_CITIES)
    )
    is_house = df["property_type"].isin(PROPERTY_TYPE_LABELS.keys())
    is_affordable = df["price"] <= MAX_PRICE
    is_recent = df["date_of_transfer"] >= cutoff

    return df[in_target_city & is_house & is_affordable & is_recent]


def build_signal_record(row: pd.Series) -> dict:
    area = (row["town_city"] or row["district"] or "").title()
    property_label = PROPERTY_TYPE_LABELS.get(row["property_type"], "House")
    address_parts = [str(row["paon"]), str(row["street"]), area]
    address = ", ".join(p for p in address_parts if p and p.lower() != "nan")

    return {
        "title": f"Sold £{int(row['price']):,} - {property_label}, {area}",
        "price": f"£{int(row['price']):,}",
        "description": (
            f"HM Land Registry record: {property_label.lower()} sold "
            f"{row['date_of_transfer'].strftime('%d %b %Y')} for £{int(row['price']):,}. "
            "This is completed sale data with no vendor contact available — "
            "use as a below-market sourcing signal for further research or "
            "direct mail, not a ready-to-call lead."
        ),
        "address": address,
        "postcode": row["postcode"] if pd.notna(row["postcode"]) else "",
        "street": row["street"] if pd.notna(row["street"]) else "",
        "link": f"land-registry://{row['transaction_id']}",
        "portal": "Land Registry",
        "region": "United Kingdom",
        "area": area,
        "reduced": "No",
        "keywords_found": "land registry, below market value",
        "deal_score": round((MAX_PRICE - row["price"]) / 1000),
        "source_type": "off_market",
        "image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=800&q=80",
    }


def save_signals(df: pd.DataFrame) -> None:
    saved = 0
    for _, row in df.iterrows():
        try:
            supabase.table("property_deals").upsert(
                build_signal_record(row), on_conflict="link"
            ).execute()
            saved += 1
        except Exception as e:
            print(f"      ⚠️ Database save error: {e}")

    print(f"✅ Saved/updated {saved} Land Registry sourcing signal(s)")


if __name__ == "__main__":
    print("⚡ LAND REGISTRY OFF-MARKET SOURCING ⚡")
    print(f"Target cities: {', '.join(sorted(TARGET_CITIES))} | Max price: £{MAX_PRICE:,} | Last {LOOKBACK_DAYS} days")

    raw = download_price_paid_data()
    targets = filter_target_deals(raw)
    print(f"    Found {len(targets)} matching sub-£{MAX_PRICE:,} house sale(s)")

    save_signals(targets)
