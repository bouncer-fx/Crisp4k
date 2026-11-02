create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  username text,
  created_at timestamptz not null default now()
);

create table public.credits (
  user_id uuid primary key references auth.users(id) on delete cascade,
  available_credits integer not null default 2 check (available_credits >= 0),
  updated_at timestamptz not null default now()
);

create table public.enhancements (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  original_path text not null,
  enhanced_path text,
  enhancement_mode text not null check (enhancement_mode in ('standard','pro','4k')),
  status text not null default 'PENDING'
    check (status in ('PENDING','UPLOADING','PROCESSING','COMPLETED','FAILED')),
  processing_time numeric,
  created_at timestamptz not null default now()
);

create table public.transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  payment_reference text not null unique,
  amount integer not null,
  currency text not null default 'GHS',
  status text not null default 'PENDING',
  created_at timestamptz not null default now()
);

create table public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  plan text not null,
  status text not null default 'ACTIVE',
  expires_at timestamptz
);
