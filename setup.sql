-- ====================================================
-- ИИ-Империя — Database Setup for Supabase
-- Запустите этот SQL в Supabase → SQL Editor
-- ====================================================

-- Employees table
create table if not exists employees (
    id           uuid primary key default gen_random_uuid(),
    name         text not null,
    role         text not null,
    department   text default 'other',
    avatar_emoji text default '👤',
    status       text default 'active',
    hired_by     uuid references employees(id) on delete set null,
    system_prompt text,
    created_at   timestamptz default now()
);

-- Tasks table
create table if not exists tasks (
    id          uuid primary key default gen_random_uuid(),
    title       text not null,
    description text,
    assigned_to uuid references employees(id) on delete set null,
    created_by  text default 'owner',
    status      text default 'todo'
                    check (status in ('todo', 'in_progress', 'done')),
    priority    text default 'medium'
                    check (priority in ('low', 'medium', 'high')),
    created_at  timestamptz default now(),
    updated_at  timestamptz default now()
);

-- Messages (chat history per employee)
create table if not exists messages (
    id          uuid primary key default gen_random_uuid(),
    employee_id uuid references employees(id) on delete cascade,
    role        text not null check (role in ('user', 'assistant')),
    content     text not null,
    created_at  timestamptz default now()
);

-- Content items (generated content history)
create table if not exists content_items (
    id         uuid primary key default gen_random_uuid(),
    type       text not null, -- script, post, article, carousel
    topic      text,
    platform   text,
    content    text not null,
    created_at timestamptz default now()
);

-- Enable Row Level Security
alter table employees     enable row level security;
alter table tasks         enable row level security;
alter table messages      enable row level security;
alter table content_items enable row level security;

-- Allow full access with anon key (personal tool — no auth needed)
create policy "anon_all_employees"     on employees     for all using (true) with check (true);
create policy "anon_all_tasks"         on tasks         for all using (true) with check (true);
create policy "anon_all_messages"      on messages      for all using (true) with check (true);
create policy "anon_all_content_items" on content_items for all using (true) with check (true);
