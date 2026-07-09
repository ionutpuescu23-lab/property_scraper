-- Run this once in the Supabase SQL editor.
-- Restores public read access to the dashboard without reopening writes.
-- RLS denies everything by default once enabled unless a policy explicitly
-- allows it - this only adds a SELECT policy, so INSERT/UPDATE/DELETE for
-- the anon role stay blocked (verify no other permissive policy already
-- grants those before assuming this is fully locked down).

alter table property_deals enable row level security;

create policy "Public can view property deals"
on property_deals
for select
to anon
using (true);
