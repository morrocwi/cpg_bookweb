-- cpg_bookweb · Supabase schema for the "ห้องสมุดสบายๆ" library
-- Apply via: Supabase SQL editor, the supabase MCP, or `psql`.
-- The website reads this table with the public anon key (RLS allows SELECT only).
-- Writes are done by the sync job using the service-role key (bypasses RLS).

create table if not exists public.articles (
  id           text primary key,            -- slug, e.g. 'pr-002'
  cat          text not null,               -- about | philosophy | equation | principle
  title        text not null,               -- Thai display title
  excerpt      text,
  body_html    text,
  tags         text[] default '{}',
  read_minutes int  default 1,
  featured     boolean default false,
  source       text,                        -- provenance path inside cpg_book
  source_id    text,                        -- original id (PR-002, EQ-PRF-01, README, ...)
  lang         text default 'th',
  sort         int  default 999,
  created_at   timestamptz default now(),
  updated_at   timestamptz default now()
);

create index if not exists articles_cat_idx  on public.articles (cat);
create index if not exists articles_sort_idx on public.articles (sort);

-- keep updated_at fresh on upsert
create or replace function public.touch_updated_at() returns trigger as $$
begin new.updated_at = now(); return new; end; $$ language plpgsql;

drop trigger if exists articles_touch on public.articles;
create trigger articles_touch before update on public.articles
  for each row execute function public.touch_updated_at();

-- public, read-only access for the website
alter table public.articles enable row level security;
drop policy if exists "public read articles" on public.articles;
create policy "public read articles" on public.articles for select using (true);
