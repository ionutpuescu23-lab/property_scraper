@echo off
cd /d C:\Users\ionut\Desktop\property_scraper
python scraper.py
python land_registry_loader.py
python title_register_fetcher.py
python revalidate_deals.py