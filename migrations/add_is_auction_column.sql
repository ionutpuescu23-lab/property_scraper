-- Run this once in the Supabase SQL editor.
-- Distinguishes the new dedicated auction-opportunities category (Auction
-- House NW, OnTheMarket Auctions) from the main non-auction deal flow, which
-- still excludes auctions entirely.

alter table property_deals
  add column if not exists is_auction boolean default false;
