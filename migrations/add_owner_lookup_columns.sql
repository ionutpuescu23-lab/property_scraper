-- Run this once in the Supabase SQL editor (Project > SQL Editor > New query).
-- The Python client only has REST access to property_deals, not DDL rights,
-- so this can't be applied automatically from a script.

alter table property_deals
  add column if not exists owner_name text,
  add column if not exists owner_type text,
  add column if not exists contact_status text default 'New',
  add column if not exists owner_contact_info jsonb default '{}'::jsonb;
