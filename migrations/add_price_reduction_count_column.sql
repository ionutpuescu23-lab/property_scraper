-- Run this once in the Supabase SQL editor.
-- price_reduction_count was missing from the schema that was actually applied
-- for migrations/add_listing_age_columns.sql (that migration also renamed
-- back_on_market to is_back_on_market and added back_on_market_reason -
-- scraper.py has been updated to match).

alter table property_deals
  add column if not exists price_reduction_count integer default 0;
