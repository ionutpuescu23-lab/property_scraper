import time

from playwright.sync_api import sync_playwright

from scraper import SOLD_STATUS_PHRASES, supabase


def is_stale(page) -> bool:
    try:
        page.wait_for_timeout(2000)
        text = " ".join(page.locator("h1, h2, h3, p, span, li").all_text_contents()).lower()
    except Exception:
        return False

    return any(phrase in text for phrase in SOLD_STATUS_PHRASES)


def revalidate_saved_deals() -> None:
    rows = (
        supabase.table("property_deals")
        .select("id, link")
        .eq("source_type", "on_market")
        .execute()
        .data
    )
    print(f"🔎 Re-checking {len(rows)} saved on-market deal(s) for sold/under-offer status...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )

        removed = 0
        for row in rows:
            link = row.get("link")
            if not link:
                continue

            try:
                page.goto(link, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                print(f"      ⚠️ Could not load {link}: {e}")
                continue

            if is_stale(page):
                supabase.table("property_deals").delete().eq("id", row["id"]).execute()
                removed += 1
                print(f"      🗑️ Removed (sold/under offer): {link}")

            time.sleep(1)

        browser.close()

    print(f"✅ Revalidation complete. Removed {removed} stale deal(s).")


if __name__ == "__main__":
    revalidate_saved_deals()
