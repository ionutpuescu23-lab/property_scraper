import requests
import json
import time

def load_off_market_deals(records):
    """Loops through manual or offline property leads and streams them to the API engine."""
    backend_url = "http://127.0.0.1:8000/api/v1/deals/ingest"
    
    print(f"📦 Initiating batch upload for {len(records)} off-market vendor records...")
    
    for idx, record in enumerate(records, 1):
        print(f"[{idx}/{len(records)}] Processing: {record['title']}...")
        
        # Formulate payload targeting the strict direct-to-vendor email logic
        payload = {
            "title": record["title"],
            "price": record["price"],
            "link": record["link"],
            "reduced": False,  # Off-market properties usually don't have portal "reduction" tags
            "keywords_found": record.get("keywords", "off-market lead"),
            "source_type": "off_market"  # 🔥 Crucial switch: Activates Strategy B outreach
        }
        
        try:
            response = requests.post(backend_url, json=payload)
            if response.status_code == 200:
                print(f"   📡 Synchronized: {record['title']} mapped directly to vendor track.")
            else:
                print(f"   ⚠️ API Rejected Record: {response.text}")
        except Exception as e:
            print(f"   ⚠️ Connection Failed to Backend: {e}")
            
        # Short breather between uploads to respect email server limits
        time.sleep(1.5)

if __name__ == "__main__":
    # Mock data sample: Imagine reading this out of a CSV spreadsheet or council document
    # NOTE: The link MUST be a valid URL structure to pass Pydantic validation (e.g. your website domain)
    sample_csv_data = [
        {
            "title": "3 Bed Terrace - Anfield, Liverpool",
            "price": "£85,000",
            "link": "https://puescupropertiesltd.com/leads/anfield-01",
            "keywords": "absentee landlord, empty home"
        },
        {
            "title": "Semi-Detached Project - Birkenhead, Wirral",
            "price": "£110,000",
            "link": "https://puescupropertiesltd.com/leads/wirral-02",
            "keywords": "probate lead, tlc needed"
        }
    ]
    
    print("\n⚡ Starting Off-Market Batch Ingestion ⚡")
    load_off_market_deals(sample_csv_data)
    print("\n🎉 Batch Upload Complete!")