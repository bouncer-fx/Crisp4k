alter table public.profiles enable row level security;
alter table public.credits enable row level security;
alter table public.enhancements enable row level security;
alter table public.transactions enable row level security;
alter table public.subscriptions enable row level security;

create policy "own profile read" on public.profiles
  for select using (auth.uid() = id);
create policy "own profile update" on public.profiles
  for update using (auth.uid() = id) with check (auth.uid() = id);

create policy "own credits read" on public.credits
  for select using (auth.uid() = user_id);

create policy "own enhancements read" on public.enhancements
  for select using (auth.uid() = user_id);
create policy "own enhancements delete" on public.enhancements
  for delete using (auth.uid() = user_id);

create policy "own transactions read" on public.transactions
  for select using (auth.uid() = user_id);

create policy "own subscriptions read" on public.subscriptions
  for select using (auth.uid() = user_id);

create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  insert into public.credits (user_id, available_credits)
  values (new.id, 2);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
