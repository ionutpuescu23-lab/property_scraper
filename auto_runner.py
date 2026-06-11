import time
import subprocess
import os
from datetime import datetime
import schedule

def run_property_pipeline():
    print(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 6:00 AM Trigger Activated!")
    print("🔄 Initializing Stealth Crawler execution layer...")
    
    # Run scraper.py exactly as if you typed 'python scraper.py' in the terminal
    try:
        # shell=True keeps it running safely inside your environment context
        result = subprocess.run(["python", "scraper.py"], check=True, shell=True)
        print(f"✅ Pipeline run completed successfully. CSV database refreshed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Automation runtime error occurred during scraper loop: {e}")

# ──── THE ALARM CLOCK LOGIC ────
# Schedule the task to execute precisely at 06:00 every single morning
schedule.every().day.at("06:00").do(run_property_pipeline)

print("📡 AlphaDeals Automation Engine is active and listening...")
print("💡 Keep this terminal session open. The pipeline will automatically wake up and fire at 06:00 AM daily.")

# Infinite daemon loop to keep the script continuously checking the clock
while True:
    schedule.run_pending()
    time.sleep(30)  # Check the clock every 30 seconds to be highly accurate