-- Run this once in the Supabase SQL editor (Project > SQL Editor > New query).
-- Supports the "Back on Market" and "Slow Burn" (90+ days, repeated price
-- reductions) motivated-seller signals in scraper.py.

alter table property_deals
  add column if not exists listed_date date,
  add column if not exists days_on_market integer,
  add column if not exists price_reduction_count integer default 0,
  add column if not exists back_on_market boolean default false;
