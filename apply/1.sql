-- v186e bug sweep (database part)

-- 1) PRIVACY. The website's public key (it is inside every page, so anyone has it) could read every learner's
--    email address and phone number from public.users without signing in, through the policy
--    "anyone can read public profiles" (USING true). Signed-in members keep their access through users_read_all;
--    nothing on the site reads public.users before sign-in except the sign-up phone check, which now uses
--    phone_registered() below. The same open read existed on invites (tokens and emails) and user_profiles
--    (both tables are empty and unused by the site).
drop policy if exists "anyone can read public profiles" on public.users;
drop policy if exists invites_token_read on public.invites;
drop policy if exists read_all_profiles on public.user_profiles;

create or replace function public.phone_registered(p_phone text)
returns boolean language sql stable security definer set search_path = public as $$
  select coalesce(p_phone, '') <> '' and exists (select 1 from users where phone_number = p_phone);
$$;
revoke all on function public.phone_registered(text) from public;
grant execute on function public.phone_registered(text) to anon, authenticated;

-- 2) Admin "user growth" chart: public.admin_user_growth() ran with the caller's rights and called a function in
--    the private schema, which signed-in users cannot reach, so it always failed (HTTP 403). It now runs with the
--    owner's rights; private.admin_user_growth() still refuses anyone who is not an admin.
create or replace function public.admin_user_growth()
returns jsonb language sql stable security definer set search_path = public, private, pg_temp as $$
  select private.admin_user_growth();
$$;

-- 3) Admin course names: admin_course_catalog() compared a uuid column with text and always failed (HTTP 400).
--    It also now includes the built-in course catalogue, so the member-activation dashboard shows real course names.
create or replace function public.admin_course_catalog()
returns jsonb language plpgsql security definer set search_path = public as $$
declare result jsonb;
begin
  if coalesce(get_my_role(), '') <> 'admin' then raise exception 'not_authorized'; end if;
  with cat as (
    select c.id::text as id, c.slug, c.title from public.courses c where coalesce(c.title, '') <> ''
    union
    select distinct cert.course_id::text as id, null::text as slug, cert.course_name as title
      from public.certificates cert
     where cert.course_id is not null and coalesce(cert.course_name, '') <> ''
    union
    select cc.course_key as id, cc.course_key as slug, cc.title from public.course_catalog cc
     where coalesce(cc.course_key, '') <> '' and coalesce(cc.title, '') <> ''
  )
  select coalesce(jsonb_agg(jsonb_build_object('id', id, 'slug', slug, 'title', title)), '[]'::jsonb) into result from cat;
  return coalesce(result, '[]'::jsonb);
end $$;
